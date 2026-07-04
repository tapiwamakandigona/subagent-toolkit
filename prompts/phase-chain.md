# Phase Chain

A declarative pipeline spec the orchestrator executes mechanically: phases in order, two roles per phase (one demanding, one producing), a required input and output artifact each, a cycle cap, and a gate. Declaring the chain up front prevents the two classic drifts — skipped verification under time pressure, and unbounded polish loops.

## Usage notes

- Each phase names an **instructor** role (states the demand, judges the output against the gate) and a **worker** role (produces the artifact). Checkable ownership: every artifact has exactly one producer and one judge.
- **Max cycles** bounds the instructor↔worker improve-loop within the phase (default 3 — see loop guards in `../harness/patterns.md`). Cap reached with the gate unmet → the phase fails; replan with `replan.md` instead of iterating past the cap.
- `[HUMAN GATE]` marks phases whose gate a human must approve before the chain continues. Defaults for full projects (spec approval, destructive ops, release) are in `../harness/project-lifecycle.md`.
- Artifact shapes come from `artifacts/` (spec, architecture, task-list, checkpoint); the orchestrator writes a checkpoint at every phase boundary.

## Template

```text
PHASE CHAIN: {{project_or_run_name}}   RUN_ID: {{run_id}}

| # | Phase | Instructor | Worker | Input artifact | Output artifact | Max cycles | Gate |
|---|-------|-----------|--------|----------------|-----------------|-----------|------|
| 1 | {{phase}} | {{role}} | {{role}} | {{path_or_dash}} | {{path}} | {{n}} | {{gate_criterion}} {{[HUMAN GATE] if applicable}} |
| 2 | {{...}} | | | | | | |

Loop rows {{i}}–{{j}} per {{milestone|item}}, up to {{k}} iterations.

Execution rules:
- Run phases strictly in order; a phase starts only when its input artifact exists and the prior gate passed.
- Instructor briefs the worker per prompts/task-briefing.md; worker reports per prompts/handoff-report.md.
- Gate unmet after max cycles → phase FAILED: write a checkpoint, then replan (prompts/replan.md) or escalate.
- Checkpoint (prompts/artifacts/checkpoint.md) after every phase, pass or fail.
```

### Example (filled, abbreviated)

```text
| # | Phase | Instructor | Worker | Input | Output | Cycles | Gate |
|---|-------|-----------|--------|-------|--------|--------|------|
| 1 | Spec | orchestrator | product-manager | idea.md | spec.md | 2 | every FR has a checkable criterion [HUMAN GATE] |
| 2 | Architecture | orchestrator | architect | spec.md | architecture.md | 2 | every FR mapped to a module; contracts verbatim |
| 3 | Build M1 | orchestrator | code-worker | task-list.md | code on branch | 3 | task auto-verify commands pass |
| 4 | QA M1 | orchestrator | qa-engineer | spec.md + branch | test suite + defect log | 3 | all M1 acceptance criteria pass E2E |
| 5 | Integrate M1 | orchestrator | integrator | branches | green mainline | 2 | full suite green post-merge |
Loop rows 3–5 per milestone.
| 6 | Release | orchestrator | release-engineer | green mainline | deployed + rollback plan | 1 | smoke check passes [HUMAN GATE] |
```

## Anti-patterns

- **Improvised pipelines** — deciding mid-run whether QA happens is how QA doesn't happen; declare the chain before phase 1.
- **Self-judging phases** — worker and instructor must differ; a phase that grades its own output is a gate in name only.
- **Uncapped polish loops** — "one more review round" repeated is a budget leak; the cap forces the replan conversation.
- **Gates without criteria** — "looks good" is not a gate; write the check the instructor will actually run.
