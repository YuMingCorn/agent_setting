[English](README.md) | **繁體中文**

# Claude Code、Codex 與 Gemini CLI 的 agent 設定

這是我自訂的 subagent 和 skill。它們原本是為 Claude Code 寫的，這個 repo 也附上為 OpenAI Codex 和 Google Gemini CLI 產生的版本，所以任何人都可以裝到自己用的工具裡。

## 內容

| 路徑 | 內容 |
|---|---|
| `agents/` | 6 個自訂 subagent，Claude Code 格式。**修改來源。** |
| `skills/brain/` | `/brain` skill。只能在 Claude Code 使用。 |
| `skills/todo-review/` | `/todo-review` skill 和它的 SessionStart hook 腳本 `todo-reminder.ps1`。**修改來源。** |
| `portable/skills/` | 開放標準 [Agent Skills](https://agentskills.io/specification) 格式的 `todo-review`，frontmatter 只有 `name` 和 `description`。自動產生。 |
| `portable/codex/agents/` | 6 個 agent 的 Codex TOML 檔。自動產生。 |
| `portable/gemini/agents/` | 6 個 agent 的 Gemini CLI Markdown 檔。自動產生。 |
| `build.ps1` | 從 `agents/` 和 `skills/` 產生 `portable/`。 |
| `deploy.ps1` | 把檔案複製到你的使用者資料夾。 |
| `backup.ps1` | 把直接在 `~/.claude` 做的修改複製回 repo。 |

不要手動修改 `portable/` 裡的檔案。請改 `agents/` 或 `skills/`，再執行 `build.ps1`。

## 安裝

選擇你的工具對應的資料夾，複製過去就好，不需要執行任何腳本。

| 工具 | 複製 | 到 |
|---|---|---|
| Claude Code | `agents/*` | `~/.claude/agents/` |
| Claude Code | `skills/*` | `~/.claude/skills/` |
| Codex | `portable/skills/*` | `~/.agents/skills/` |
| Codex | `portable/codex/agents/*` | `~/.codex/agents/` |
| Gemini CLI | `portable/skills/*` | `~/.agents/skills/`（或 `~/.gemini/skills/`） |
| Gemini CLI | `portable/gemini/agents/*` | `~/.gemini/agents/` |

macOS 或 Linux，以 Codex 為例：

```sh
git clone https://github.com/YuMingCorn/agent_setting.git
cd agent_setting
mkdir -p ~/.agents/skills ~/.codex/agents
cp -R portable/skills/* ~/.agents/skills/
cp portable/codex/agents/* ~/.codex/agents/
```

Windows，一次安裝所有工具：

```powershell
git clone https://github.com/YuMingCorn/agent_setting.git
cd agent_setting
powershell -ExecutionPolicy Bypass -File .\deploy.ps1 -All
```

安裝後重新開啟工具。

## Agents

每個 agent 都是主 agent 為了某項工作啟動的 subagent。設計原則是依工作選模型：便宜的機械式工作用小模型，需要判斷的搜尋和檢查用中型模型，實作用最強的模型。

| Agent | Claude 模型 | 工具 | 用途 |
|---|---|---|---|
| `Explore` | Haiku | Read、Grep、Glob、WebFetch、WebSearch | 有明確關鍵字或目標的唯讀搜尋：找檔案、搜尋程式碼、查文件。回傳簡短答案和 `path:line` 位置。 |
| `sonnet-search` | Sonnet | Read、Grep、Glob、WebFetch、WebSearch | 需要判斷的唯讀搜尋：追蹤程式碼或規則在檔案之間的關係，或找沒有明確關鍵字的東西。會分開列出親眼看到的和推論出來的。 |
| `haiku-audit` | Haiku | Read、Grep、Glob | 用一份簡短明確的清單檢查大量檔案（frontmatter 欄位、命名規則、禁用寫法）。逐條回報違規，不修改任何東西。 |
| `haiku-worker` | Haiku | 全部 | 結果容易檢查的大量重複工作：改名、擷取欄位、加標籤、簡短摘要。不寫程式。 |
| `opus-builder` | Opus | 全部 | 計畫決定後，照明確的說明實作。撰寫和修改程式碼與檔案，並逐檔回報改了什麼。 |
| `sonnet-checker` | Sonnet | Read、Grep、Glob、Bash（不能用 Write 和 Edit） | 工作完成前，對照說明檢查成果。會跑測試、讀差異、試邊界情況，最後回報 `PASS` 或 `FAIL`。 |

產生的版本有三個不同的地方：

- **模型**：Codex 和 Gemini 的檔案沒有指定模型，所以每個 agent 都用主 session 的模型。要指定的話，加上 `model = "..."`（Codex）或 `model: ...`（Gemini）。
- **Gemini CLI 的工具**：工具清單會換成 Gemini 的名稱，例如 `Read` 換成 `read_file`、`Grep` 換成 `grep_search`。沒有工具清單的 agent 可以用全部工具。
- **Codex 的工具**：Codex 的 agent 檔不能限制工具。Codex 的 subagent 沿用主 agent 的沙箱和核准設定，所以唯讀 agent 能保持唯讀，只是因為它們的說明要求它們不要修改檔案。

## Skills

### `/todo-review`（Claude Code、Codex、Gemini CLI）

用一份清單管理所有專案、所有工具的待決定事項，清單放在 `~/.agents/todo.md`。每個項目屬於一個專案資料夾（`*` 表示所有專案），狀態有 `open`、`decided`、`done`、`dropped` 四種。

| 指令 | 作用 |
|---|---|
| `/todo-review` | 一次問幾題，逐項詢問目前專案的 `open` 項目。有選項的項目會跳出選擇，沒選項的項目請你輸入怎麼做。每個回答都會寫回清單，然後執行屬於這個專案、剛決定的工作。 |
| `/todo-review add <描述>` | 為目前專案新增一個項目。 |
| `/todo-review list` | 列出目前專案的 `open` 和 `decided` 項目，不修改任何東西。 |

在 Codex 裡用 `$todo-review` 呼叫這個 skill。在 Gemini CLI 裡直接用文字要求，例如「看待辦」。這個 skill 會用你的語言提問。它在 Claude Code 用 `AskUserQuestion`，在 Gemini CLI 用 `ask_user`，沒有提問工具時就直接用文字問。

**選用的開啟提醒。** `todo-reminder.ps1` 會在 session 開啟時，計算目前資料夾有幾個 `open` 項目。有的話，agent 會在第一次回覆時先進行 review。三個工具都讀同一種 hook 輸出（`systemMessage` 和 `hookSpecificOutput.additionalContext`）。腳本需要 Windows PowerShell 5.1 或 PowerShell 7（`pwsh`）。把它加到工具的 hook 設定，並把路徑改成你安裝 skill 的位置：

- Claude Code，在 `~/.claude/settings.json`：
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
- Codex：在 `~/.codex/hooks.json` 加一個 matcher 為 `startup` 的 `SessionStart` hook。請參考 [Codex hooks 文件](https://learn.chatgpt.com/docs/hooks.md)。
- Gemini CLI：在 `~/.gemini/settings.json` 的 `hooks` 物件加一個 matcher 為 `startup` 的 `SessionStart` hook。請參考 [Gemini CLI hooks 文件](https://geminicli.com/docs/hooks/)。

### `/brain`（只能在 Claude Code 使用）

```
/brain <要做的工作，以及怎樣算完成>
```

讓 Fable（high effort）當大腦來執行大型工作。Fable 負責規劃、把工作拆成幾個部分、向上面的 agent 交代任務，並判斷交回來的成果。它只在划算時才分派工作，例如互不相依的部分、一個 session 做不完的工作，或大量重複的工作。規劃、找根本原因和最後的決定都由 Fable 自己做。宣布完成前，會先讓 `sonnet-checker` 檢查成果。

只有你輸入 `/brain` 時才會執行，Claude 不會自己啟動它。它不在 `portable/` 裡，因為它依賴 Claude 的模型、Claude 專用的 frontmatter 欄位和 Claude 的 agent 團隊。

## 維護這個 repo

1. 修改 `agents/` 或 `skills/`。
2. 重新產生通用版檔案：
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\build.ps1
   ```
3. 先預覽，再部署。不加 `-All` 就只部署到 Claude Code：
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\deploy.ps1 -All -DryRun
   powershell -ExecutionPolicy Bypass -File .\deploy.ps1 -All
   ```
   `deploy.ps1` 會先把目前的版本存到 `%TEMP%\claude-deploy-backup\<時間>`。它只新增和覆蓋檔案，不會刪除目標資料夾裡的任何東西。它也不會碰 `~/.claude/skills/synced/`，那裡是 claude.ai 自動同步的 Anthropic 官方 skill。
4. commit 並推送。

如果你直接在 `~/.claude` 改了檔案，先用 `backup.ps1` 把變更複製回來，再執行 `build.ps1`。`backup.ps1` 用 `robocopy /MIR` 把 `~/.claude/agents` 和 `~/.claude/skills` 鏡像到 repo，所以在那裡刪掉的檔案，repo 裡也會刪掉。它不會改動 `~/.claude`。

## 注意

- **測試狀態**：Claude Code 的檔案已經測試過。Codex 和 Gemini CLI 的檔案是照官方文件產生的，但還沒有在 Codex 或 Gemini CLI 裡實際執行過。
- Gemini CLI 的 agent 名稱只能用小寫字母、數字、連字號和底線，所以 `Explore` 在 Gemini 的檔案裡改成 `explore`。
- 在 Gemini CLI 上，`run_shell_command` 是 hooks 文件裡寫的 shell 工具名稱。文件沒有說明遇到不認得的工具名稱時會怎樣。
- 腳本只能在 Windows 上執行，需要 PowerShell 5.1 和 `robocopy`。腳本只用英文字元，因為 Windows PowerShell 5.1 會用系統編碼讀取沒有 BOM 的 UTF-8 檔案，中文會變成亂碼。
- `.gitattributes` 固定使用 LF 換行，所以安裝出來的檔案和 repo 裡的檔案完全相同。
- 待辦清單本身（`~/.agents/todo.md`）只放在本機，不在這個 repo 裡。
