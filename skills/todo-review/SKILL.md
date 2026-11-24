---
name: todo-review
description: Reads the current project's own to-do list in ~/.agents/todo/ and asks the user, one item at a time, about its open decisions. Items with options become a multiple-choice question; items without options ask the user to type how to continue. Writes each decision back to the list. Use when a session-start reminder asks for it, when the user says "review todo", "show my to-dos" or "看待辦", or types /todo-review. Also adds items (/todo-review add ...) and lists them (/todo-review list).
argument-hint: "[add <description> | list] (no argument = review one by one)"
---

# To-do review

Each project has its own to-do list. The lists are in the folder `~/.agents/todo/`, one file per project. They stay on the local computer, outside every project folder, so they never go into a git repo.

Work only with the current project's list. Never read, mention or count another project's list.

`todo-reminder.ps1` in this folder is a SessionStart hook. At session start it counts the `open` items in the current project's list and, if there are any, asks the agent to run this skill. It reads the `project:` line and the `status:` fields, so do not rename or reformat them.

Talk to the user in the language they use. Field names in the list stay in English. Field values are in the user's language.

## Find the current project's list

1. Each file in `~/.agents/todo/` starts with a title line and a `project:` line, for example:

   ```markdown
   # To-do list
   project: D:\Projects\example
   ```

2. The current project's list is the file whose `project:` is the current working folder or a parent folder of it. Compare paths without case, treat `/` and `\` as the same, and ignore a trailing slash. If more than one file matches, use the one with the longest `project:` path.
3. If no file matches, the project root is the top folder of the git repo that holds the working folder (`git rev-parse --show-toplevel`), or the working folder itself when it is not in a git repo. Make a new file only when you must write an item. Name it after the project root: replace every character that is not a letter, a digit, `.`, `_` or `-` with `-` (for example `D:\Projects\example` becomes `D--Projects-example.md`).

## List format

Each item is an H2 section. Example:

```markdown
## T-007 Import the example project's data now?
- added: 2026-01-15
- status: open
- context: 3 files are downloaded to the inbox and wait to move into the main folder.
- options:
  - Import now (recommended)
  - I move them myself: tell me when done, then import
  - Skip this batch
- source: ~/notes/example-import-plan.md
```

- `status`: `open` (waits for a decision), `decided` (decided, work still to do), `done` (finished) or `dropped` (cancelled). Only `open` items are asked.
- `options`: optional. An item with options is a "choice item"; an item without options is an "input item". Write one option per line. If an option needs an explanation, write it as "short title: explanation". Put the recommended option first and end it with `(recommended)`. Treat the older marker `（建議）` the same way.
- `source`: optional. A file that must also receive the decision (for example a notes or memory file), so the two never disagree.
- After a decision, add `decision:` (what was decided) and `decided:` (the date). When an item is skipped, add `skipped:` (the date).
- Item numbers `T-xxx` count per list. They only go up and are never reused. A new item takes the highest number in this list plus one.
- Do not put code blocks in a list file. `todo-reminder.ps1` ignores everything inside code blocks.

## Asking questions

Use the multiple-choice question tool of your agent tool: `AskUserQuestion` in Claude Code, `ask_user` in Gemini CLI. If no such tool is available, ask the same questions as numbered plain text in the chat, list each option with its letter, and wait for the reply. In a non-interactive run (for example `claude -p`), do not review. Say in one line how many items wait for a decision, then continue with the original task.

## Mode 1: review (no argument)

1. Find the current project's list. If there is none, say in one line that there are no items, and continue with the user's original request.
2. Select the items with `status: open`. If there are none, say in one line that there is nothing to decide, and continue with the original request.
3. First show a short table of the items you will ask about: number, title, type (choice or input).
4. Ask at most 4 questions at a time, in list order, single choice.
   - The header is the item number (for example `T-003`, at most 12 characters).
   - Each question must stand on its own: include the title and one sentence of context, because the user may see only the question.
   - Each option has a short label (at most about 5 words) and a one-sentence description.
   - **Choice item**: if an option line has a colon, the text before it is the label and the text after it is the description. Without a colon, use a short version as the label and the full text as the description. Put the recommended option first, remove its `(recommended)` or `（建議）` marker, and mark it the way your tool marks a recommendation (in Claude Code, end the label with "(Recommended)"). The last option is always "Skip for now" (description: ask again next session), so use at most 3 options from the list. If the list has 4 or more options, use the first 3 and write the rest in the question, and ask the user to type their choice as a free-text answer.
   - **Input item**: end the question with "Type how you want to continue." Give two fixed options: "Skip for now" (ask again next session) and "Drop this item" (mark it dropped).
   - Write these fixed labels in the user's language.
   - Do not add an option named "Other" yourself. Claude Code adds a free-text answer automatically. If your tool has no free-text answer, tell the user they can reply in the chat instead.
   - If the user closes or cancels the question, treat every item in that batch as "Skip for now".
5. After each batch, **write the answers back to the list before you do anything else**:

   | Answer | Write back |
   |---|---|
   | An option, or a clear plan typed as free text | `status: decided`, `decision:` with the choice or the user's words, `decided:` with today's date |
   | "Skip for now", or anything that means "ask me later" | Keep `open` and add or update `skipped:`. Never mark it `decided`, because `decided` items are not asked again |
   | "Drop this item" | `status: dropped`, `decided:` with today's date |
   | Free text that is a question or unclear | Keep `open`. Answer or ask back in the chat, and write back once there is a conclusion |

   For an item with `source:`, also write the decision into that file in one sentence.
6. When all batches are done, report in one paragraph and a short table: which items are decided, skipped and dropped.
7. Carry out the decisions. Act only on items **decided in this review**. Items left `decided` by earlier sessions are only listed in the report; act on them only if the user asks.
   - Items that can be done now: do them in order. Follow the user's own instructions (for example CLAUDE.md, AGENTS.md or GEMINI.md) for steps that need approval. When done, set `status` to `done`.
   - Items whose decision is "wait for the user to do something" or "do it later": keep `decided`, and say in the report whose move it is next.
8. If the user's first message had another task, do that task after the review.

## Mode 2: add (`add <description>`)

1. From the description and the current conversation, write a title, one sentence of context, and the known options. Use only options that the user or the conversation actually mentioned. Do not invent options. If there are none, leave out `options`.
2. Write the item to the current project's list. Make the list first if there is none (see "Find the current project's list").
3. Report the item's number and content.

## Mode 3: list

Show the `open` and `decided` items of the current project's list in a short table: number, title, status, decision. Ask no questions and change no files.

## Maintenance

When a list has more than 20 `done` and `dropped` items, move them to the end of a file with the same name in `~/.agents/todo/archive/`. Keep only `open` and `decided` items in the list.

## Older single list

Older versions kept every project in one file, `~/.agents/todo.md`, with a `project:` field on each item. If that file exists and has items whose `project:` is the current project, copy them into the current project's list, keep their numbers, and remove their `project:` field. Then remove those items from the old file. Do this silently, except for one line that says how many items moved. Never delete the old file itself: when it has no items left, say once that the user can delete it.
