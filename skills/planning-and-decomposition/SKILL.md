---
name: planning-and-decomposition
description: Converts a fuzzy objective into a staged, executable plan. Covers clarifying the definition of done, structuring a todo list, ordering work by dependencies, placing milestone checkpoints, and recognizing when to replan versus push through. Use at the start of any multi-step task, and again whenever reality diverges from the plan.
license: MIT
metadata:
  version: "2.0.0"
---

# Planning & Decomposition

Agents fail on long tasks in two symmetric ways: **no plan** (wandering, redundant work, forgotten requirements) and **frozen plan** (executing a stale plan long after evidence says it's wrong). This skill fixes both.

## 1. Pin down "done" before planning

Write one sentence: *"This task is done when ___, verified by ___."* If you can't fill both blanks, the objective is ambiguous — resolve it first (ask, or state your interpretation explicitly and proceed). Everything in the plan must trace back to this sentence; anything that doesn't is scope creep.

Also capture **constraints** (deadline, budget, tools available, things you must not touch) and **assumptions** you're making. Assumptions are future replanning triggers.

## 2. Decompose into verifiable steps

Rules for good decomposition:

- **Each step has an observable output** — a file, a passing test, a decision recorded. "Understand the codebase" is not a step; "write a 10-line summary of the request flow in notes.md" is.
- **Right granularity:** one focused tool-session producing one verifiable artifact per step (roughly 5–30 minutes of human-equivalent work). Finer wastes overhead; coarser hides being stuck.
- **Front-load risk:** do the step most likely to invalidate the whole approach *first* (the unknown API, the data that might not exist, the permission you might not have). Cheap discovery beats expensive rework.
- **Separate discovery from execution.** If you don't know enough to plan phase 2, make "investigate X, then replan" a step — don't fabricate detailed steps you'll ignore.

## 3. Order by dependencies

- Sketch the dependency graph mentally (or literally, for big tasks). Identify the **critical path** — the chain of steps that gates completion.
- Steps not on the critical path get scheduled opportunistically or dropped when time runs short.
- Flag steps that are **irreversible or externally visible** (sending, deploying, deleting, publishing). These always come last within their phase and get an explicit pre-check.

## 4. Todo structure

Maintain the plan as a living checklist in your working notes:

```markdown
## Goal
Done when: <definition of done>. Verified by: <verification>.

## Plan
- [x] 1. Reproduce the bug locally — output: failing test `test_auth_expiry`
- [x] 2. Locate cause — output: note pointing at `session.py:142`
- [ ] 3. Fix + make test pass          ← current
- [ ] 4. Run full test suite (checkpoint A)
- [ ] 5. Write summary of change
Risks/assumptions: assumes bug is server-side; if not, replan after step 2.
```

Conventions: exactly one step is "current"; completed steps record their actual output; the risk list lives with the plan. Update the checklist **as you go**, not retroactively — it's your external memory and your recovery point if context is lost.

## 5. Milestone checkpoints

Insert an explicit checkpoint every 3–5 steps or at phase boundaries. At a checkpoint, spend 60 seconds answering:

1. Does completed work still serve the definition of done?
2. Have any assumptions been falsified?
3. Is the remaining plan still the cheapest path — or has what I learned revealed a shortcut?
4. Budget check: am I on pace? If not, what gets cut? (Cut scope, not verification.)

## 6. Replanning triggers

Replan — don't push through — when any of these fires:

- **Assumption broken:** something the plan relied on turned out false.
- **Two consecutive failures** on the same step with different approaches. A third identical attempt is almost never the answer; change strategy or escalate.
- **Scope discovery:** the task is 3×+ larger than planned. Report and re-scope rather than silently delivering a fraction.
- **New information dominates:** you found an existing solution / library / prior work that makes phases obsolete.
- **Sunk-cost check:** if you were starting fresh knowing what you know now, would you follow the current plan? If no, replan.

Replanning is cheap: edit the checklist, note *why* it changed (one line), continue. The "why" line prevents oscillating back to an abandoned approach.

## 7. Anti-patterns

- **The 40-step waterfall:** detailed plans for phases you don't understand yet. Plan the next phase in detail, later phases as sketches.
- **Plan-as-theater:** writing a plan and never reading it again. If the checklist doesn't drive your next action, it's dead weight.
- **Verification as final step only:** verification belongs inside steps (each has an observable output), not just at the end.
- **Silent scope changes:** any change to the definition of done must be surfaced, not just absorbed.
