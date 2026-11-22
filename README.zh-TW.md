[English](README.md) | **繁體中文**

# Claude Code 全域設定

這是 `~/.claude` 裡全域 Claude Code 設定的備份。這個 repo 是修改來源：先在這裡改檔案，再部署到 `~/.claude`。

## 內容

| 資料夾 | 內容 |
|---|---|
| `agents/` | 自訂 subagent（`~/.claude/agents/*.md`） |
| `skills/brain/` | `/brain`：Fable 負責規劃和判斷，Opus、Sonnet、Haiku subagent 負責執行 |
| `skills/todo-review/` | 全域待決定清單，session 開啟時逐項詢問。包含它的 SessionStart hook 腳本 `todo-reminder.ps1` |

`~/.claude/skills/synced/` 不備份。裡面是 Anthropic 的官方 skill，登入 claude.ai 後會自動同步下來。

## 修改流程

1. 在這個 repo 修改檔案，然後 commit。
2. 預覽 `~/.claude` 會有哪些變動：
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\deploy.ps1 -DryRun
   ```
3. 部署：
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\deploy.ps1
   ```
   `deploy.ps1` 會先把 `~/.claude` 裡目前的版本存到 `%TEMP%\claude-deploy-backup\<時間>`。它只新增和覆蓋檔案，不會刪除 `~/.claude` 裡的任何東西。
4. 推送：`git push`。

如果你直接在 `~/.claude` 改了檔案，先把變更複製回 repo：

```powershell
powershell -ExecutionPolicy Bypass -File .\backup.ps1
```

`backup.ps1` 用 `robocopy /MIR` 把 `~/.claude` 鏡像到 repo，所以在 `~/.claude` 刪掉的檔案，repo 裡也會刪掉。它不會改動 `~/.claude`。

## 在新電腦還原

```powershell
git clone https://github.com/YuMingCorn/agent_setting.git
cd agent_setting
powershell -ExecutionPolicy Bypass -File .\deploy.ps1
```

`todo-review` 需要 `~/.claude/settings.json` 裡的 SessionStart hook。`settings.json` 不在這個 repo 裡，所以要手動加上：

```json
"hooks": {
  "SessionStart": [
    { "hooks": [ {
      "type": "command",
      "command": "powershell -NoProfile -ExecutionPolicy Bypass -File \"C:/Users/<你的使用者名稱>/.claude/skills/todo-review/todo-reminder.ps1\"",
      "timeout": 30
    } ] }
  ]
}
```

還原後重新開啟 Claude Code。

## 注意

- 腳本只能在 Windows 上執行，需要 PowerShell 5.1 和 `robocopy`。腳本只用英文字元，因為 Windows PowerShell 5.1 會用系統編碼讀取沒有 BOM 的 UTF-8 檔案，中文會變成亂碼。
- `.gitattributes` 固定使用 LF 換行，所以還原出來的檔案和原始檔完全相同。
- 待辦清單本身（`~/.claude/todo.md`）只放在本機，不備份。
