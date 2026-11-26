---
name: reframe
description: "Gets the problem right before work starts. Reads the source material, resolves ambiguous readings, collects key terms and lessons from nearby fields, fills in missing constraints, and rewrites the request. Builds nothing. Use only when the user types /reframe. Run it before /sharpen."
---

# Reframe

Get the concepts and the wording of a request right before anyone acts on it. The output is a rewritten request that uses the right terms and asks the right questions, so that the user, or an agent after them, starts from a correct problem.

This skill only makes the problem clear. It does not build anything, and it does not go deep into the method. The method and the acceptance checks are the work of /sharpen.

The request is the argument, or, without one, the user's latest request in this conversation. Talk to the user in the language they use.

## Steps

### 1. Read the source material

- Open the original files, code, links and request text that the user gave, and read them word for word.
- Do not judge the problem from a summary, a paraphrase or your own earlier recap in this conversation.
- If material is missing, say what is missing and which judgment it affects.

### 2. Resolve ambiguity

If one sentence of the request can be read in several ways, list 2 or 3 readings. For each reading, write:

- **Name**: what this kind of problem is usually called in industry or research.
- **Meaning**: what the finished work looks like under this reading.
- **Signals**: which signs in the material support or rule out this reading.

Then choose one reading and say which signals it rests on. If the signals are too weak and a wrong choice is costly, stop and ask the user. Do not force a choice. If the request has no ambiguity, say so in one sentence and skip this step.

### 3. Key terms (8 to 12)

Sort the terms by how much each one changes the finished work, the largest first. For each term, give:

- **Meaning**: one or two sentences.
- **Part of the request**: which part of the request it applies to.
- **Source**: a link to one real project, paper or official document that uses the term in this meaning.
- **How to ask with it**: one example sentence that can go straight into a prompt, to show how to instruct an agent once you know the term.

### 4. Lessons from nearby fields (2 or 3)

For each field, write:

- **What you can use directly**: a practice that carries over as it is.
- **Where the analogy fails**: how the two fields differ, and what goes wrong if you copy the practice without change.

### 5. Fill in missing constraints

List the conditions that the user can easily leave out but that change the finished work. Examples: scale, runtime environment, compatibility, performance, security and privacy, audience, delivery format, time and budget, and what counts as success. Mark each one as **stated** (written in the material) or **inferred** (your guess).

### 6. Rewrite the request

Write a version that can go straight to an agent. Use the terms from step 3, and include the chosen reading and the constraints. Mark the inferred parts, so that the user can confirm them.

### 7. Check every source (required before you send)

- Open each link. Make sure that the page exists and uses the term in the meaning you gave.
- Delete each source that you cannot check or that does not match. Do not replace it with a link from memory. If a term has no reliable source, write "no checked source".
- The final message must not contain any link that you did not open and check.

## Message format

Use these parts, in this order, with short headings:

1. **Material read**: a list.
2. **Readings and choice**.
3. **Key terms**: a table, sorted by impact.
4. **Lessons from nearby fields**.
5. **Constraints**: each marked stated or inferred.
6. **Rewritten request**.
7. **Next step**: suggest running /sharpen next.

## Do not

- Do not start building, and do not write code.
- Do not run experiments to choose a technology, and do not set acceptance checks. That is the work of /sharpen.
- Do not use a second-hand summary in place of the original text.
