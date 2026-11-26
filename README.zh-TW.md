[English](README.md) | **繁體中文**

# Claude Code、Codex 與 Antigravity CLI 的 agent 設定

我自訂的 subagent 和 skill。原本為 Claude Code 撰寫，repo 也附上 Codex 和 Antigravity CLI（`agy`）的自動產生版本，方便把部分工作交給這些工具。

## Quick Start

Windows，一次裝好三個工具：

```powershell
git clone https://github.com/YuMingCorn/agent_setting.git
cd agent_setting
powershell -ExecutionPolicy Bypass -File .\deploy.ps1 -All
```

macOS 或 Linux（以 Codex 為例）：

```sh
git clone https://github.com/YuMingCorn/agent_setting.git
cd agent_setting
mkdir -p ~/.agents/skills ~/.codex/agents
cp -R portable/skills/* ~/.agents/skills/
cp portable/codex/agents/* ~/.codex/agents/
```

重新開啟工具，在 Claude Code 輸入 `/reframe <你的需求>` 試試看。只想裝單一工具，照下表複製即可：

| 工具 | 複製 | 到 |
|---|---|---|
| Claude Code | `agents/*`、`skills/*`、`tools/*` | `~/.claude/agents/`、`~/.claude/skills/`、`~/.claude/tools/` |
| Codex | `portable/skills/*`、`portable/codex/agents/*` | `~/.agents/skills/`、`~/.codex/agents/` |
| Antigravity CLI | `portable/skills/*`、`portable/antigravity/agents/*` | `~/.agents/skills/`（或 `~/.gemini/config/skills/`）、`~/.gemini/config/agents/` |

## 內容

| 路徑 | 內容 |
|---|---|
| `agents/` | 8 個 subagent，Claude Code 格式。**修改來源。** |
| `skills/` | 7 個 skill，Claude Code 格式。**修改來源。** |
| `tools/` | agent 呼叫的腳本，例如 `agy_run.py`。部署到 `~/.claude/tools/`。 |
| `portable/` | `build.ps1` 產生的 Codex、Antigravity CLI agent（`agy-runner` 除外），以及 [Agent Skills](https://agentskills.io/specification) 格式的 5 個 skill。不要手動修改。 |
| `build.ps1` | 從 `agents/` 和 `skills/` 產生 `portable/`。 |
| `deploy.ps1` | 把檔案複製到使用者資料夾。 |
| `backup.ps1` | 把直接在 `~/.claude` 做的修改複製回 repo。 |

## Agents

主 agent 依工作類型啟動的 subagent：機械式工作用 Haiku，需要判斷的搜尋和檢查用 Sonnet，實作用 Opus。

| Agent | 模型 | 工具 | 用途 |
|---|---|---|---|
| `haiku-explore` | Haiku | Read、Grep、Glob | 有明確目標的本機搜尋，回傳 `path:line`。 |
| `sonnet-search` | Sonnet | Read、Grep、Glob | 需要判斷的本機搜尋，例如追蹤跨檔案的關係。 |
| `sonnet-web` | Sonnet | WebSearch、WebFetch | 上網查文件、API 和版本，每個結論附網址和日期。 |
| `haiku-audit` | Haiku | Read、Grep、Glob | 用明確清單檢查大量檔案，只回報違規。 |
| `haiku-worker` | Haiku | 全部 | 結果容易檢查的大量重複工作，不寫程式。 |
| `opus-builder` | Opus | 全部 | 計畫定案後照說明實作，逐檔回報修改。 |
| `sonnet-checker` | Sonnet | Read、Grep、Glob、Bash | 完成前對照說明檢查成果，回報 `PASS` 或 `FAIL`。 |
| `agy-runner` | Haiku | Read、Bash | 只限 Claude Code。把寫好的任務交給 Antigravity CLI（`agy`）執行，回報它改了什麼。只在你要求用 agy 時使用。 |

Codex 和 Antigravity CLI 版本有以下差異：

- 不指定模型，沿用主 session 的模型。
- Antigravity CLI 的工具名稱會自動轉換，例如 `Read` 轉成 `read_file`。它的自訂 agent 拿不到搜尋工具，所以 `Grep` 和 `Glob` 轉成 `run_command`（用 shell 指令搜尋），`WebFetch` 轉成 `search_web`。沒有 `tools` 的 agent 會寫入完整的工具清單，因為 Antigravity 只給這種 agent 一小組唯讀工具。
- Codex 不能限制工具，所以「唯讀」和「只查本機或只查網路」只靠說明約束。Antigravity CLI 的搜尋 agent 需要 `run_command`，所以「唯讀」也只靠說明約束。

### `agy-runner`（只限 Claude Code）

主 agent 先把任務寫成檔案，`agy-runner` 再執行 `tools/agy_run.py`。腳本依任務類型（`read`、`rewrite`、`simple`）選模型，跳過你說額度已用完的組別，並透過 `agy acp` 自己回答每個權限請求：

- 只能寫進 `--write` 指定的資料夾。沒有 `--write` 就是唯讀任務。
- shell 指令必須以 `--allow-cmd` 指定的前綴開頭，而且不能有引號、管線或 `..`。
- 結束時列出寫入範圍內和範圍外有變動的檔案。

限制不到的部分（2026-11-26 用 agy 1.5.18 實測）：agy 讀檔不會詢問，`.env` 也讀得到。它也會自己放行寫進系統暫存資料夾的動作，所以腳本拒絕在暫存資料夾裡的專案。不用一般的 `agy -p`，因為這個模式下 agy 可以不經詢問寫到任何地方。

## Skills

| Skill | 可用工具 | 用途 |
|---|---|---|
| `/reframe` | Claude Code、Codex、Antigravity CLI | 動手前把問題定義對，重寫需求。 |
| `/sharpen` | Claude Code、Codex、Antigravity CLI | 把做法和驗收拉到頂尖水準，重寫提示詞。 |
| `/restate` | Claude Code、Codex、Antigravity CLI | 用自己的話重述你的目標並提問。 |
| `/first-principle` | Claude Code、Codex、Antigravity CLI | 拆到公理，再從公理推演出解法。 |
| `/wrap-up` | Claude Code、Codex、Antigravity CLI | 收工：檢查、commit，並給總結。 |
| `/session-review` | 只限 Claude Code | 回顧最近的 session，建議新的 skill、腳本或規則。 |
| `/brain` | 只限 Claude Code | 用 Fable 規劃大型工作，再分派給 agent。 |

呼叫方式：Claude Code 和 Antigravity CLI 輸入 `/名稱`，Codex 輸入 `$名稱`。所有 skill 都只在你明確呼叫時執行。Claude Code 靠 `disable-model-invocation: true` 強制做到，Codex 靠自動產生的 `agents/openai.yaml`。Antigravity CLI 沒有這種設定，只能靠描述要求模型不要自行啟動。

### `/reframe`

```
/reframe [要釐清的需求]
```

動手前先把問題想對、說對。它讀一手材料，選定需求的解讀，整理 8–12 個關鍵術語（附已核驗的出處）、相鄰領域的做法和遺漏的約束，最後重寫成可以交給 agent 的需求。它不實作。

### `/sharpen`

```
/sharpen [要做深的需求，通常是 /reframe 的產出]
```

把做法拉到頂尖從業者的水準。技術選型先用小實驗驗證再建議，產品取捨列出選項留給你決定；驗收只認外部證據，例如測試或基準。最後輸出一份可以直接執行的提示詞。建議順序：`/reframe` → `/sharpen` → 實作。

### `/restate`

```
/restate [要重述的任務，預設是你最新的要求]
```

動手前用自己的話說出你的目標、問題和它做的猜測，再列出附預設答案的問題，等你回覆。這一輪只讀檔案，不做任何修改。

### `/first-principle`

```
/first-principle [要思考的問題，預設是你最新的要求]
```

把一般解法背後的假設分成公理、慣例和未驗證的看法，只用公理重新推演解法，並說明和一般做法相比的風險。事實靠讀程式碼或實測確認，不憑記憶。

### `/wrap-up`

```
/wrap-up [push | pr] [要寫進總結的備註]
```

收工：還沒檢查的改動先交給 `sonnet-checker`，逐檔 commit 這個 session 的修改，最後給一段總結，列出沒做完的事。只有寫了 `push` 或 `pr` 才推送或開 PR；不會 force-push、merge 或刪除分支。

### `/session-review`（只限 Claude Code）

```
/session-review [天數，預設 30] [專案名稱篩選]
```

讀 `~/.claude/projects/` 裡的對話紀錄，找出你想被告知的事、不必問你的問題，以及目前專案裡可以做成 skill、腳本或規則的事。它會先讀過去的複盤和你現有的規則，所以不會重提你拒絕過的建議，也不會重複已有的規則。它只列出編號的建議，你選了才動手。腳本用 `uv run --no-project python` 執行。

### `/brain`（只限 Claude Code）

```
/brain <要做的工作，以及怎樣算完成>
```

由 Fable（high effort）規劃和拆解大型工作，只在划算時分派給上面的 agent，宣布完成前先讓 `sonnet-checker` 檢查。它依賴 Claude 專屬的模型和功能，所以不在 `portable/` 裡。

## 維護這個 repo

1. 修改 `agents/` 或 `skills/`，再執行 `build.ps1` 重新產生 `portable/`。
2. 先預覽再部署（不加 `-All` 就只部署到 Claude Code）：
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\deploy.ps1 -All -DryRun
   powershell -ExecutionPolicy Bypass -File .\deploy.ps1 -All
   ```
   部署前會備份到 `%TEMP%\claude-deploy-backup\`。它只新增和覆蓋檔案，不刪除，也不碰 `~/.claude/skills/synced/`。
3. commit 並推送。

直接改了 `~/.claude`（`agents`、`skills` 或 `tools`）的話，先執行 `backup.ps1` 再執行 `build.ps1`。`backup.ps1` 用 `robocopy /MIR` 鏡像，所以在 `~/.claude` 刪掉的檔案，repo 裡也會刪掉。

## 注意

- Claude Code 版已測試。Antigravity CLI 的 agent 格式和工具名稱已在 2026-11-26 用 `agy` 實際確認。Codex 版照官方文件產生，還沒實際執行過。
- 腳本只能在 Windows 執行（PowerShell 5.1 和 `robocopy`），並且只用 ASCII 字元，避免 PowerShell 5.1 讀錯編碼。
- 產生 Antigravity CLI 版時，`build.ps1` 會把 agent 名稱轉成小寫，遇到小寫字母、數字、`-` 和 `_` 以外的字元就報錯。
- `.gitattributes` 固定使用 LF 換行。
