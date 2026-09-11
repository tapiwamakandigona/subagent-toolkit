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
   started and integrated by a human. (A sequential, read-only evaluator
   pass is not a subagent — see "Independent evaluator".)
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
   plan is visible. For a new build, run `templates/PLANNER.md` once first:
   it expands a short brief into `features.json` (all failing), `verify.sh`,
   `init.sh`, `PROJECT.md` — a maintainer reviews these before the loop.
2. **Act.** Execute one task. If execution reveals the plan is wrong,
   revise the plan doc first, then continue.
3. **Verify.** Run the checks. "It should work" is not evidence; a passing
   command, a diff, or an artifact is.
4. **Commit.** Commit the work with a message that says what and why, and
   update the state files.

For long work, run this loop with **fresh context per iteration**
(Ralph-style): the agent re-reads the state files, picks the single most
important unfinished task, does it, verifies, commits, writes `report.json`,
exits. `templates/loop.sh` restarts it. Progress lives in files and git, so
restarts lose nothing. Prefer fresh restarts over compaction: a summary of a
summary is a blurry photocopy of the plan, and a persistent session
reintroduces context rot and "context anxiety" (wrapping up early as the
window fills).

Two rules keep the loop honest: **one task per iteration** (protects the
context window from filling with noise), and **search before assuming** —
check the repo and progress.md before treating anything as unbuilt, so
iterations don't redo or overwrite finished work.

### Two phases per run

Imported from Codex cloud environments: **setup** runs once with network
and full environment (`init.sh`: install, start, smoke-test), then the check
baseline is frozen and **agent iterations** run offline by default through
`sandbox.sh` (environment allowlist, no network unless `HARNESS_NET=1`,
bubblewrap filesystem isolation when available). Secrets belong to phase 1
and to credential files, never to the agent's environment.

### Capability vs. approval

Also from Codex: what the agent **can** do (sandbox) is separate from when it
must **ask** (approval). The AGENTS.md boundaries (always / ask first / never)
are the approval policy. When a task hits "ask first", the agent lists it in
`report.json → approval_requests` and stops; the loop writes
`APPROVAL_REQUESTED.md` and exits 5 for a human. Never work around a denied
capability; ask.

## State files

Three files, kept current, are the resume point for any fresh agent:

- `PROJECT.md` — goal, standing decisions, constraints, session-start
  ritual. Template: `templates/PROJECT.md`.
- `features.json` — machine-readable definition of done. Each feature has
  `"passes": false` until there is evidence; only flip with evidence.
  Evidence is an artifact **written by `verify.sh`** and containing the
  current `HARNESS_RUN_ID`, so a claim cannot masquerade as a check result.
  Template: `templates/features.json`.
- `progress.md` — append-only history of what was done, what worked, what
  failed. Failures are data; record them so the next iteration doesn't
  repeat them.

Per-iteration artifacts: `report.json` (the agent's structured report —
task, status, claims each labeled VERIFIED/ASSUMED with evidence,
approval requests, next task; validated and archived by the loop) and, when an
evaluator is configured, `evaluation.json`. The loop keeps a hash-chained,
append-only ledger of every run in `.harness/runs/` (`check_features.py chain`
verifies it) and a single-writer lock in `.harness/lock`.

## Rules file (AGENTS.md / CLAUDE.md)

The always-loaded contract. Keep it ≤100 lines: executable commands, project
structure map, non-negotiable constraints, three-tier boundaries (always do /
ask first / never do), and an index to deeper docs. The test for every line:
"would removing this cause mistakes?" If no, cut it. Task-specific playbooks
go in skills or `docs/`, not here. Template: `templates/AGENTS.md`.
Codex reads `AGENTS.md` root-down with nearer files overriding; Claude Code
reads `CLAUDE.md`. Keep one and symlink the other if both agents are used.

## Checks

- Wire tests/lint/build so the agent runs them after every change
  (`verify.sh` — one command, deterministic, writes the evidence artifacts).
- Completion is defined by the checks and `features.json`, not by the
  agent's claim. Reject "done" without evidence. `"status": "complete"` in
  the report only tells the loop to run the gate.
- Guard rails that must hold (don't touch tests, don't edit generated
  files) belong in hooks/CI, not prose — deterministic beats probabilistic.
- **Check integrity.** The fastest path to green is editing the check; a
  weakened assertion, a skipped test, or a hardcoded return is a failure,
  not a fix. `loop.sh` freezes acceptance criteria, `verify.sh`, hooks,
  workflows and `tests/` at run start and exits 6 on any change; the checker
  itself runs from a run-local copy so it cannot be edited into compliance.
- **Completion must be machine-verifiable.** "Run until done" is only as
  safe as its stop signal; prefer an exit code (`verify.sh`, features.json
  all-passing with run-bound evidence) over a model judging "looks done".
- **Hooks are trusted by hash.** `hooks/pre_iteration` and
  `hooks/post_iteration` run only when `hooks.lock` pins their exact
  contents (Codex's trust model); changed or unpinned hooks are skipped and
  logged, never run.

### Independent evaluator (optional, sequential)

Anthropic's harness work found the strongest lever after checks is separating
the agent that builds from the agent that judges: self-grading skews
generous. `EVALUATOR_CMD` runs **after** each successful iteration, in a fresh
context, with `templates/EVALUATOR.md`: it reviews the diff, artifacts and
report, exercises the work read-only, and writes `PASS` or `NEEDS_WORK` with
reproducible findings that are fed into the next brief. It is not a subagent:
nothing runs in parallel, and the loop fingerprints the project before and
after — an evaluator that changes anything is an integrity violation (exit 6).
`NEEDS_WORK` blocks completion. Use it when the task sits beyond what the
model does reliably solo; drop it when a model upgrade makes it dead weight.

## Loop guards

- **One thing per iteration.** An iteration that tries three tasks fails
  at all of them.
- **Max iterations** (`loop.sh N`, 1–1000) and **wall-clock caps**
  (`ITER_TIMEOUT` per run, default 1h; `MAX_MINUTES` per loop). Overrun
  means the task or the checks are wrong, not that you need more loops.
- **Output cap** (`OUTPUT_CAP`, default 5 MB) — runaway transcripts fail
  the iteration instead of filling the disk.
- **Stall halt.** Two consecutive iterations with no project-content delta
  and no check-status delta → exit 2; don't grind. Progress-log-only writes
  and commit metadata do not count as progress.
- **Failure handling.** One retry with the failure quoted verbatim in the
  new brief; then exit 1 for descope or escalation. Never retry the identical
  prompt blindly, and never fabricate what a failed run "would have found".
- **Operator controls.** `touch AGENT_STOP` halts before the next iteration
  (exit 7); `STEER.md` is injected into the next brief once, then consumed.
  Watch a run with `tail -f progress.md` and the `.harness/runs/*.jsonl`
  ledger — no dashboard needed.
- **Exit codes.** 0 complete · 1 repeated failure · 2 stalled · 3 setup ·
  4 cap reached · 5 approval required · 6 integrity · 7 operator stop.

## Honest limits

`sandbox.sh` is a best-effort boundary: bubblewrap when installed, else a
network namespace, else environment scrubbing only — it reports which mode
ran (`HARNESS_SANDBOX`, ledger `sandbox_mode`) and `HARNESS_REQUIRE_SANDBOX=1`
refuses to run without isolation. Codex enforces this at the kernel; this
harness cannot. Integrity checks detect silent check edits, not a hostile
process running as the same user. Evidence binding proves an artifact came
from this run's checks, not that the checks are sufficient — that is what
review of `verify.sh` is for. The evaluator is a model: `PASS` is a second
opinion, not proof.

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
