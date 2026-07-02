# Plan Then Execute

Template that forces an agent to commit to a written plan before touching anything. Use for tasks with irreversible steps, multiple valid approaches, or >30 minutes of work — planning failures caught at step 0 cost one message; caught at step 7 they cost the run.

## Usage notes

- The plan is a **contract**: deviations during execution must be logged, not silently absorbed.
- For risky work, insert a checkpoint after the plan: the agent posts the plan and waits for approval before executing (`{{checkpoint_mode}}` = "wait for approval" vs. "proceed immediately").
- Keep plans short — 5–9 steps. A 25-step plan is a decomposition failure; delegate instead.

## Template

```text
Task: {{task_description}}

Work in two phases. Do NOT begin Phase 2 until Phase 1 is written out in full.

PHASE 1 — PLAN (no side effects: no file edits, no state changes)
1. Restate the goal and definition of done in your own words.
2. List what you must inspect first (files, docs, existing behavior) and inspect it.
3. Produce a numbered plan of 5–9 steps. For each step:
   - action and expected outcome
   - how you'll verify the step worked
   - mark it [REVERSIBLE] or [IRREVERSIBLE]
4. List the top 2–3 risks and what you'll do if each materializes.
5. State the fallback: what you'll deliver if the primary approach fails at
   the halfway point.

Checkpoint: {{checkpoint_mode}}.

PHASE 2 — EXECUTE
- Follow the plan step by step, verifying each step before the next.
- Before any [IRREVERSIBLE] step, re-check its preconditions explicitly.
- If reality diverges from the plan, stop, write a one-line plan amendment
  (what changed and why), then continue. Three amendments = replan from scratch.
- Finish with a report per {{abilities_dir}}/prompts/handoff-report.md, including
  the final plan with per-step outcomes (done / amended / skipped-because).
```

## Anti-patterns

- **Plan theater** — writing a plan, then executing something else without amendments.
- **Verification postponed to the end** — per-step checks exist to localize failures.
- **Planning what's already known** — if the task is truly mechanical, skip this template; plans have a cost too.
