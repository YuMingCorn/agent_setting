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

## Agents

每個 agent 都是 Claude 用 Agent 工具啟動的 subagent。設計原則是依工作選模型：便宜的機械式工作用 Haiku，需要判斷的搜尋和檢查用 Sonnet，實作用 Opus。

| Agent | 模型 | 工具 | 用途 |
|---|---|---|---|
| `Explore` | Haiku | Read、Grep、Glob、WebFetch、WebSearch | 有明確關鍵字或目標的唯讀搜尋：找檔案、搜尋程式碼、查文件。回傳簡短答案和 `path:line` 位置。 |
| `sonnet-search` | Sonnet | Read、Grep、Glob、WebFetch、WebSearch | 需要判斷的唯讀搜尋：追蹤程式碼或規則在檔案之間的關係，或找沒有明確關鍵字的東西。會分開列出親眼看到的和推論出來的。 |
| `haiku-audit` | Haiku | Read、Grep、Glob | 用一份簡短明確的清單檢查大量檔案（frontmatter 欄位、命名規則、禁用寫法）。逐條回報違規，不修改任何東西。 |
| `haiku-worker` | Haiku | 全部 | 結果容易檢查的大量重複工作：改名、擷取欄位、加標籤、簡短摘要。不寫程式。 |
| `opus-builder` | Opus | 全部 | 計畫決定後，照明確的說明實作。撰寫和修改程式碼與檔案，並逐檔回報改了什麼。 |
| `sonnet-checker` | Sonnet | Read、Grep、Glob、Bash（不能用 Write 和 Edit） | 工作完成前，對照說明檢查成果。會跑測試、讀差異、試邊界情況，最後回報 `PASS` 或 `FAIL`。 |

## Skills

### `/brain`

```
/brain <要做的工作，以及怎樣算完成>
```

讓 Fable（high effort）當大腦來執行大型工作。Fable 負責規劃、把工作拆成幾個部分、向上面的 agent 交代任務，並判斷交回來的成果。它只在划算時才分派工作，例如互不相依的部分、一個 session 做不完的工作，或大量重複的工作。規劃、找根本原因和最後的決定都由 Fable 自己做。宣布完成前，會先讓 `sonnet-checker` 檢查成果。

只有你輸入 `/brain` 時才會執行，Claude 不會自己啟動它。

### `/todo-review`

用一份清單管理所有專案的待決定事項，清單放在 `~/.claude/todo.md`。每個項目屬於一個專案資料夾（`*` 表示所有專案），狀態有 `open`、`decided`、`done`、`dropped` 四種。

| 指令 | 作用 |
|---|---|
| `/todo-review` | 一次問幾題，逐項詢問目前專案的 `open` 項目。有選項的項目會跳出選擇，沒選項的項目請你輸入怎麼做。每個回答都會寫回清單，然後執行屬於這個專案、剛決定的工作。 |
| `/todo-review add <描述>` | 為目前專案新增一個項目。 |
| `/todo-review list` | 列出目前專案的 `open` 和 `decided` 項目，不修改任何東西。 |

開啟新的 session 時，SessionStart hook `todo-reminder.ps1` 會計算目前資料夾有幾個 `open` 項目。有的話，Claude 會在第一次回覆時先進行 review。

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
