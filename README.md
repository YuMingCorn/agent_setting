**English** | [繁體中文](README.zh-TW.md)

# Claude Code global settings

A backup of my global Claude Code settings from `~/.claude`. This repo is the source of truth: I edit the files here, then deploy them to `~/.claude`.

## Contents

| Folder | What it holds |
|---|---|
| `agents/` | Custom subagents (`~/.claude/agents/*.md`) |
| `skills/brain/` | `/brain`: Fable plans and judges, and Opus, Sonnet and Haiku subagents do the work |
| `skills/todo-review/` | A global to-do list of open decisions, asked one by one at session start. Includes its SessionStart hook script `todo-reminder.ps1` |

`~/.claude/skills/synced/` is not backed up. It holds Anthropic's skills that claude.ai syncs automatically after you sign in.

## Agents

Each agent is a subagent that Claude starts with the Agent tool. The idea is to match the model to the job: Haiku for cheap mechanical work, Sonnet for search and checks that need judgment, and Opus for building.

| Agent | Model | Tools | Use it for |
|---|---|---|---|
| `Explore` | Haiku | Read, Grep, Glob, WebFetch, WebSearch | Read-only search with a known keyword or target: find files, grep code, look up docs. Returns a short answer with `path:line` locations. |
| `sonnet-search` | Sonnet | Read, Grep, Glob, WebFetch, WebSearch | Read-only search that needs judgment: trace how code or rules connect across files, or find something without a known keyword. Separates what it saw from what it inferred. |
| `haiku-audit` | Haiku | Read, Grep, Glob | Check many files against a short, explicit checklist (frontmatter fields, naming rules, forbidden patterns). Reports each violation and changes nothing. |
| `haiku-worker` | Haiku | All | Repetitive work across many items whose results are easy to check: renaming, extracting fields, tagging, short summaries. Not for code. |
| `opus-builder` | Opus | All | Build from a clear brief after the plan is decided. Writes and changes code and files, and reports what it changed file by file. |
| `sonnet-checker` | Sonnet | Read, Grep, Glob, Bash (no Write or Edit) | Check finished work against its brief before it is called done. Runs tests, reads the diff, tries edge cases, and ends with `PASS` or `FAIL`. |

## Skills

### `/brain`

```
/brain <the job and what done means>
```

Runs a big job with Fable (high effort) as the brain. Fable plans the job, splits it into parts, briefs the agents above, and judges what comes back. It delegates only when that pays off, such as independent parts, work too large for one session, or repetitive work. Planning, root causes and final decisions stay with Fable. Before it calls the job done, `sonnet-checker` checks the result.

It runs only when you type `/brain`. Claude never starts it on its own.

### `/todo-review`

Keeps one to-do list of open decisions for all projects in `~/.claude/todo.md`. Each item belongs to a project folder (or `*` for every project) and has a status: `open`, `decided`, `done` or `dropped`.

| Command | What it does |
|---|---|
| `/todo-review` | Asks you about each `open` item for the current project, a few at a time. Items with options show a choice; items without options ask you to type what to do. Writes each answer back to the list, then does the decided work that belongs to this project. |
| `/todo-review add <description>` | Adds a new item for the current project. |
| `/todo-review list` | Lists the `open` and `decided` items for the current project, and changes nothing. |

When you start a new session, the SessionStart hook `todo-reminder.ps1` counts the `open` items for the current folder. If there are any, Claude runs the review in its first reply.

## Workflow

1. Edit the files in this repo and commit.
2. Preview what will change in `~/.claude`:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\deploy.ps1 -DryRun
   ```
3. Deploy:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\deploy.ps1
   ```
   `deploy.ps1` first saves the current `~/.claude` copies to `%TEMP%\claude-deploy-backup\<timestamp>`. It adds and overwrites files, and never deletes anything under `~/.claude`.
4. Push: `git push`.

If you changed a file directly in `~/.claude`, copy the change back into the repo first:

```powershell
powershell -ExecutionPolicy Bypass -File .\backup.ps1
```

`backup.ps1` mirrors `~/.claude` into the repo with `robocopy /MIR`. A file you deleted in `~/.claude` is also deleted in the repo. It never changes `~/.claude`.

## Restore on a new computer

```powershell
git clone https://github.com/YuMingCorn/agent_setting.git
cd agent_setting
powershell -ExecutionPolicy Bypass -File .\deploy.ps1
```

`todo-review` needs a SessionStart hook in `~/.claude/settings.json`. `settings.json` is not in this repo, so add the hook by hand:

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

Restart Claude Code after you restore.

## Notes

- The scripts are for Windows (PowerShell 5.1 and `robocopy`). They contain ASCII characters only, because Windows PowerShell 5.1 reads a UTF-8 file without a BOM in the system code page.
- `.gitattributes` keeps LF line endings, so restored files are byte-identical to the originals.
- The to-do list itself (`~/.claude/todo.md`) stays on the local computer and is not backed up.
