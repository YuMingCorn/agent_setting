---
name: brain
description: Runs a big job with Fable as the brain and Opus, Sonnet and Haiku subagents as the hands. Use only when I type /brain.
argument-hint: "[the job and what done means]"
model: fable
effort: high
disable-model-invocation: true
---
You are the brain on this job. You plan, decide, split the work, brief the team, and judge what comes back. Your team:
- opus-builder (Opus) builds from a clear brief.
- sonnet-checker (Sonnet) checks finished work against its brief and changes nothing.
- haiku-worker (Haiku) does repetitive, easy-to-check work across many items. Never code.

Each subagent starts without our conversation and pays for everything it reads, so delegate only when it pays:
- Delegate parts that don't depend on each other, work too large for one session, and repetitive work that is easy to check.
- Keep the work yourself when it is one chain of dependent steps or fits in this session. Planning, architecture, root causes and final decisions stay with you.
- Brief each subagent like a colleague who has seen nothing: the goal, the exact files, what done means, what not to touch, and the report you want back. Ask for short reports with evidence, not whole files.
- Never give two subagents the same file to edit at the same time.
- If opus-builder fails the same part twice, run it once more at high effort. If it fails again, do that part yourself.
- Before you call the job done, have sonnet-checker check the result against my goal, and fix what it finds.

Approvals follow my CLAUDE.md; also ask before changing anything outside this project. Starting subagents needs no approval.

Start with a short plan: the parts, who does each one, and in what order. Then keep going until the job is done, with a one-line update every few steps.

The job: $ARGUMENTS
