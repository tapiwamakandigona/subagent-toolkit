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

## Browser & authenticated sessions

When an agent logs into a site through a browser, **open a long-running,
6-hour session** — not the short default. A run that authenticates and then
loses the session mid-task has to re-login (re-triggering 2FA and burning a
human interaction) or silently fails on an expired session.

- **Create the session with a 6-hour keep-alive.** Browser sessions default
  to a short idle timeout (300s in the Viktor SDK); pass the max instead.
  In the Viktor SDK: `get_browser(name, timeout_seconds=21600)` (21600s =
  6h). 6h is the Browserbase per-session ceiling. VERIFIED 2026-07-25:
  `timeout_seconds=21600` is accepted and the session is created; the 300s
  default is what causes premature drops.
- **One named session, reconnect — never re-create.** Use a stable session
  name (`get_browser("gmail")`) and reconnect to it across script runs;
  re-creating a session throws away the logged-in state and forces another
  login. Only `close_browser(name)` when the whole task is done.
- **Login is a one-time cost per session; do the whole job inside it.**
  After login the site's own auth cookies persist far beyond the browser
  session (Google's, VERIFIED, last ~400 days), so the binding constraint
  is the browser session lifetime, not the cookies — which is exactly why
  the session must be long. Batch all authenticated work into the single
  6h window.
- **2FA is a human handoff.** When a login hits 2FA (device prompt, code,
  passkey), post the exact prompt to the human and wait for approval; where
  offered, tick "don't ask again on this device" so a reconnect within the
  session doesn't re-challenge. Never guess or loop on a challenge.
- **Evidence before "logged in".** Confirm auth by an authenticated URL or
  a signed-in DOM element (e.g. landed on `myaccount.google.com`), not by
  the absence of an error. Label it VERIFIED only with that evidence.

## Credentials

The operator provisions credentials **per environment — usually by pasting
them into chat**. That paste is the provisioning step, not a policy
violation. Refusing to store it strands the whole environment without
credentials.

- **Store it immediately, outside any repo.** Put pasted credentials in a
  locked-down local file (secrets dir `700`, file `600`), confirm the
  storage path back to the operator, and use them for tasks from there —
  never from chat scrollback.
- **Flag exposure once, then move on.** If credentials arrived in plaintext
  chat or are visibly reused across services, say so once with concrete
  rotation advice — then proceed with the work. Don't block on it, and
  don't repeat the warning every run.
- **Values never leave the secrets file.** No credential values in commits,
  logs, reports, prompts, state files, or issue text. When flagging an
  anomaly (e.g. a suspicious trailing character), describe it without
  printing the value.
- **Missing ≠ inventable.** If a task needs a credential that isn't
  present, stop and ask; never guess, scaffold placeholders, or dig one
  out of unrelated chat history.

## Evidence

Label every deliverable claim **VERIFIED** (command output, diff, artifact
inspected) or **ASSUMED** (inference, unverified report). Never relay an
agent's claim unchecked. If blocked or ambiguous: report, don't guess.
