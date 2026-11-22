# Claude Code 全域設定備份

備份 `~/.claude` 底下的全域設定。目前包含：

| 資料夾 | 內容 |
|---|---|
| `agents/` | 自訂 subagent（`~/.claude/agents/*.md`） |
| `skills/` | 自訂 skill（`~/.claude/skills/<name>/SKILL.md`），不含 `skills/synced/` |

`skills/synced/` 是 claude.ai 自動同步的 Anthropic 官方 skill，登入後會自動下載，所以不備份。

## 備份

```powershell
powershell -ExecutionPolicy Bypass -File .\backup.ps1
git add -A
git commit -m "更新設定備份"
git push
```

`backup.ps1` 用 `robocopy /MIR` 把來源鏡像到 repo：在 `~/.claude` 刪掉的檔案，repo 裡也會刪掉。它只寫入 repo，不會改動 `~/.claude`。

## 還原到新電腦

```powershell
git clone https://github.com/YuMingCorn/agent_setting.git
cd agent_setting
robocopy .\agents "$env:USERPROFILE\.claude\agents" /E
robocopy .\skills "$env:USERPROFILE\.claude\skills" /E
```

`/E` 只新增和覆蓋檔案，不會刪掉目的地原有的檔案。還原後重新開啟 Claude Code 即可。

## 注意

部分檔案裡有本機路徑（例如 `C:\Users\Corn\.claude\todo.md`）。在別的電腦還原時，使用者名稱不同就要手動改路徑。
