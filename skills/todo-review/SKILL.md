---
name: todo-review
description: 讀取全域待辦清單 ~/.claude/todo.md，把目前專案「待決定」的項目一項一項問使用者：有選項的跳出選擇，沒選項的讓使用者輸入怎麼繼續，並把決定寫回清單。session 開啟時的提醒要求時、使用者說「看待辦」「review todo」或 /todo-review 時使用；也用來新增項目（/todo-review add …）。
argument-hint: "[add <描述> | list]（不帶參數就是逐項 review）"
---

# 待辦 review

清單檔：`~/.claude/todo.md`（Windows：`C:\Users\Corn\.claude\todo.md`）。所有專案共用一份，用 `project` 欄區分。清單只在本機，不進任何 git repo。

## 清單格式

每個項目是一個 H2 區塊。欄位名用英文（開啟提醒的 script 靠它們計數），內容用中文。

```markdown
## T-003 第 4b／4c 批來源要不要現在匯入
- project: D:\hackmd_llm_wiki
- added: 2026-11-19
- status: open
- context: 8 份已下載在 .llm-wiki/inbox/，雜湊核對過，等搬進 raw。
- options:
  - 現在搬入並批次匯入（建議）
  - 我自己搬：搬完後告訴你，再批次匯入
  - 這批不做了
- source: C:\Users\Corn\.claude\projects\D--hackmd-llm-wiki\memory\ai-agent-course-todo.md
```

- `project`：專案根目錄的 Windows 路徑；`*` 表示每個專案都要問。
- `status`：`open`（待決定）、`decided`（已決定，還有事要做）、`done`（做完）、`dropped`（取消）。只有 `open` 會被問。
- `options`：可省略。有就是「有選項的項目」；沒有就是「待輸入的項目」。建議的選項放第一個，結尾標「（建議）」。每個選項寫成一行；需要說明時用「短標題：說明」。
- 清單檔裡不要放 code block（開啟提醒的 script 會略過 code block 裡的內容）。
- `source`：可省略。決定要同步寫回的檔案（例如記憶檔），避免兩邊說法不一致。
- 決定後加上 `decision:`（決定內容）與 `decided:`（日期），跳過時加 `skipped:`（日期）。
- 編號 `T-xxx` 只增不重用；新增時取現有最大號加一。

## 模式一：review（不帶參數）

1. 讀清單。檔案不存在就建一個只有 `# 待辦清單` 標題的檔，告訴使用者目前沒有項目，然後繼續處理使用者原本的要求。
2. 篩出 `status: open`，且 `project` 是 `*`、等於目前工作目錄、或是目前工作目錄的上層資料夾的項目。比對路徑時不分大小寫，`/` 和 `\` 視為相同，去掉結尾斜線。沒有符合的項目就說一行「沒有待決定的項目」，然後繼續處理使用者原本的要求。
3. 先用一個短表列出這次要問的項目：編號、標題、類型（有選項／待輸入）。
4. 用 `AskUserQuestion` 問，一次最多 4 題，照清單順序分批。每題：
   - `header`：項目編號（例如 `T-003`，不超過 12 字）。
   - `question`：自成一句，包含標題與一句背景，因為使用者可能只看到對話框。
   - `multiSelect: false`。
   - **有選項的項目**：每個選項都要有 `label`（簡短，最多約 5 個詞）與 `description`（一句說明）。清單的選項行是「短標題：說明」時，冒號前當 label、冒號後當 description；沒有冒號時，label 取簡短版本，description 放完整原文。建議的選項放第一個，去掉清單裡的「（建議）」，改在 label 結尾加「(Recommended)」。最後一個選項一律是「先跳過」（description：下次開啟再問），所以清單選項最多放 3 個；清單有 4 個以上選項時，放前 3 個，其餘選項逐條寫進 question 文字，請使用者用 Other 輸入。
   - 使用者關掉或取消對話框，視同這一批全部「先跳過」。
   - **待輸入的項目**：question 結尾寫「請選 Other，輸入你要怎麼繼續。」選項固定兩個：「先跳過」（下次開啟再問）、「取消這項」（標為 dropped）。
   - 不要自己加名為 Other 的選項，工具會自動提供自由輸入。
5. 每批回答後**先寫回清單，再做別的事**：
   - 選了某個選項，或用 Other 輸入了明確的做法 → `status: decided`，`decision:` 寫使用者的選擇或原文，`decided:` 寫今天日期。
   - 「先跳過」，或任何意思是「下次再問我」的選擇或輸入 → 保持 `open`，加或更新 `skipped:`（`decided` 的項目不會再被問，所以「之後再決定」不能標成 `decided`）。
   - 「取消這項」→ `status: dropped`，`decided:` 寫今天日期。
   - Other 的內容是問題或看不懂 → 保持 `open`，在對話裡回答或追問，有結論再寫回。
   - 有 `source:` 的項目，把決定用一句話同步寫進那個檔案。
6. 全部問完後，用一段話加一個短表回報：哪些已決定、哪些跳過、哪些取消。
7. 執行決定：只處理**這次 review 剛決定**的項目（以前 session 留下的 `decided` 項目只在回報中列出，使用者要求才做）。屬於目前專案、而且現在就能做的，依序去做，照使用者的 CLAUDE.md 規則處理需要同意的步驟。做完把 `status` 改成 `done`。決定內容是「等使用者做某事」或「之後再做」的，保持 `decided`，在回報中說明下一步是誰的事。屬於其他專案的項目只記錄，不在這裡做。
8. 如果使用者的第一則訊息本來就有別的任務，review 結束後接著做那個任務。
9. 沒有 `AskUserQuestion` 可用（例如 `claude -p` 非互動模式）時，不做 review，只用一行說明有幾項待決定，然後繼續原本的任務。

## 模式二：add（`/todo-review add <描述>`）

1. 從描述與目前對話整理出標題、一句背景，以及已知的選項。選項是使用者或對話中真的提過的做法，不要自己編。沒有就不寫 `options`。
2. `project` 預設是目前工作目錄；使用者說「全部專案」才用 `*`。
3. 寫入清單，回報新項目的編號與內容。

## 模式三：list

列出目前專案的 `open` 與 `decided` 項目（短表：編號、標題、狀態、決定），不問問題，不改檔。

## 維護

清單中 `done` 與 `dropped` 的項目超過 20 個時，把它們搬到 `~/.claude/todo-archive.md` 結尾，清單只留 `open` 與 `decided`。
