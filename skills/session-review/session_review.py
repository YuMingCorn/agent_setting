"""Extract what the user typed in recent Claude Code sessions, and measure how often
the user just accepted the recommended option of a multiple-choice question.

Reads the session transcripts in ~/.claude/projects/*/*.jsonl and writes these
UTF-8 files to the output folder:
  messages.txt  the user's own messages, the questions asked (AskUserQuestion)
                and the user's answers, grouped by session in time order.
  stats.md      counts per project, the recommended-option rate, the most
                repeated short replies, and the answers that did not take the
                recommended option.
  part0.txt ... messages.txt split at session borders into parts of about
                150,000 characters, for reading in parallel.

The output holds private conversation text. Keep it outside any git repo.

Usage:
  uv run --no-project python -I session_review.py --out <folder> [--days 30]
      [--project <substring>]
"""

import argparse
import collections
import datetime
import glob
import json
import os
import re
import sys

NOISE_PREFIXES = (
    "/clear", "/compact", "/model", "/mcp", "/ide", "/plugin", "/reload-plugins",
    "/exit", "/resume", "/config", "/status", "/cost", "/context", "/login",
    "This session is being continued from a previous conversation",
    "<bash-stdout>", "<bash-input>", "<local-command", "Caveat:",
)
REC_MARK = re.compile(r"\(Recommended\)|（建議）|（推薦）|\(推薦\)|\(建議\)|\(recommended\)")
CHUNK_CHARS = 150_000


def parse_args():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--out", required=True, help="output folder, outside any git repo")
    p.add_argument("--days", type=int, default=30, help="look back this many days (default 30)")
    p.add_argument("--project", default="", help="only transcript folders whose name contains this text")
    return p.parse_args()


def block_text(content):
    """Join the text of a tool_result content field."""
    if isinstance(content, list):
        return " ".join(x.get("text", "") for x in content if isinstance(x, dict))
    return str(content or "")


def clean_user_text(content):
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        text = "".join(b.get("text", "") for b in content if b.get("type") == "text")
    else:
        return ""
    text = re.sub(r"<system-reminder>.*?</system-reminder>", "", text, flags=re.S).strip()
    m = re.search(r"<command-name>(.*?)</command-name>.*?<command-args>(.*?)</command-args>", text, re.S)
    if m:
        text = "/" + m.group(1).strip().lstrip("/") + " " + m.group(2).strip()
    text = text.strip()
    if not text or text.startswith(NOISE_PREFIXES) or "<task-notification>" in text[:200]:
        return ""
    return text


def parse_answers(result_text, questions):
    """Map each question to the user's answer in an AskUserQuestion result."""
    answers = {}
    for q in questions:
        qq = q.get("question", "")
        # Answers look like "question"="answer", joined by ", " and ended by ". ".
        end = r'"(?=\s*,\s*"|\.\s|\.?\s*$|\s+selected preview|\s+user notes)'
        m = re.search(re.escape(qq) + r'"\s*=\s*"(.*?)' + end, result_text, re.S)
        if not m:
            m = re.search(re.escape(qq[:40]) + r'[^"]*"\s*=\s*"(.*?)' + end, result_text, re.S)
        answers[qq] = m.group(1).strip() if m else ""
    return answers


def main():
    args = parse_args()
    root = os.path.join(os.path.expanduser("~"), ".claude", "projects")
    cutoff = datetime.datetime.now().timestamp() - args.days * 86400
    files = [
        f for f in glob.glob(os.path.join(root, "*", "*.jsonl"))
        if os.path.getmtime(f) >= cutoff
        and args.project.lower() in os.path.basename(os.path.dirname(f)).lower()
        # Sessions started inside temporary folders are test runs, not real work.
        and "-temp" not in os.path.basename(os.path.dirname(f)).lower()
    ]
    files.sort(key=os.path.getmtime)

    out_lines = []
    seen_asks = set()          # tool_use ids; resumed sessions copy earlier history
    seen_msgs = set()          # (uuid) of user messages, for the same reason
    per_project = collections.Counter()
    short_replies = collections.Counter()
    q_total = q_with_rec = q_took_rec = q_blank = 0
    not_rec = []
    n_msgs = 0

    for path in files:
        project = os.path.basename(os.path.dirname(path))
        asks = {}
        lines = []
        with open(path, encoding="utf-8", errors="ignore") as fh:
            for raw in fh:
                try:
                    d = json.loads(raw)
                except ValueError:
                    continue
                if d.get("isSidechain") or d.get("isMeta"):
                    continue
                content = (d.get("message") or {}).get("content")
                ts = (d.get("timestamp") or "")[:16]
                if d.get("type") == "user":
                    if isinstance(content, list):
                        for b in content:
                            if b.get("type") == "tool_result" and b.get("tool_use_id") in asks:
                                qs = asks.pop(b["tool_use_id"])
                                answers = parse_answers(block_text(b.get("content")), qs)
                                for q in qs:
                                    ans = answers.get(q.get("question", ""), "")
                                    lines.append(f"  [ANSWER] {ans[:400]}")
                                    q_total += 1
                                    recs = [REC_MARK.sub("", o.get("label", "")).strip()
                                            for o in q.get("options", []) if REC_MARK.search(o.get("label", ""))]
                                    if not ans:
                                        q_blank += 1
                                        continue
                                    if not recs:
                                        continue
                                    q_with_rec += 1
                                    picked = [REC_MARK.sub("", a).strip() for a in ans.split(", ")]
                                    if any(r in picked for r in recs):
                                        q_took_rec += 1
                                    else:
                                        not_rec.append((project, q.get("question", "")[:160], recs[0][:60], ans[:200]))
                    uid = d.get("uuid")
                    text = clean_user_text(content)
                    if not text or (uid and uid in seen_msgs):
                        continue
                    if uid:
                        seen_msgs.add(uid)
                    n_msgs += 1
                    per_project[project] += 1
                    if len(text) <= 12:
                        short_replies[text] += 1
                    lines.append(f"[{ts}] USER: {text[:1200]}")
                elif d.get("type") == "assistant" and isinstance(content, list):
                    for b in content:
                        if b.get("type") == "tool_use" and b.get("name") == "AskUserQuestion":
                            if b["id"] in seen_asks:
                                continue
                            seen_asks.add(b["id"])
                            qs = (b.get("input") or {}).get("questions", [])
                            asks[b["id"]] = qs
                            for q in qs:
                                opts = " | ".join(o.get("label", "") for o in q.get("options", []))
                                lines.append(f"  [ASK] {q.get('question', '')[:300]} :: {opts[:300]}")
        if any("USER:" in ln for ln in lines):
            out_lines.append(f"\n===== {project} / {os.path.basename(path)[:8]} =====")
            out_lines.extend(lines)

    os.makedirs(args.out, exist_ok=True)
    text = "\n".join(out_lines)
    with open(os.path.join(args.out, "messages.txt"), "w", encoding="utf-8") as fh:
        fh.write(text)

    # Split into parts of about CHUNK_CHARS at session boundaries, for parallel reading.
    parts, cur, size = [], [], 0
    for ln in out_lines:
        if ln.startswith("\n=====") and size > CHUNK_CHARS:
            parts.append(cur)
            cur, size = [], 0
        cur.append(ln)
        size += len(ln)
    if cur:
        parts.append(cur)
    for i, part in enumerate(parts):
        with open(os.path.join(args.out, f"part{i}.txt"), "w", encoding="utf-8") as fh:
            fh.write("\n".join(part))

    rate = f"{100 * q_took_rec / q_with_rec:.0f}%" if q_with_rec else "n/a"
    st = [
        f"# Session review, last {args.days} days",
        "",
        f"- Sessions with user messages: {sum(1 for ln in out_lines if ln.startswith(chr(10) + '====='))}",
        f"- User messages (noise removed): {n_msgs}",
        f"- Questions asked: {q_total} (no answer parsed: {q_blank})",
        f"- Questions with a recommended option: {q_with_rec}; the user took it: {q_took_rec} ({rate})",
        f"- Parts written for reading: {len(parts)}",
        "",
        "## User messages per project",
        "",
    ]
    st += [f"- {p}: {n}" for p, n in per_project.most_common()]
    st += ["", "## Most repeated short replies", ""]
    st += [f"- {r!r}: {n}" for r, n in short_replies.most_common(25)]
    st += ["", "## Answers that did not take the recommended option", ""]
    st += [f"- [{p}] {q} || recommended: {r} || answer: {a}" for p, q, r, a in not_rec]
    with open(os.path.join(args.out, "stats.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(st) + "\n")

    # ASCII-only console output: the Windows console may not be UTF-8.
    print(f"sessions={len(files)} messages={n_msgs} questions={q_total} "
          f"with_rec={q_with_rec} took_rec={q_took_rec} ({rate}) parts={len(parts)}")
    print(f"wrote {os.path.abspath(args.out)}")


if __name__ == "__main__":
    sys.exit(main())
