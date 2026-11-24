[English](README.md) | **繁體中文**

# Claude Code、Codex 與 Gemini CLI 的 agent 設定

這是我自訂的 subagent 和 skill。它們原本是為 Claude Code 寫的，這個 repo 也附上為 OpenAI Codex 和 Google Gemini CLI 產生的版本，所以任何人都可以裝到自己用的工具裡。

## 內容

| 路徑 | 內容 |
|---|---|
| `agents/` | 7 個自訂 subagent，Claude Code 格式。**修改來源。** |
| `skills/brain/` | `/brain` skill。只能在 Claude Code 使用。 |
| `skills/todo-review/` | `/todo-review` skill 和它的 SessionStart hook 腳本 `todo-reminder.ps1`。**修改來源。** |
| `skills/wrap-up/` | `/wrap-up` skill。**修改來源。** |
| `skills/restate/` | `/restate` skill。**修改來源。** |
| `skills/first-principle/` | `/first-principle` skill。**修改來源。** |
| `skills/session-review/` | `/session-review` skill 和它的腳本 `session_review.py`。只能在 Claude Code 使用。 |
| `portable/skills/` | 開放標準 [Agent Skills](https://agentskills.io/specification) 格式的 `todo-review`、`wrap-up`、`restate` 和 `first-principle`，frontmatter 只有 `name` 和 `description`。自動產生。 |
| `portable/codex/agents/` | 7 個 agent 的 Codex TOML 檔。自動產生。 |
| `portable/gemini/agents/` | 7 個 agent 的 Gemini CLI Markdown 檔。自動產生。 |
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
| `haiku-explore` | Haiku | Read、Grep、Glob | 有明確關鍵字或目標的本機唯讀搜尋：找檔案、搜尋程式碼、讀本機文件。不能上網。回傳簡短答案和 `path:line` 位置。 |
| `sonnet-search` | Sonnet | Read、Grep、Glob | 需要判斷的本機唯讀搜尋：追蹤程式碼或規則在檔案之間的關係，或找沒有明確關鍵字的東西。不能上網。會分開列出親眼看到的和推論出來的。 |
| `sonnet-web` | Sonnet | WebSearch、WebFetch | 唯讀的上網查詢：文件、API、版本、發布紀錄和其他公開資訊。不能讀本機檔案。優先用第一手來源，每個結論都附網址和日期。 |
| `haiku-audit` | Haiku | Read、Grep、Glob | 用一份簡短明確的清單檢查大量檔案（frontmatter 欄位、命名規則、禁用寫法）。逐條回報違規，不修改任何東西。 |
| `haiku-worker` | Haiku | 全部 | 結果容易檢查的大量重複工作：改名、擷取欄位、加標籤、簡短摘要。不寫程式。 |
| `opus-builder` | Opus | 全部 | 計畫決定後，照明確的說明實作。撰寫和修改程式碼與檔案，並逐檔回報改了什麼。 |
| `sonnet-checker` | Sonnet | Read、Grep、Glob、Bash（不能用 Write 和 Edit） | 工作完成前，對照說明檢查成果。會跑測試、讀差異、試邊界情況，最後回報 `PASS` 或 `FAIL`。 |

產生的版本有三個不同的地方：

- **模型**：Codex 和 Gemini 的檔案沒有指定模型，所以每個 agent 都用主 session 的模型。要指定的話，加上 `model = "..."`（Codex）或 `model: ...`（Gemini）。
- **Gemini CLI 的工具**：工具清單會換成 Gemini 的名稱，例如 `Read` 換成 `read_file`、`Grep` 換成 `grep_search`。沒有工具清單的 agent 可以用全部工具。
- **Codex 的工具**：Codex 的 agent 檔不能限制工具。Codex 的 subagent 沿用主 agent 的沙箱和核准設定，所以唯讀 agent 能保持唯讀，只是因為它們的說明要求它們不要修改檔案。本機搜尋和上網搜尋的區分也一樣：在 Codex 上，`haiku-explore` 和 `sonnet-search` 仍然可能上網，`sonnet-web` 也仍然可能讀本機檔案。

## Skills

| Skill | 工具 | 用途 |
|---|---|---|
| `/todo-review` | Claude Code、Codex、Gemini CLI | 問你目前專案待辦清單裡還沒決定的事。 |
| `/wrap-up` | Claude Code、Codex、Gemini CLI | 結束工作：檢查、commit、記下沒做完的事，最後給一段總結。 |
| `/restate` | Claude Code、Codex、Gemini CLI | 開始工作前，先用自己的話重述你的目標並提問。 |
| `/first-principle` | Claude Code、Codex、Gemini CLI | 把問題拆到公理，再從公理重新推演出解法。 |
| `/session-review` | 只能在 Claude Code 使用 | 回顧你最近的 session，提出可以做成 skill、腳本或規則的建議。 |
| `/brain` | 只能在 Claude Code 使用 | 用 Fable 規劃大型工作，再交給各個 agent 執行。 |

呼叫方式：在 Claude Code 裡輸入 `/名稱`，在 Codex 裡輸入 `$名稱`（例如 `$first-principle`）。在 Gemini CLI 裡直接用文字要求，例如「用第一原理想這個問題」。三個工具裡，只要你的說法符合 skill 的描述，agent 也可能自動啟動它。

### `/todo-review`（Claude Code、Codex、Gemini CLI）

每個專案有自己的待決定事項清單，放在 `~/.agents/todo/`，一個專案一個檔案（例如 `D--Projects-example.md`）。檔案開頭的 `project:` 寫專案根目錄，也就是 git repo 的最上層；不在 git 裡時就是當時的資料夾。清單放在所有專案資料夾之外，所以不會進 git。所有工具共用同一份清單。skill 只讀目前專案的清單，不會提到其他專案。每個項目的狀態有 `open`、`decided`、`done`、`dropped` 四種。

| 指令 | 作用 |
|---|---|
| `/todo-review` | 一次問幾題，逐項詢問目前專案的 `open` 項目。有選項的項目會跳出選擇，沒選項的項目請你輸入怎麼做。每個回答都會寫回清單，然後執行剛決定的工作。 |
| `/todo-review add <描述>` | 為目前專案新增一個項目。 |
| `/todo-review list` | 列出目前專案的 `open` 和 `decided` 項目，不修改任何東西。 |

在 Codex 裡用 `$todo-review` 呼叫這個 skill。在 Gemini CLI 裡直接用文字要求，例如「看待辦」。這個 skill 會用你的語言提問。它在 Claude Code 用 `AskUserQuestion`，在 Gemini CLI 用 `ask_user`，沒有提問工具時就直接用文字問。

舊版把所有專案放在同一個 `~/.agents/todo.md`。如果這個檔案還在，skill 會把屬於目前專案的項目搬進新清單，不會刪掉舊檔案本身。

**選用的開啟提醒。** `todo-reminder.ps1` 會在 session 開啟時，計算目前專案的清單有幾個 `open` 項目。有的話，agent 會在第一次回覆時先進行 review。三個工具都讀同一種 hook 輸出（`systemMessage` 和 `hookSpecificOutput.additionalContext`）。腳本需要 Windows PowerShell 5.1 或 PowerShell 7（`pwsh`）。把它加到工具的 hook 設定，並把路徑改成你安裝 skill 的位置：

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

### `/wrap-up`（Claude Code、Codex、Gemini CLI）

```
/wrap-up [push | pr] [要寫進總結的備註]
```

結束一個工作 session，依序做這幾件事：

1. 如果程式或設定改過、還沒檢查，先讓 `sonnet-checker` 檢查。
2. commit 這個 session 改的檔案，一個一個指定，不用 `git add -A`。看起來像密碼的檔案和不相關的檔案不會 commit。
3. 把沒做完的工作和等你決定的事寫進目前專案的待辦清單（`todo-review` 的格式）。
4. 最後給一段可以單獨閱讀的總結：做了什麼、檢查結果、commit 和推到哪裡、剩下的待辦編號、下一步。

預設只在本機 commit。只有你寫了 `push` 或 `pr`，或在同一句話裡要求推送，它才會推送或開 PR。它不會 force-push、merge、刪除分支或建立 repo。專案自己的規則（例如「不要 push」）比這個 skill 優先。你說「收工」時，Claude 也可以自己啟動它。

### `/restate`（Claude Code、Codex、Gemini CLI）

```
/restate [要重述的任務，預設是你最新的要求]
```

在開始工作之前，agent 先用自己的話說出你的目標、你想解決的問題，以及它做了哪些猜測。最後列出編號的問題，最重要的排第一，每題都附上預設答案，然後等你回覆。這一輪它不改任何檔案，只會讀檔案和執行唯讀指令來了解你的要求。你回答之後，它就開始做事。你說「先別動手」、「用你自己的話說」或「restate in your own words」時，Claude 也可能自動啟動它。

### `/first-principle`（Claude Code、Codex、Gemini CLI）

```
/first-principle [要思考的問題，預設是你最新的要求]
```

用第一原理思維解決問題。agent 先寫出不含任何做法的目標，再列出一般解法背後的所有假設。它把每個假設拆到最基本的事實，標成公理（不論誰的偏好都成立的事實）、慣例（只因為大家這樣選才成立）或未驗證的看法。接著只用公理重新推演出解法，列出每一步推理，並和一般做法比較，說明每個改變的風險。它會讀程式碼、執行指令或實際量測來確認事實，不憑記憶。你說「第一原理」、「第一性原理」、「從根本想」、「拆到最基本」或「first principles」時，Claude 也可能自動啟動它。

### `/session-review`（只能在 Claude Code 使用）

```
/session-review [天數，預設 30] [專案名稱篩選]
```

複盤最近的 Claude Code session，找出三件事：你想要被告訴什麼、哪些問題其實不用問你、哪些重複的要求可以做成 skill、腳本或規則。`session_review.py` 會讀 `~/.claude/projects/` 裡的對話紀錄，抽出你打的訊息、問過你的選擇題和你的回答，並算出你選「建議」選項的比例。輸出寫到暫存資料夾，因為裡面有私人對話內容。訊息太多時，skill 會把它分成幾份，交給幾個 `sonnet-search` agent 同時讀。最後它只提出建議，等你選了才會動手。

執行腳本要用 `uv run --no-project python`。在 Windows 上，直接打 `python` 可能會叫到 Microsoft Store 的空殼程式。只有你輸入 `/session-review` 時才會執行。

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
- Gemini CLI 的 agent 名稱只能用小寫字母、數字、連字號和底線。`build.ps1` 產生 Gemini 檔案時會把名稱轉成小寫，遇到其他字元就報錯停止。
- 在 Gemini CLI 上，`run_shell_command` 是 hooks 文件裡寫的 shell 工具名稱。文件沒有說明遇到不認得的工具名稱時會怎樣。
- 腳本只能在 Windows 上執行，需要 PowerShell 5.1 和 `robocopy`。腳本只用英文字元，因為 Windows PowerShell 5.1 會用系統編碼讀取沒有 BOM 的 UTF-8 檔案，中文會變成亂碼。
- `.gitattributes` 固定使用 LF 換行，所以安裝出來的檔案和 repo 裡的檔案完全相同。
- 待辦清單本身（`~/.agents/todo/`）只放在本機，不在這個 repo 裡。
