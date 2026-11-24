**English** | [繁體中文](README.zh-TW.md)

# Agent settings for Claude Code, Codex and Gemini CLI

My custom subagents and skills. They were written for Claude Code, and the repo also ships generated versions for OpenAI Codex and Google Gemini CLI, so anyone can install them in the tool they use.

## Contents

| Path | What it holds |
|---|---|
| `agents/` | 6 custom subagents in Claude Code format. **Source of truth.** |
| `skills/brain/` | `/brain` skill. Claude Code only. |
| `skills/todo-review/` | `/todo-review` skill and its SessionStart hook script `todo-reminder.ps1`. **Source of truth.** |
| `skills/wrap-up/` | `/wrap-up` skill. **Source of truth.** |
| `skills/session-review/` | `/session-review` skill and its script `session_review.py`. Claude Code only. |
| `portable/skills/` | `todo-review` and `wrap-up` in the open [Agent Skills](https://agentskills.io/specification) format (only `name` and `description` in the frontmatter). Generated. |
| `portable/codex/agents/` | The 6 agents as Codex TOML files. Generated. |
| `portable/gemini/agents/` | The 6 agents as Gemini CLI Markdown files. Generated. |
| `build.ps1` | Generates `portable/` from `agents/` and `skills/`. |
| `deploy.ps1` | Copies the files into your home folder. |
| `backup.ps1` | Copies direct edits in `~/.claude` back into the repo. |

Never edit files under `portable/` by hand. Edit `agents/` or `skills/` and run `build.ps1`.

## Install

Pick the folders for your tool and copy them. You do not need to run any script.

| Tool | Copy | To |
|---|---|---|
| Claude Code | `agents/*` | `~/.claude/agents/` |
| Claude Code | `skills/*` | `~/.claude/skills/` |
| Codex | `portable/skills/*` | `~/.agents/skills/` |
| Codex | `portable/codex/agents/*` | `~/.codex/agents/` |
| Gemini CLI | `portable/skills/*` | `~/.agents/skills/` (or `~/.gemini/skills/`) |
| Gemini CLI | `portable/gemini/agents/*` | `~/.gemini/agents/` |

macOS or Linux, for example for Codex:

```sh
git clone https://github.com/YuMingCorn/agent_setting.git
cd agent_setting
mkdir -p ~/.agents/skills ~/.codex/agents
cp -R portable/skills/* ~/.agents/skills/
cp portable/codex/agents/* ~/.codex/agents/
```

Windows, all tools at once:

```powershell
git clone https://github.com/YuMingCorn/agent_setting.git
cd agent_setting
powershell -ExecutionPolicy Bypass -File .\deploy.ps1 -All
```

Restart the tool after you install.

## Agents

Each agent is a subagent that the main agent starts for one task. The idea is to match the model to the job: a small model for cheap mechanical work, a mid-size model for search and checks that need judgment, and the strongest model for building.

| Agent | Claude model | Tools | Use it for |
|---|---|---|---|
| `Explore` | Haiku | Read, Grep, Glob, WebFetch, WebSearch | Read-only search with a known keyword or target: find files, grep code, look up docs. Returns a short answer with `path:line` locations. |
| `sonnet-search` | Sonnet | Read, Grep, Glob, WebFetch, WebSearch | Read-only search that needs judgment: trace how code or rules connect across files, or find something without a known keyword. Separates what it saw from what it inferred. |
| `haiku-audit` | Haiku | Read, Grep, Glob | Check many files against a short, explicit checklist (frontmatter fields, naming rules, forbidden patterns). Reports each violation and changes nothing. |
| `haiku-worker` | Haiku | All | Repetitive work across many items whose results are easy to check: renaming, extracting fields, tagging, short summaries. Not for code. |
| `opus-builder` | Opus | All | Build from a clear brief after the plan is decided. Writes and changes code and files, and reports what it changed file by file. |
| `sonnet-checker` | Sonnet | Read, Grep, Glob, Bash (no Write or Edit) | Check finished work against its brief before it is called done. Runs tests, reads the diff, tries edge cases, and ends with `PASS` or `FAIL`. |

How the generated versions differ:

- **Model**: the Codex and Gemini files set no model, so each agent uses the main session's model. To pick one, add `model = "..."` (Codex) or `model: ...` (Gemini).
- **Tools on Gemini CLI**: the tool list is translated, for example `Read` to `read_file` and `Grep` to `grep_search`. Agents with no tool list get all tools.
- **Tools on Codex**: a Codex agent file cannot limit tools. Codex subagents use the parent's sandbox and approvals, so the read-only agents stay read-only only because their instructions say so.

## Skills

### `/todo-review` (Claude Code, Codex, Gemini CLI)

Each project has its own to-do list of open decisions in `~/.agents/todo/`, one file per project (for example `D--Projects-example.md`). The `project:` line at the top of the file is the project root: the top folder of the git repo, or the working folder when it is not in a git repo. The lists are outside every project folder, so they never go into git. All tools share the same lists. The skill reads only the current project's list and never mentions other projects. Each item has a status: `open`, `decided`, `done` or `dropped`.

| Command | What it does |
|---|---|
| `/todo-review` | Asks you about each `open` item for the current project, a few at a time. Items with options show a choice; items without options ask you to type what to do. Writes each answer back to the list, then does the work you just decided. |
| `/todo-review add <description>` | Adds a new item for the current project. |
| `/todo-review list` | Lists the `open` and `decided` items for the current project, and changes nothing. |

In Codex, call the skill with `$todo-review`. In Gemini CLI, ask for it in plain words, for example "review my to-dos". The skill asks its questions in your language. It uses `AskUserQuestion` in Claude Code and `ask_user` in Gemini CLI, and asks in plain text where no question tool exists.

Older versions kept every project in one file, `~/.agents/todo.md`. If that file still exists, the skill moves the current project's items into the new list. It never deletes the old file itself.

**Optional session-start reminder.** `todo-reminder.ps1` counts the `open` items in the current project's list when a session starts. If there are any, the agent runs the review in its first reply. All three tools read the same hook output (`systemMessage` and `hookSpecificOutput.additionalContext`). The script needs Windows PowerShell 5.1 or PowerShell 7 (`pwsh`). Add it to the tool's hook settings and change the path to where you installed the skill:

- Claude Code, in `~/.claude/settings.json`:
  ```json
  "hooks": {
    "SessionStart": [
      { "hooks": [ {
        "type": "command",
        "command": "powershell -NoProfile -ExecutionPolicy Bypass -File \"C:/Users/<you>/.claude/skills/todo-review/todo-reminder.ps1\"",
        "timeout": 30
      } ] }
    ]
  }
  ```
- Codex: a `SessionStart` hook with matcher `startup` in `~/.codex/hooks.json`. See the [Codex hooks docs](https://learn.chatgpt.com/docs/hooks.md).
- Gemini CLI: a `SessionStart` hook with matcher `startup` in the `hooks` object of `~/.gemini/settings.json`. See the [Gemini CLI hooks docs](https://geminicli.com/docs/hooks/).

### `/wrap-up` (Claude Code, Codex, Gemini CLI)

```
/wrap-up [push | pr] [notes for the recap]
```

Ends a work session in this order:

1. If code or config changed and has not been checked, `sonnet-checker` checks it.
2. Commits the files that this session changed, named one by one (never `git add -A`). Files that look like secrets and unrelated files stay out.
3. Writes unfinished work and decisions that wait for you to the current project's to-do list (in the `todo-review` format).
4. Ends with a recap that stands on its own: what was done, the check result, the commit and where it went, the leftover item numbers, and the next step.

By default it commits locally only. It pushes or opens a pull request only when you write `push` or `pr`, or ask for it in the same request. It never force-pushes, merges, deletes a branch or creates a repository. The project's own rules (for example "never push") win over this skill. Claude may also start it when you say "wrap up" or "收工".

### `/session-review` (Claude Code only)

```
/session-review [days, default 30] [project name filter]
```

Reviews your recent Claude Code sessions to find three things: what you want to be told, which questions you did not need to be asked, and which repeated requests could become a skill, a script or a rule. `session_review.py` reads the transcripts in `~/.claude/projects/`, extracts your messages, the multiple-choice questions you were asked and your answers, and measures how often you took the recommended option. It writes its output to a temp folder, because the output holds private conversation text. When there are many messages, the skill splits them into parts and has several `sonnet-search` agents read them at once. It ends with proposals and builds nothing until you pick.

Run the script with `uv run --no-project python`. On Windows, a plain `python` may start the Microsoft Store stub. It runs only when you type `/session-review`.

### `/brain` (Claude Code only)

```
/brain <the job and what done means>
```

Runs a big job with Fable (high effort) as the brain. Fable plans the job, splits it into parts, briefs the agents above, and judges what comes back. It delegates only when that pays off, such as independent parts, work too large for one session, or repetitive work. Planning, root causes and final decisions stay with Fable. Before it calls the job done, `sonnet-checker` checks the result.

It runs only when you type `/brain`. Claude never starts it on its own. It is not in `portable/`, because it depends on Claude models, Claude-only frontmatter fields and the Claude agent team.

## Maintaining this repo

1. Edit `agents/` or `skills/`.
2. Regenerate the portable files:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\build.ps1
   ```
3. Preview, then deploy. Leave out `-All` to deploy to Claude Code only:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\deploy.ps1 -All -DryRun
   powershell -ExecutionPolicy Bypass -File .\deploy.ps1 -All
   ```
   `deploy.ps1` first saves the current copies to `%TEMP%\claude-deploy-backup\<timestamp>`. It adds and overwrites files, and never deletes anything in the target folders. It never touches `~/.claude/skills/synced/`, which holds Anthropic's skills that claude.ai syncs automatically.
4. Commit and push.

If you changed a file directly in `~/.claude`, copy the change back with `backup.ps1`, then run `build.ps1`. `backup.ps1` mirrors `~/.claude/agents` and `~/.claude/skills` into the repo with `robocopy /MIR`, so a file you deleted there is also deleted in the repo. It never changes `~/.claude`.

## Notes

- **Status**: the Claude Code files are tested. The Codex and Gemini CLI files follow the official docs, but they have not been run in Codex or Gemini CLI yet.
- Gemini CLI agent names allow only lowercase letters, numbers, hyphens and underscores, so `Explore` becomes `explore` in the Gemini files.
- On Gemini CLI, `run_shell_command` is the documented shell tool name in the hooks docs. The docs do not say what happens with an unknown tool name.
- The scripts are for Windows (PowerShell 5.1 and `robocopy`). They contain ASCII characters only, because Windows PowerShell 5.1 reads a UTF-8 file without a BOM in the system code page.
- `.gitattributes` keeps LF line endings, so installed files are byte-identical to the ones in the repo.
- The to-do lists themselves (`~/.agents/todo/`) stay on the local computer and are not in this repo.
