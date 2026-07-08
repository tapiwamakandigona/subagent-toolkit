# Project Lifecycle

The playbook for full-project runs: one-line idea → spec → architecture → milestone builds → QA → release. Task-level delegation ([`patterns.md`](patterns.md)) handles a bounded task; this doc handles the phase structure around many of them. It assumes the project state protocol from [`context-management.md`](context-management.md) §6 — `PROJECT.md`, `features.json`, `progress.md`, `init.sh`, `checkpoints/` — is in place from the first phase.

A phase is done when its output artifact exists, meets its gate criteria, and the go/no-go decision is written to a checkpoint. Not before, and never on an agent's say-so alone.

---

## 1. Phases

| Phase | Instructor → worker | Input | Output artifact | Gate criteria |
|---|---|---|---|---|
| **Spec** | orchestrator → product-manager | the idea, one line up | `spec.md` (see `../prompts/artifacts/spec.md`) | every functional requirement carries a machine-checkable acceptance criterion; assumptions logged; **[HUMAN GATE]** |
| **Architecture** | orchestrator → architect | approved spec | `architecture.md` (see `../prompts/artifacts/architecture.md`) | stack decided with rationale; module map with owners; interface contracts verbatim; design freeze declared |
| **Foundation** | orchestrator → release-engineer | architecture | scaffolded repo, CI, and the state files (`../prompts/artifacts/project-state.md`; instantiate with `python3 harness/scripts/scaffold_project.py <dir> --name N --goal G [--features seed.json]`): `init.sh`, initial `features.json` | fresh clone + `init.sh` yields a running skeleton whose test suite contains at least one trivial smoke test and runs green — an empty suite is not a passing suite (bare `python3 -m unittest discover` exits 5 with "NO TESTS RAN" on Python 3.12+) |
| **Milestone loop** | see §2 | task list for the milestone (see `../prompts/artifacts/task-list.md`) | working increment, all milestone features `passes: true` | every acceptance check green; QA defects at [Blocking] severity: zero; checkpoint written |
| **Release** | orchestrator → release-engineer | final increment | deployed/packaged release + rollback path | E2E verification as a real user; rollback tested or documented; **[HUMAN GATE]** |

The pipeline is declarative: write it down as a phase-chain table (template: `../prompts/phase-chain.md`) at planning time and execute it mechanically. Deviations are replans (§4), not improvisation.

---

## 2. The milestone loop

Each milestone from the spec runs the same inner cycle:

1. **Build** — code-workers implement the milestone's tasks under path ownership or branch isolation (single-writer rule, `patterns.md` pattern 2). Each task carries its auto-verify command from the task list.
2. **QA** — qa-engineer writes/extends tests as deliverables and verifies the increment end-to-end as a real user; logs defects, never fixes them. Defects go back to build as rework briefs; review/fix cycles cap at 3.
3. **Integrate** — integrator merges branches serially in deliberate order, resolves conflicts in fresh context, regenerates generated/shared files.
4. **Gate** — orchestrator checks `features.json`: every feature in the milestone has `passes: true` with an `evidence` path that actually exists. Run `harness/scripts/check_features.py <features.json> --gate --milestone <M> --against <baseline>` from the installed pack (shape + evidence existence + gate + frozen-criteria tamper check), plus `check_contract.py` on each handoff sidecar; then open the evidence and judge it — the scripts prove the proof exists, not that it proves the right thing. Records go/no-go in `checkpoints/NN-<milestone>.md`.

**Evidence-of-done:** a completion claim without a proof artifact (test output, screenshot, E2E log) is rejected as-is — the work may be fine, but the claim isn't. VERIFIED means you ran the check; ASSUMED means you didn't; reports must say which.

One milestone per pass. An agent asked to "build the whole app" will run out of context mid-bite and leave a half-built mess; the milestone boundary is where state gets flushed to disk and contexts get reset (constant-context restart, `context-management.md` §6).

---

## 3. Human gates

Default gates — pause and get explicit approval; everything else runs autonomously:

- **Spec approval** (end of Spec phase): the cheapest moment to be wrong. Everything downstream inherits the spec.
- **Destructive or irreversible operations**: data deletion, migrations against shared databases, force-pushes, spending money. Deny by default; environment separation over prompt-level caution.
- **Release** to anything a real user touches.

Mark gates in the plan as `[HUMAN GATE]` so they're visible at planning time, not discovered mid-run. Projects can add gates (e.g. after architecture); removing a default gate is itself a human decision.

---

## 4. Replan triggers

Plans are checkpoints, not contracts. Replan — using `../prompts/replan.md`, from the latest checkpoint — when:

- a spec assumption fails in reality (the logged assumption was wrong),
- the same task fails twice with changed briefs (`patterns.md` §5: two failures is evidence about the plan),
- a third of a fan-out fails (the partition is wrong),
- no-progress detection fires (two iterations, no diff/test delta),
- the milestone budget envelope is exhausted with the gate unmet.

A replan keeps verified work, accounts for sunk cost honestly, and carries interface contracts forward verbatim. Silent perseverance past a trigger burns budget on hope.

---

Three rules worth restating: no phase closes without its artifact, its gate, and a checkpoint; claims need evidence, not confidence; one milestone per pass, state on disk between passes.
