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
