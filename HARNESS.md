# HARNESS.md — the operating protocol

One file, the whole method. Read this at the start of a run; load templates
from `templates/` only when you need them.

## Principles

1. **One agent by default.** A single agent with clean context outperforms a
   swarm on almost everything. Handoffs bury intent, multiply tokens, and
   let parallel writers make conflicting implicit decisions ("Don't Build
   Multi-Agents" — Cognition). Parallelize only when the work splits into
   genuinely independent, read-heavy or disjoint-path tracks.
2. **The repo is the brain; agents are disposable.** All state lives in
   files and git, never in a model's memory. Any fresh agent must be able to
   resume from the state files alone.
3. **Feedback beats instructions.** Of the harness subsystems — rules,
   state, tools, checks, environment — checks have the highest return.
   An agent without checks overestimates its own output and cannot learn.
   Invest in tests, linters, build gates, and evidence requirements before
   tuning prompts.
4. **Lean context wins.** Models reliably follow ~150–200 instructions
   total; every extra rule degrades all rules. Keep the always-loaded rules
   file short (≤100 lines), push depth into on-demand docs, and delete
   scaffolding the model has outgrown.
5. **Small steps, verified, committed.** One task per iteration, checks run,
   progress committed. Deterministically modest beats unpredictably
   ambitious.

## The loop

Every unit of work follows plan → act → verify → commit:

1. **Plan.** Write the plan as a doc before acting (task list with
   checkable definitions of done). A bad plan beats no plan because a bad
   plan is visible.
2. **Act.** Execute one task. If execution reveals the plan is wrong,
   revise the plan doc first, then continue.
3. **Verify.** Run the checks. "It should work" is not evidence; a passing
   command, a diff, or an artifact is.
4. **Commit.** Commit the work with a message that says what and why, and
   update the state files.

For long work, run this loop with **fresh context per iteration**
(Ralph-style): the agent re-reads the state files, picks the single most
important unfinished task, does it, verifies, commits, exits. The loop
restarts it. Progress lives in files and git, so restarts lose nothing.
`templates/loop.sh` is the reference loop with stop conditions and guards.

## State files

Three files, kept current, are the resume point for any fresh agent:

- `PROJECT.md` — goal, standing decisions, constraints, session-start
  ritual. Template: `templates/PROJECT.md`.
- `features.json` — machine-readable definition of done. Each feature has
  `"passes": false` until there is evidence; only flip with evidence.
  Template: `templates/features.json`.
- `progress.md` — append-only history of what was done, what worked, what
  failed. Failures are data; record them so the next iteration doesn't
  repeat them.

## Rules file (AGENTS.md / CLAUDE.md)

The always-loaded contract. Keep it ≤100 lines: executable commands, project
structure map, non-negotiable constraints, three-tier boundaries (always do /
ask first / never do), and an index to deeper docs. The test for every line:
"would removing this cause mistakes?" If no, cut it. Task-specific playbooks
go in skills or `docs/`, not here. Template: `templates/AGENTS.md`.

## Checks

- Wire tests/lint/build so the agent runs them after every change
  (`make ci` or equivalent — one command, deterministic).
- Completion is defined by the checks and `features.json`, not by the
  agent's claim. Reject "done" without evidence.
- Guard rails that must hold (don't touch tests, don't edit generated
  files) belong in hooks/CI, not prose — deterministic beats probabilistic.

## Loop guards

- **One thing per iteration.** An iteration that tries three tasks fails
  at all of them.
- **Max iterations.** Hard cap per run; overrun means the task or the
  checks are wrong, not that you need more loops.
- **Stall halt.** Two consecutive iterations with no diff and no
  test-delta → stop and report; don't grind.
- **Failure handling.** One retry with the failure quoted verbatim in the
  new brief; then descope or escalate. Never retry the identical prompt
  blindly, and never fabricate what a failed run "would have found".

## Parallelism (the exception)

Gate before spawning anything — all four must be true:

1. The work splits into tracks with **disjoint file/path ownership** (or
   separate git worktrees/branches).
2. Tracks don't need to talk while running; a summary handoff is enough.
3. Each track is verifiable on its own.
4. You can name at least 3 genuinely independent tracks — otherwise a
   single agent is faster and cheaper.

Rules when you do: one writer per path set, interfaces frozen and quoted
verbatim in every brief, serial integration in a fresh context, regenerate
(never hand-merge) generated files. Brief template: `templates/brief.md` —
objective, output contract, boundaries, budget, escape hatch, ≤500 words.
Read-heavy fan-out (research, audits, log analysis) is the sweet spot;
write-heavy fan-out is where swarms betray you.

## Evidence

Label every deliverable claim **VERIFIED** (command output, diff, artifact
inspected) or **ASSUMED** (inference, unverified report). Never relay an
agent's claim unchecked. If blocked or ambiguous: report, don't guess.
