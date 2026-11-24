---
name: first-principle
description: "Solves a problem by first-principles thinking. Takes the problem apart down to its basic axioms (facts that cannot be reduced further), then reasons up from those axioms alone to build the solution, instead of copying how it is usually done. Use when the user types /first-principle, or says \"第一原理\", \"第一性原理\", \"從根本想\", \"拆到最基本\", \"first principles\" or \"reason from first principles\"."
---

# First principle

First-principles thinking takes a complex problem apart down to its basic **axioms**, then reasons up again from those axioms alone to build the solution. The opposite is **reasoning by analogy**: "others do it this way, so we do too." Analogy is fast, but it carries old assumptions in with it. This skill finds those assumptions, keeps only the ones that are true, and rebuilds from there.

The problem is the argument, or, without one, the user's latest request in this conversation. Talk to the user in the language they use.

## Steps

1. **State the goal, not the solution.** Write in one or two sentences the end state the user needs: what is true when the problem is solved. Remove any method from that sentence. "We need a faster database" names a method. "Each page must load in under 1 second" names a goal. Done when the goal sentence contains no method.

2. **List every assumption.** Write down everything the current way of thinking takes for granted: the usual solution, its costs, the limits people quote, "it has to be like this", and the analogies in play. Include the assumptions hidden in the user's request. Done when each part of the usual solution traces to at least one listed assumption.

3. **Reduce each assumption to axioms.** For each assumption, ask "why is this true?" and repeat the question on each answer until it can go no further. Then sort it into one of three kinds:
   - **Axiom**: a fact that holds no matter what anyone prefers. Examples: physics, math, a guarantee of the language or platform, a measured number, a hard limit the user set.
   - **Convention**: true only because people chose it, such as habit, tradition, an industry standard, or "we always did it this way". You can change it.
   - **Unverified belief**: it may be true, but no one has checked.

   Check facts by looking, not from memory: read the code, run the command, measure, or find the primary source. If an unverified belief decides the result and you cannot check it, mark it as an open question for the user. Done when every assumption has a kind, and every axiom names its source.

4. **Rebuild from the axioms alone.** Set aside the conventions and the usual solution. Ask: "Given only these axioms, what is the simplest way to reach the goal?" Write each solution as a chain: axiom → inference → solution, one link per line, so that the user can check every step. Build at least one solution that analogy would not reach. If the rebuilt solution ends up the same as the usual one, that is a valid result: say that the usual solution holds up and why.

5. **Test the result against reality.** Compare the rebuilt solution with the usual one. For each convention you dropped, say what it gave people and what you risk by dropping it. Sometimes a convention exists for a reason you did not see; then add that reason back as an axiom and repeat step 4. Done when each difference from the usual solution has its reason and its risk.

## Message format

Use these parts, in this order, with short headings:

1. **Goal**: the goal sentence from step 1.
2. **Assumptions and axioms**: a table with columns for the assumption, its kind (axiom, convention or unverified belief), and the source or reason.
3. **Rebuilt solution**: the reasoning chain from step 4, then the solution in plain words.
4. **Versus the usual way**: what changed, why, and the risk of each change.
5. **Open questions**: the unverified beliefs that could change the result, each with your default guess. Leave this part out if there are none.

Lead with the conclusion: a reader who stops after part 3 must still know what to do. If the user asked you to carry out the task, not only to think it through, start the work after the message, based on the rebuilt solution. Steps that need approval under the user's or project's own instructions still need it.
