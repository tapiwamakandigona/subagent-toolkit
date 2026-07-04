# Replan

Template for re-planning when the current plan has failed — a phase blew its cycle cap, a fan-out partition collapsed, or reality falsified the plan's assumptions. A good replan is an audit plus a new plan: it separates what is verified and kept from what is sunk, names the assumptions that failed verbatim, and re-partitions the remaining work without relitigating the sound parts.

## Usage notes

- Replanning is the common case in long projects, not the edge case. Triggers: three plan amendments (`plan-then-execute.md`), a phase failing its cycle cap (`phase-chain.md`), two no-progress iterations, or a falsified load-bearing assumption.
- Sunk cost accounting is there to *prevent* sunk-cost reasoning: work is kept because it's verified and still needed, never because it was expensive.
- Carry contracts forward verbatim. Interfaces, acceptance criteria, and constraints that survive the replan are copied word-for-word into the new plan — paraphrasing during a replan is how requirements quietly change.
- Write the replan into the run's trace and checkpoint before executing it; a replan that lives only in context dies with the context.

## Template

```text
REPLAN: {{run_id}} — round {{n}}
Trigger: {{what_failed — cycle cap, falsified assumption, no-progress halt; cite evidence}}

1. VERIFIED & KEPT
   {{artifact_or_result}} — verified by {{check}}; still needed because {{reason}}
   {{one line each; anything not listed here is NOT assumed good}}

2. SUNK
   {{work_discarded}} — cost {{rough_effort}}; discarded because {{reason}}
   {{kept ≠ cheap, sunk ≠ wasted-feelings: the only test is "verified and still needed"}}

3. FAILED ASSUMPTIONS (verbatim)
   "{{the_assumption_as_originally_written}}" — falsified by {{observation/evidence}}
   {{quote the original wording; paraphrased failures hide what actually broke}}

4. NEW PLAN
   {{numbered steps or a fresh phase-chain/task-list, sized per harness/patterns.md;
   each step states its owner, its auto-verify check, and which kept artifacts it builds on}}

5. CARRY-FORWARD CONTRACTS (verbatim)
   {{interfaces, acceptance criteria, constraints copied word-for-word from the
   spec/architecture — these did NOT change; the plan changed}}

6. WHAT CHANGES FOR IN-FLIGHT AGENTS
   {{who gets re-briefed, who gets stopped, who is unaffected}}
```

## Anti-patterns

- **Replan as retry** — re-running the same plan with hope is not a replan; something in sections 2–3 must explain why this time differs.
- **Keeping by default** — unverified prior work carried into the new plan imports the old failure; if it isn't in section 1 with a check, rebuild or re-verify it.
- **Paraphrased contracts** — the replan is exactly when requirement drift sneaks in; sections 3 and 5 quote, never summarize.
- **Silent replans** — downstream agents building on a plan that no longer exists; section 6 is mandatory.
