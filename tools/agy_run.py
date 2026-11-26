"""Runs one Antigravity CLI (agy) task with a permission whitelist.

Why not ``agy -p``: checked on 2026-11-26, print mode lets agy write files
anywhere on disk with no prompt (``--sandbox`` and the deny rules tried did
not stop it), and it runs a shell command only when an allow rule matches the
whole command line. So this script starts ``agy acp`` (Agent Client Protocol
over stdio), sends one prompt, and answers every permission request itself:

- edit: every path must lie in a ``--write`` folder. No ``--write`` means
  the task is read-only.
- execute: the command must start with an ``--allow-cmd`` prefix, run in the
  project root, use only letters, digits, CJK characters, spaces and
  ``_ - . / : = ,`` (no quotes, pipes, redirects or ``..``), and every
  path-like argument must lie in the project. No ``--allow-cmd`` means no
  shell. A prefix is trusted: give only commands that cannot write outside
  the write folders.
- read / search, if agy asks: every path must lie in the project root and
  must not be a secrets file or ``.git``. A search with no path is denied.
- anything else (fetch, delete, unknown kinds): denied.

Limits seen with agy 1.5.18 on 2026-11-26:
- agy reads files without asking, so reads are not limited: it read a
  ``.env`` in the project. Do not run it where it must not see a file.
- agy approves writes inside the system temp folder by itself, without
  asking. So the project root must not be in the temp folder, and writes
  that agy makes into the temp folder are not checked.
- The change check covers the project root only (not ``.git`` or caches).

agy ends its turn after a denial, so the script resumes it with the reason,
up to 5 times.

Usage (run from the project root):
  uv run --no-project python -I agy_run.py --prompt-file P --dir D
      [--write DIR ...] [--allow-cmd PREFIX ...]
      [--task read|rewrite|simple] [--exhausted argon,neon,claude]
      [--model ID] [--timeout SEC]

It writes into D: ``agy-out.md`` (agy's messages), ``agy-log.txt`` (every
permission decision) and ``agy-summary.txt`` (model, exit code, counts,
changed files, a quota hint), and prints the summary. Exit 0 when the turn
ended normally with no denial left; 1 otherwise; 2 for bad arguments.
"""

from __future__ import annotations

import argparse
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import TextIO

# Model candidates per task type, tried left to right, skipping quota groups
# that the caller says are used up. Checked with `agy models` on 2026-11-26.
MODELS = {
    "read": ("gemini-4-neon-high", "gemini-4-argon-high",
             "claude-sonnet-5-5-high"),
    "rewrite": ("gemini-4-argon-medium", "gemini-4-neon-medium",
                "claude-sonnet-5-5-medium"),
    "simple": ("gemini-4-hydrogen-low", "gemini-4-argon-low",
               "claude-sonnet-5-5-low"),
}
GROUPS = {
    "argon": ("gemini-4-argon-",),
    "neon": ("gemini-4-neon-", "gemini-4-hydrogen-"),
    "claude": ("claude-",),
}
QUOTA = re.compile(r"quota|rate.?limit|exhaust|\b429\b|resource_exhausted",
                   re.I)
MAX_RESUMES = 5
MAX_TIMEOUT = 6600  # a background Bash command lives at most 2 hours; leave room for startup (up to 360 s) and snapshots
RESUME_PROMPT = (
    "These actions were denied by the permission policy:\n{denied}\n"
    "Do not try them again. Use what is allowed instead: read files in the "
    "project, write files only in the allowed folders, and run only the "
    "allowed commands (letters, digits, spaces and _ - . / : = , only; no "
    "quotes, pipes or '..'; give a concrete path). Then finish the original "
    "task, and say at the end what you could not do.")
SAFE_COMMAND = re.compile(
    r"[A-Za-z0-9_ \-./:=,\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]+")
READ_KINDS = {"read", "search"}
PATH_KEY = re.compile(r"path|file|dir|target|dest|uri|location|folder|out",
                      re.I)
# Exact key names (lower case) whose values are text, not paths.
CONTENT_KEYS = {
    "content", "codecontent", "target", "replacement", "targetcontent",
    "replacementcontent", "toolsummary", "description", "instruction",
    "codemarkdownlanguage", "query", "explanation", "title", "toolaction",
    "targetlinterrorids", "complexity"}
# Never read, never scanned, and left out of the change check.
OPAQUE_DIRS = {".git", ".venv", "node_modules"}
SKIP_IN_SNAPSHOT = OPAQUE_DIRS | {"__pycache__", ".pytest_cache",
                                  ".mypy_cache", ".ruff_cache"}
SECRET_NAMES = {".env", ".mcp.json", "settings.local.json", "credentials.json",
                ".npmrc", ".netrc", "id_rsa", "id_ed25519"}


def pick_model(task: str, exhausted: set[str]) -> str | None:
    """Returns the first candidate whose quota group is not used up."""
    for model in MODELS[task]:
        group = next((g for g, pre in GROUPS.items()
                      if model.startswith(pre)), None)
        if group not in exhausted:
            return model
    return None


def group_of(model: str) -> str:
    return next((g for g, pre in GROUPS.items() if model.startswith(pre)),
                "other")


def _bad_path_text(text: str) -> bool:
    """Path spellings the policy refuses outright (expansion, odd URIs)."""
    return (text.startswith("~") or "%" in text or "$" in text
            or re.match(r"^[A-Za-z]:(?![/\\])", text) is not None
            or (text.startswith("file:") and not text.startswith("file:///")))


def _to_path(text: str, cwd: Path) -> Path:
    """Turns an agy path (/D:/x, a Windows path, relative) into a Path."""
    if text.startswith("file:///"):
        text = text[len("file:///"):]
    if re.match(r"^/[A-Za-z]:[/\\]", text):
        text = text[1:]
    path = Path(text)
    if not path.is_absolute():
        path = cwd / path
    return path.resolve()


def _inside(path: Path, dirs: list[Path]) -> bool:
    return any(path == d or path.is_relative_to(d) for d in dirs)


def _secret_spots(cwd: Path) -> tuple[Path, ...]:
    """Secrets files under the project (fixed names plus a fresh scan)."""
    spots = {cwd / ".git", cwd / ".claude" / "settings.local.json"}
    for top, dirs, files in os.walk(cwd):
        spots.update(Path(top) / d for d in dirs if d.lower() in OPAQUE_DIRS)
        dirs[:] = [d for d in dirs if d.lower() not in OPAQUE_DIRS]
        spots.update(Path(top) / f for f in files
                     if f.lower() in SECRET_NAMES
                     or f.lower().startswith(".env."))
    return tuple(spots)


def _protected(path: Path, cwd: Path) -> bool:
    """True for secrets, git internals, and folders that contain either.

    A folder counts because agy's search recurses into it.
    """
    name = path.name.lower()
    if name in SECRET_NAMES or name.startswith(".env.") or OPAQUE_DIRS & {
            part.lower() for part in path.parts}:
        return True
    return any(spot == path or spot.is_relative_to(path)
               for spot in _secret_spots(cwd))


def _looks_like_path(text: str) -> bool:
    return bool(re.search(r"[/\\:]", text) or text.startswith((".", "~")))


def _strings(value: object, key: str = "") -> Iterator[tuple[str, str]]:
    """Yields (key, string) for nested strings, skipping text-valued keys."""
    if isinstance(value, str):
        yield key, value
    elif isinstance(value, dict):
        for k, item in value.items():
            if str(k).lower() not in CONTENT_KEYS:
                yield from _strings(item, str(k))
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item, key)


def _request_paths(tool_call: dict, *, every_string: bool) -> list[str]:
    """Collects the path strings a request names.

    With ``every_string`` (edits) every non-text string counts, so an
    unknown field fails closed. Otherwise a string counts when its key names
    a path or the string looks like one.
    """
    texts = [v for _, v in _strings(tool_call.get("locations"))]
    for key, value in _strings(tool_call.get("rawInput")):
        if not value.strip():
            continue
        if every_string or PATH_KEY.search(key) or _looks_like_path(value):
            texts.append(value)
    return texts


def _check_read(texts: list[str], cwd: Path) -> tuple[bool, str]:
    for text in texts:
        if _bad_path_text(text):
            return False, f"path form not allowed: {text}"
        path = _to_path(text, cwd)
        if not _inside(path, [cwd]):
            return False, f"read outside project: {path}"
        if _protected(path, cwd):
            return False, f"protected path (secrets or .git inside): {path}"
    return True, "read inside project"


def _check_command(line: str, cwd: Path,
                   commands: tuple[str, ...]) -> tuple[bool, str]:
    """Checks one command line against the whitelist."""
    if not commands:
        return False, "no shell commands allowed for this task"
    if not SAFE_COMMAND.fullmatch(line):
        return False, "command has characters outside the safe set"
    if ".." in line:
        return False, "command contains '..'"
    if not any(line == p.rstrip() or line.startswith(p) for p in commands):
        return False, "command not in whitelist"
    reads = []
    for arg in line.split()[1:]:
        if "=" in arg and arg.startswith("-"):
            arg = arg.split("=", 1)[1]
        if arg and not arg.startswith("-") and _looks_like_path(arg):
            reads.append(arg)
    ok, reason = _check_read(reads, cwd)
    if not ok:
        return False, f"command {reason}"
    return True, "whitelisted command"


def decide(tool_call: dict, *, cwd: Path, write_dirs: list[Path],
           commands: tuple[str, ...]) -> tuple[bool, str]:
    """Returns (allowed, reason) for one permission request."""
    if not isinstance(tool_call, dict):
        return False, "malformed request"
    kind = tool_call.get("kind", "")
    raw = tool_call.get("rawInput")
    if not isinstance(raw, dict):
        raw = {}
    if kind == "execute":
        cwd_arg = raw.get("Cwd") or raw.get("cwd")
        if cwd_arg and _to_path(str(cwd_arg), cwd) != cwd:
            return False, "command must run in the project root"
        line = raw.get("CommandLine") or raw.get("command")
        if not isinstance(line, str):
            return False, "command line missing"
        return _check_command(line.strip(), cwd, commands)
    if kind == "edit":
        if not write_dirs:
            return False, "read-only task: no write folders"
        if not isinstance(tool_call.get("rawInput"), dict):
            return False, "edit without raw input"
        texts = _request_paths(tool_call, every_string=True)
        if not texts:
            return False, "edit without a path"
        for text in texts:
            if _bad_path_text(text):
                return False, f"path form not allowed: {text}"
            path = _to_path(text, cwd)
            if not _inside(path, write_dirs):
                return False, f"write outside write folders: {path}"
            if _protected(path, cwd):
                return False, f"protected path: {path}"
        return True, "write inside write folders"
    if kind in READ_KINDS:
        texts = _request_paths(tool_call, every_string=False)
        if not texts:
            return False, f"{kind} needs an explicit path"
        return _check_read(texts, cwd)
    return False, f"kind {kind or '?'} not allowed"


def snapshot(root: Path) -> dict[str, tuple[int, int]]:
    """Maps each file under root to (size, mtime_ns), skipping caches."""
    files: dict[str, tuple[int, int]] = {}
    for top, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if d.lower() not in SKIP_IN_SNAPSHOT]
        for name in names:
            path = Path(top) / name
            try:
                st = path.stat()
            except OSError:
                continue
            files[str(path.relative_to(root))] = (st.st_size, st.st_mtime_ns)
    return files


def changed_files(before: dict, after: dict) -> list[str]:
    return sorted(k for k in before.keys() | after.keys()
                  if before.get(k) != after.get(k))


def _kill_tree(proc: subprocess.Popen) -> None:
    """Stops agy and every process it started."""
    if proc.poll() is not None:
        return
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)],
                       capture_output=True, check=False)
    else:
        proc.kill()


class Client:
    """Minimal JSON-RPC client for ``agy acp`` over stdio."""

    def __init__(self, argv: list[str], cwd: Path, log: TextIO,
                 policy: Callable[[dict], tuple[bool, str]]) -> None:
        self.stderr: list[str] = []
        self.proc = subprocess.Popen(
            argv, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        self.log, self.policy = log, policy
        self.next_id, self.replies = 0, {}
        self.lock = threading.Lock()
        self.closed = False
        self.text: list[str] = []
        self.denied: list[str] = []
        self.allows = self.denies = 0
        threading.Thread(target=self._read, daemon=True).start()
        threading.Thread(target=self._read_err, daemon=True).start()

    def _send(self, obj: dict) -> None:
        data = (json.dumps(obj, ensure_ascii=False) + "\n").encode("utf-8")
        with self.lock:
            try:
                self.proc.stdin.write(data)
                self.proc.stdin.flush()
            except OSError:
                self.closed = True

    def call(self, method: str, params: dict, timeout: float) -> dict:
        """Sends a request and waits for its reply."""
        self.next_id += 1
        box: queue.Queue = queue.Queue()
        self.replies[self.next_id] = box
        if self.closed:
            return {"error": {"message": "agy exited"}}
        self._send({"jsonrpc": "2.0", "id": self.next_id, "method": method,
                    "params": params})
        try:
            return box.get(timeout=timeout)
        except queue.Empty as exc:
            raise TimeoutError(f"{method} timed out after {timeout:.0f}s") \
                from exc

    def note(self, line: str) -> None:
        self.log.write(time.strftime("%H:%M:%S ") + line + "\n")
        self.log.flush()

    def _read_err(self) -> None:
        for raw in self.proc.stderr:
            self.stderr.append(raw.decode("utf-8", "replace").rstrip())
            del self.stderr[:-200]

    def _read(self) -> None:
        try:
            for raw in self.proc.stdout:
                try:
                    msg = json.loads(raw.decode("utf-8", "replace"))
                except json.JSONDecodeError:
                    continue
                if not isinstance(msg, dict):
                    continue
                if "method" in msg:
                    try:
                        self._handle(msg)
                    except Exception as exc:  # noqa: BLE001
                        self.note(f"handler error: {exc!r}")
                        if "id" in msg:
                            self._answer(msg, False)
                elif msg.get("id") in self.replies:
                    self.replies[msg["id"]].put(msg)
        finally:
            self.closed = True
            for box in list(self.replies.values()):
                box.put({"error": {"message": "agy exited"}})

    def _answer(self, msg: dict, ok: bool) -> None:
        params = msg.get("params") if isinstance(msg.get("params"), dict) \
            else {}
        options = params.get("options") or []
        want = "allow_once" if ok else "reject_once"
        option = next((o for o in options if isinstance(o, dict)
                       and o.get("kind") == want), None)
        if option is None:
            result = {"outcome": {"outcome": "cancelled"}}
        else:
            result = {"outcome": {"outcome": "selected",
                                  "optionId": option.get("optionId")}}
        self._send({"jsonrpc": "2.0", "id": msg["id"], "result": result})

    def _handle(self, msg: dict) -> None:
        method, params = msg["method"], msg.get("params") or {}
        if method == "session/update":
            update = params.get("update") or {}
            if update.get("sessionUpdate") == "agent_message_chunk":
                self.text.append((update.get("content") or {}).get("text", ""))
            return
        if "id" not in msg:
            return
        if method == "session/request_permission":
            tool_call = params.get("toolCall") or {}
            ok, reason = self.policy(tool_call)
            title = tool_call.get("title") if isinstance(tool_call, dict) \
                else "?"
            kind = tool_call.get("kind") if isinstance(tool_call, dict) \
                else "?"
            if ok:
                self.allows += 1
            else:
                self.denies += 1
                self.denied.append(f"{title} ({reason})")
            self.note(f"{'ALLOW' if ok else 'DENY '} [{kind}] {title} - "
                      f"{reason}")
            if isinstance(tool_call, dict):
                raw = json.dumps(tool_call.get("rawInput"), ensure_ascii=False)
                self.note(f"  rawInput {raw[:300]}")
            self._answer(msg, ok)
            return
        self._send({"jsonrpc": "2.0", "id": msg["id"],
                    "error": {"code": -32601, "message": "not supported"}})

    def close(self) -> None:
        _kill_tree(self.proc)


def run(args: argparse.Namespace, cwd: Path, model: str, write_dirs:
        list[Path], commands: tuple[str, ...], log: TextIO,
        prompt: str) -> tuple[int, list[str], Client | None, str]:
    """Runs the prompt. Returns (code, turn texts, client, error text)."""
    exe = shutil.which("agy")
    if not exe:
        return 1, [], None, "agy not found on PATH"

    def policy(tool_call: dict) -> tuple[bool, str]:
        return decide(tool_call, cwd=cwd, write_dirs=write_dirs,
                      commands=commands)

    client = Client([exe, "acp"], cwd, log, policy)
    turns: list[str] = []
    code, error = 1, ""
    try:
        init = client.call("initialize", {
            "protocolVersion": 1,
            "clientCapabilities": {"fs": {"readTextFile": False,
                                          "writeTextFile": False},
                                   "terminal": False}}, 120)
        if "error" in init:
            return 1, turns, client, f"initialize failed: {init['error']}"
        new = client.call("session/new", {"cwd": str(cwd), "mcpServers": []},
                          120)
        if "error" in new:
            return 1, turns, client, f"session/new failed: {new['error']}"
        sid = new["result"]["sessionId"]
        chosen = client.call("session/set_model",
                             {"sessionId": sid, "modelId": model}, 60)
        if "error" in chosen:
            return 1, turns, client, f"set_model failed: {chosen['error']}"
        client.note(f"model {model}: ok")
        # The user's agy settings may say accept-edits, which approves edits
        # without asking. Force the mode that sends every edit to the policy.
        mode = client.call("session/set_mode",
                           {"sessionId": sid, "modeId": "default"}, 60)
        if "error" in mode:
            return 1, turns, client, f"set_mode failed: {mode['error']}"
        client.note("mode default: ok")
        deadline = time.monotonic() + args.timeout
        for attempt in range(MAX_RESUMES + 1):
            client.denied.clear()
            client.text.clear()
            reply = client.call("session/prompt", {
                "sessionId": sid, "prompt": [{"type": "text", "text": prompt}]},
                max(deadline - time.monotonic(), 1))
            turns.append("".join(client.text))
            if "error" in reply:
                error = f"session/prompt failed: {reply['error']}"
                break
            stop = reply["result"].get("stopReason")
            client.note(f"stop {stop}; usage {reply['result'].get('usage')}")
            if not client.denied:
                code = 0 if stop == "end_turn" else 1
                if code:
                    error = f"turn ended with stopReason {stop}"
                break
            if attempt == MAX_RESUMES:
                error = "denials still pending after the last resume"
                client.note(error)
                break
            client.note(f"resume {attempt + 1}/{MAX_RESUMES}")
            prompt = RESUME_PROMPT.format(denied="\n".join(
                f"- {d}" for d in client.denied))
    except TimeoutError as exc:
        turns.append("".join(client.text))
        error = str(exc)
    finally:
        client.close()
    return code, turns, client, error


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--prompt-file", required=True, type=Path)
    parser.add_argument("--dir", required=True, type=Path,
                        help="folder for agy-out.md, agy-log.txt, "
                             "agy-summary.txt")
    parser.add_argument("--write", action="append", default=[],
                        help="folder agy may write to (repeatable)")
    parser.add_argument("--allow-cmd", action="append", default=[],
                        help="allowed command prefix (repeatable)")
    parser.add_argument("--task", choices=sorted(MODELS), default="read")
    parser.add_argument("--exhausted", default="",
                        help="used-up quota groups: argon, neon, claude")
    parser.add_argument("--model", help="model ID; overrides --task")
    parser.add_argument("--root", type=Path, default=Path.cwd(),
                        help="project root (default: current folder)")
    parser.add_argument("--timeout", type=float, default=MAX_TIMEOUT)
    args = parser.parse_args(argv)

    def fail(msg: str) -> int:
        print(f"error: {msg}", file=sys.stderr)
        return 2

    cwd = args.root.resolve()
    if not cwd.is_dir():
        return fail(f"project root not found: {cwd}")
    temp = Path(tempfile.gettempdir()).resolve()
    if _inside(cwd, [temp]):
        return fail(f"project root is in the temp folder {temp}; agy approves "
                    "writes there by itself, so the write limits would not "
                    "hold")
    try:
        prompt = args.prompt_file.read_text(encoding="utf-8")
    except OSError as exc:
        return fail(f"cannot read the prompt file: {exc}")
    if not prompt.strip():
        return fail("the prompt file is empty")
    exhausted = {g.strip().lower() for g in args.exhausted.split(",")
                 if g.strip()}
    if exhausted - GROUPS.keys():
        return fail(f"unknown quota group: {', '.join(exhausted - GROUPS.keys())}")
    model = args.model or pick_model(args.task, exhausted)
    if not model:
        return fail("every candidate model is in a used-up quota group")
    args.timeout = min(max(args.timeout, 60), MAX_TIMEOUT)

    out_dir = args.dir if args.dir.is_absolute() else cwd / args.dir
    out_dir = out_dir.resolve()
    write_dirs = []
    for d in args.write:
        if _bad_path_text(d):
            return fail(f"write folder form not allowed: {d}")
        path = _to_path(d, cwd)
        if path == cwd or not _inside(path, [cwd]):
            return fail(f"write folder must be a subfolder of {cwd}: {path}")
        if _protected(path, cwd):
            return fail(f"write folder holds secrets or .git: {path}")
        write_dirs.append(path)
    commands = tuple(p.strip() + " " for p in args.allow_cmd if p.strip())
    for p in commands:
        if not SAFE_COMMAND.fullmatch(p.strip()) or ".." in p:
            return fail(f"command prefix has unsafe characters: {p.strip()}")

    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "agy-out.md"
    log_path = out_dir / "agy-log.txt"
    summary_path = out_dir / "agy-summary.txt"
    before = snapshot(cwd)
    started = time.monotonic()
    with log_path.open("a", encoding="utf-8") as log:
        log.write(f"\n== {time.strftime('%Y-%m-%d %H:%M:%S')} root {cwd}\n")
        code, turns, client, error = run(
            args, cwd, model, write_dirs, commands, log, prompt)
    text = "\n\n---\n\n".join(t for t in turns if t.strip())
    out_file.write_text(text, encoding="utf-8")
    after = snapshot(cwd)

    own = {out_file, log_path, summary_path}
    inside, outside = [], []
    for rel in changed_files(before, after):
        path = cwd / rel
        if path in own:
            continue
        (inside if _inside(path, write_dirs) else outside).append(rel)
    lines = [
        f"exit: {code}",
        f"model: {model} (quota group {group_of(model)})",
        f"minutes: {(time.monotonic() - started) / 60:.1f}",
        f"write folders: {', '.join(str(d) for d in write_dirs) or 'none (read-only)'}",
        f"allowed commands: {', '.join(c.strip() for c in commands) or 'none'}",
    ]
    if client:
        lines.append(f"permission requests: {client.allows} allowed, "
                     f"{client.denies} denied")
    if error:
        lines.append(f"error: {error}")
    hay = "\n".join([error, text[-4000:]] + (client.stderr if client else []))
    hits = [ln.strip()[:200] for ln in hay.splitlines() if QUOTA.search(ln)]
    if code and hits:
        lines.append(f"quota suspected: group {group_of(model)} ({model})")
        lines += [f"  {h}" for h in hits[:5]]
    if code and client and client.stderr:
        lines.append("agy stderr (last lines):")
        lines += [f"  {s}" for s in client.stderr[-10:]]
    lines.append(f"changed inside the write folders ({len(inside)}):")
    lines += [f"  {r}" for r in inside]
    lines.append(f"changed OUTSIDE the write folders ({len(outside)}):")
    lines += [f"  {r}" for r in outside]
    lines += [f"agy output: {out_file}", f"permission log: {log_path}"]
    summary = "\n".join(lines) + "\n"
    summary_path.write_text(summary, encoding="utf-8")
    print(summary, end="")
    return code


if __name__ == "__main__":
    sys.exit(main())
