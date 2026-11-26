---
name: restate
description: Before any work starts, restates in the agent's own words what the user's goal is, what problem they are trying to solve, and what is still unclear, then stops and waits for the user's reply. Use only when the user types /restate.
argument-hint: "[the task to restate; default: the user's latest request]"
disable-model-invocation: true
---

# Restate

Show the user how you understood the request, so that a wrong reading is caught before any work is done on it. The user reads your restatement and corrects it. The value is in what they correct, so make your reading easy to check, not impressive.

The task to restate is the argument, or, without one, the user's latest request in this conversation. Talk to the user in the language they use.

## This turn is read-only

This turn ends with your questions. Its only output is the message described below. You may look at the environment to ground your reading: read files, search, list folders, and run read-only commands such as `git status` or `git log`. Keep it to the few lookups that make the restatement concrete. Leave all creating, editing, deleting, installing and sending for after the user replies.

## Steps

1. **Read the request closely.** Note the exact words the user used, what they asked for, and what they did not say.
2. **Look around, briefly.** If the request names a project, file, tool or earlier work, look at it so that your restatement rests on facts. Stop when you can describe the current state in one or two sentences.
3. **Separate three things.** Most bad starts mix them up:
   - **Goal**: the end state the user wants. What is true when they are satisfied?
   - **Problem**: what goes wrong today, and for whom. Why does the user want this now?
   - **Request**: the thing they asked you to make or do. Check it against the goal: it can be an XY problem, where the user asks for their guessed solution (Y) instead of the real need (X). If the request may not reach the goal, say so in one sentence.
4. **Write the message** in the format below. Every sentence must say something specific to this request. A sentence that would fit any task tells the user nothing.
5. **Stop.** Send the message and wait. Do not add a plan, a first draft or an offer to start.

## Message format

Use these four parts, in this order, with short headings:

1. **Your goal, as I understand it.** Two to four sentences in plain words. Do not copy the user's sentence back; say it in different words, so that a misreading shows.
2. **The problem you want to solve.** One to three sentences: the current pain and what it costs the user.
3. **What I assumed.** Each guess you made to fill a gap, one per line, so that the user can correct each one separately. Mark what came from their words and what you inferred. If you looked at files or the project, say in one line what you found.
4. **What I need from you.** Numbered questions, the most important first. Ask only questions whose answer changes what you would do. For each one, give your default answer in a few words, so that the user can reply "the defaults are fine". Name the one question that matters most.

Keep the whole message short enough to read in under a minute. When the request is already clear and you have no real question, say that, give the restatement, and ask the user to confirm it.

## After the user replies

- If the reply changes your reading, restate the corrected goal in one or two sentences.
- If a question that changes the work is still open, ask only that question.
- Otherwise start the task. The user's answers are the go-ahead to start, unless they say to wait. Steps that need approval under the user's or project's own instructions still need it.
