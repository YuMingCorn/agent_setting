---
name: wrap-up
description: Ends a work session. Checks unchecked code changes, commits this session's work, and gives a short recap that lists unfinished work. Pushes or opens a pull request only when the user asks for it in the same request. Use when the user types /wrap-up or says "wrap up", "收工", "結束今天的工作" or "commit 然後收工".
argument-hint: "[push | pr] [notes for the recap]"
---

# Wrap up

Close the session so that the work is saved, nothing is lost, and a reader who sees only the recap knows where things stand.

Talk to the user in the language they use. The project's own instructions (CLAUDE.md, AGENTS.md or GEMINI.md) win over this skill when they disagree, for example "never push" or a commit message format.

## What may leave this computer

- **Default: nothing.** Commit locally only.
- **Push** only when the user asks for it in this request: the argument `push` or `pr`, or their own words such as "push", "推上去" or "開 PR". This request is then the go-ahead for a normal push of the current branch to its existing remote. Exception: `pr` alone on the default branch is not a go-ahead to push (see step 4).
- **Never** force-push, merge, delete a branch, create a repository, or change a repository's visibility here. If one of these seems needed, say so in the recap.

## Steps

1. **See the state.** Run `git status`, `git diff --stat` and `git log --oneline -5`. Note the current branch, its upstream, and commits that are not pushed. If the folder is not in a git repo, skip the git steps and say so in the recap.

2. **Check the work.** If this session changed code, scripts or config and no check has run on the final version, have the `sonnet-checker` agent check it against what the user asked for in this session. Give it the request, the changed files and how to test them. Skip the check for changes to notes and documents only, and when a check already passed on the final version.
   - On FAIL: fix the real problems and check again. If a fix needs the user's decision, do not commit the broken part. List it as a leftover in the recap.

3. **Commit.**
   - Stage only the files that this session's work changed. Name them one by one; do not use `git add -A` or `git add .`.
   - Leave out files that look like secrets (`.env`, keys, tokens, credentials) and files that the user changed for something else. List them in the recap.
   - Write the message in the project's style: follow its instructions first, then the style of the recent commits. Say what changed and why. Add the attribution lines that the user's or the tool's instructions ask for.
   - Make one commit per separate piece of work when the session did unrelated things; otherwise make one commit.
   - Do not commit when nothing changed.

4. **Push (only when asked).**
   - Branch with an upstream: `git push`.
   - Branch with no upstream: `git push -u origin <branch>`.
   - `pr` on a branch that is not the default branch: push, then open a pull request if none exists for the branch (`gh pr create`). The body says what changed and why, and how it was checked. If a pull request already exists, push only and give its link.
   - `pr` on the default branch: do not create a branch on your own. Push if the user also said push; otherwise say in the recap that a pull request needs a branch.
   - If the push is refused, stop. Report the error and do not try other ways.

5. **Recap.** End with one short message that stands on its own, in this order:
   - what was done in this session (at most 5 points),
   - the check result (PASS, FAIL or skipped, and why),
   - the commit hash and message, and where it went (local only, pushed to which branch, or the pull request link),
   - the leftovers: work that is decided but not done, and decisions that wait for the user (in the recap only; do not write them to a to-do list),
   - files left out of the commit, and why,
   - the next step, in one sentence.

   Use plain words. Do not use terms or abbreviations made up during the session. If the user gave notes in the argument, put them in the recap.
