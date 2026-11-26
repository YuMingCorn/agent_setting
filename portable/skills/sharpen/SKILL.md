---
name: sharpen
description: "Raises how a task is done to the standard of the best people in its field. Finds the primary sources, picks the method, tests technical choices with small experiments, leaves product trade-offs to the user, sets acceptance checks that rest on outside evidence, and rewrites the prompt. Use only when the user types /sharpen. Usually runs after /reframe."
---

# Sharpen

Once the problem is clearly defined, usually by /reframe, raise the task to the level of the best people in the field. Deliver a deeper prompt with a clear method and clear acceptance checks.

If the problem still has ambiguous readings or unclear terms, suggest that the user run /reframe first.

The request is the argument. Without one, use the latest /reframe output in this conversation, or else the user's latest request. Talk to the user in the language they use.

## Steps

### 1. Read the source material

Open the original files, code and request text, and the /reframe output if there is one. Do not judge from a summary.

### 2. What the best people do in addition

Compare the usual way with the way the best people in the field work, and list the gaps. For each extra step, say which failure it prevents or which quality it raises.

### 3. Primary sources to start from

Name the primary sources that the work must rest on, with links. Examples: specifications, standards, raw data, source code, papers, official documentation and real user data. Before you send the message, open each link and check it. Delete each one that you cannot check.

### 4. Method

Describe the specific method or process, and say why it fits this task.

### 5. Sort the decisions into two kinds

- **A. Technical choices that a small experiment can settle.** First build the smallest prototype or run an experiment, and look at the real result. Then recommend. Write what you tried, how you measured it, what the result was, and what you recommend because of it. Do not decide without an experiment.
- **B. Product trade-offs or personal preferences that no experiment can settle.** List the options, the trade-offs of each, and when each one fits. **Leave the choice to the user.** Do not choose for them.

Mark each decision as A or B.

### 6. Acceptance checks from outside evidence

Define how the finished work is accepted. The evidence must come from outside, not from your own review. Examples: automated tests, benchmarks, comparison with reference data or an existing system, checks by third-party tools, and real user behavior. For each check, state the pass condition.

### 7. Rewrite the prompt

Combine the steps above into a prompt that an agent can run as it is. It covers the goal, the primary sources, the method, the steps, the A decisions already made, the B decisions that wait for the user, and the acceptance checks.

## Message format

Use these parts, in this order, with short headings:

1. **Material read**.
2. **Best practice versus the usual way**.
3. **Primary sources**: checked.
4. **Method**.
5. **Decisions**: A (experiment, result and recommendation) and B (options that wait for the user).
6. **Acceptance checks**: the outside evidence and the pass condition of each.
7. **Rewritten prompt**.

## Do not

- Do not make B decisions for the user.
- Do not accept work because it "looks fine".
- Do not keep a source that you did not check.
