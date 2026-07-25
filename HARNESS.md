# HARNESS.md — the operating protocol

One file, the whole method. Read this at the start of a run; load templates
from `templates/` only when you need them.

## Principles

1. **One agent. No subagents.** A single agent with clean context
   outperforms a swarm on almost everything: handoffs bury intent, multiply
   tokens, and let parallel writers make conflicting implicit decisions
   ("Don't Build Multi-Agents" — Cognition). This harness does not spawn
   subagents, period. If work seems to demand parallelism, sequence it —
   or run two independent harnessed loops on fully separate repos/branches,
   started and integrated by a human.
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

Two rules keep the loop honest: **one task per iteration** (protects the
context window from filling with noise), and **search before assuming** —
check the repo and progress.md before treating anything as unbuilt, so
iterations don't redo or overwrite finished work. Prefer fresh restarts
over compaction for long runs: a summary of a summary is a blurry
photocopy of the plan, and a persistent session reintroduces context rot.

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
- **Check integrity.** The fastest path to green is editing the check; a
  weakened assertion, a skipped test, or a hardcoded return is a failure,
  not a fix. Tests and check scripts are read-only unless the task IS the
  check — and then the diff to them is called out explicitly.
- **Completion must be machine-verifiable.** "Run until done" is only as
  safe as its stop signal; prefer an exit code (`make ci`, features.json
  all-passing) over a model reading a transcript and judging "looks done".

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

## No subagents

There is no parallelism gate because there is no parallelism: this harness
never spawns subagents. Reasons, so the temptation stays dead:

- Parallel writers make conflicting implicit decisions that surface only
  at integration, where they cost more than the parallelism saved.
- A brief can't transfer full context; a summary handoff loses exactly the
  nuance that made the work hard.
- Subagent claims arrive unverified; re-verifying them costs as much as
  doing the work.
- Field result (v2, this repo): swarm output was worse than one
  well-harnessed agent. The 2025–26 practitioner consensus agrees.

If throughput is genuinely the bottleneck, run separate harnessed loops on
fully separate repos or branches — started, owned, and integrated by a
human, not spawned by an agent.

## Evidence

Label every deliverable claim **VERIFIED** (command output, diff, artifact
inspected) or **ASSUMED** (inference, unverified report). Never relay an
agent's claim unchecked. If blocked or ambiguous: report, don't guess.
