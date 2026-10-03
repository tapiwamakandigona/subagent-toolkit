# High-autonomy profile — v3.2.0-derived, opt-in

This is a local upgrade based on canonical main revision
`3a4d707bdc7f72d622c5e4ea1976bee76be10d50`. It is not a published upstream
release, changed Viktor permission, or deployed automation. See VERIFICATION.json
for the local verification and publication scope.
The original `templates/loop.sh` and upstream shell tests are unchanged.

## What changes

- Routine legitimate, reversible work is action-first.
- Operator-provided credentials are explicitly usable for authorized tasks.
  New agents discover a private store without putting values in their context.
- Ordinary verification pages are not blanket hard stops; permitted completion
  and bypassing anti-bot/access controls remain distinct. No CAPTCHA capability
  of the requester's models is claimed or tested.
- Feature-local blockers do not halt independent ready work.
- Early `DONE_ALL` does not stop unfinished work.
- Missing contracts or verification gates fail closed.
- Progress means task-file changes, newly verified features, or a verified
  failing-to-passing test delta — not just a new Git commit or a status report.
- Acceptance/verify commands and selected checks are immutable during a run.
- Oversized progress logs rotate verbatim, with SHA-256 links.
- Iterations, per-process time and total time are bounded.
- The strengthened boot-budget gate includes optional always-read profile
  files and the actual progress tail; it does not silently omit that context.

## Install without overwriting your existing project

Back up your project's rules and state first. Merge the boundary changes from
`templates/AGENTS.md` rather than blindly replacing project-specific commands.
Copy these additions into the project:

- `AUTONOMY.md`, `PROMPT.md`, `autonomous_loop.py`, `high_autonomy_loop.sh`
- `credential_store.py`
- `browser_credentials.py` for runtime-only browser form filling
- the canonical `PROJECT.md`, `features.json`, `check_budget.sh` and
  `EVALUATOR.md` only if the project does not already have them

Fill the existing feature acceptance and verify commands **before** a run.
`blocked_reason` is an optional string for a feature needing human input.
Remove it once that access/decision is supplied. Do not change acceptance or
verify commands while a run is in progress; a spec change starts a new brief.

## Credentials: provision once, reuse safely

Keep only `AGENT_SECRET_DIR` (a directory pointer) in agent setup. The helper's
default is your user's private `~/.local/share/agent-secrets`, outside repos.
It stores plaintext files protected by OS permissions, **not an encrypted vault**.
Use a managed secret manager on shared/multi-tenant hosts and managed OAuth
when the platform requires it.
For fresh agents/containers, point `AGENT_SECRET_DIR` to persistent private
storage mounted for the authorized runtime user. Do not assume a disposable
home directory survives a new sandbox, and do not loosen 700/600 permissions
to fix a missing mount or wrong UID. Provision through the platform's secret
manager or remount the authorized secret instead.

From your own terminal, provision a credential without putting it in argv:

```sh
python3 credential_store.py put github_pat
# Hidden terminal input; no value echoed.
python3 credential_store.py list
python3 credential_store.py check github_pat
```

Noninteractive provisioning accepts `--source` from an already-private file,
or `--stdin`; do not put a literal secret in a shell command or prompt.
The helper preserves bytes; use `--trim-newline` for a token supplied with a
terminal/file newline. `--replace` explicitly authorizes rotating an alias.

Use a credential in an approved API script:

```sh
python3 credential_store.py exec --map github_pat=GITHUB_TOKEN -- python3 api_task.py
```

Values are injected into the child environment, not argv. Exact, URL-encoded,
and Base64 representations of these values are redacted from child stdout and
stderr. This is defense in depth, not a guarantee against every transformation:
the API script must not log secrets, dump its environment, or send them to
unrelated services. In-process callers can import `read_secret`, keep the bytes
in runtime memory, and put them directly into the authorized request headers.
Do not `cat` a secret or run a CLI `get` into model-visible output.

Credentials already exposed in chat or standing instructions should be
rotated, then removed from the prompt. Rotation advice happens once; it does
not justify refusing all remaining legitimate work.

## Browser login is explicitly supported

An operator-provided password can be used in an authorized, supported browser
workflow. API/OAuth preference must not become a blanket browser refusal.
Read `docs/browser.md` for session lifecycle and a runtime-only fill example.
`browser_credentials.py` takes credential **aliases**, not literal passwords,
checks the exact approved HTTPS origin, requires a real password input, and
sanitizes credential values from fill errors.

OS file permissions protect local storage only. A remote browser provider may
record sessions, screenshots, traces, and keyboard/form events; mode 600 does
not control those recordings. Prefer native saved-login injection when the
platform exposes it; verify its recording/redaction behavior. Otherwise keep
login tracing/capture disabled and do not claim third-party recording is
secret-free without verifying it. Use a local controlled browser or human
login handoff if the provider cannot meet the account's requirements.

## Run

Use your platform's supported agent invocation, not an unauthenticated guess:

```sh
AGENT_CMD='your-agent-cli your-approved-flags' \
VERIFY_CMD='make ci' \
sh high_autonomy_loop.sh --max-iterations 40 --max-seconds 7200 \
  --step-timeout 1800 --protect tests
```

`AGENT_CMD` is parsed as argv, not evaluated by a shell. Use an authorized
wrapper script if the invocation needs shell composition. `VERIFY_CMD` and
feature `verify` commands are trusted project commands and run through `sh`.
An executable `verify.sh` can replace `VERIFY_CMD`; the gate is mandatory.
The runner does not grant approvals, spend authority or repository access.

Defaults: 40 iterations, 2 hours total, 30 minutes per agent/check invocation.
Choose lower caps for costly model/API work. A wall-clock cap is **not** a dollar
budget; use provider billing controls and an explicit approved spend ceiling.
Two consecutive no-progress iterations always halt. The runner kills its own
timed-out process group on POSIX; this cannot undo remote work already accepted
by a service or terminate independently daemonized children.

## Exit codes and evidence

| Code | Meaning |
|---|---|
| 0 | Every feature check and the full gate actually passed |
| 1 | Iteration cap or claimed completion failed verification |
| 2 | Two iterations stalled (argparse also uses 2 for invalid CLI syntax) |
| 3 | A global blocker, or only blocked features remain |
| 4 | Missing/invalid configuration or check-integrity violation |
| 5 | The same failure persisted through one informed retry |
| 6 | Per-process or total wall-clock limit |

Receipts: `.harness/evidence.json`; summary: `.harness/run-report.json`.
No full agent transcript is written by the runner. Failures fed back into
the next iteration are tagged as data; oversized error output is labeled as
an excerpt rather than misrepresented as complete.

Check-integrity protection covers feature IDs/acceptance/verify commands and,
by default, PROMPT.md, AGENTS.md, AUTONOMY.md, verify.sh and check_budget.sh.
Add `--protect tests` or other gate paths. This is a deterministic guard against
accidental changes, not a security sandbox against a malicious same-user agent.

## Verification scope

The included regression suite uses scripted fake agents and temporary task
directories. It verifies local runner/store behavior, not an actual provider's
willingness, remote credentials, real model performance, or remote CI.
Credentials used in tests are generated fixtures, never operator secrets.

## Tool-status lookup failures are not permission denials

A status helper may fail to match a generated SDK alias to the primary
integration settings. Before declaring a tool blocked, distinguish "no matching
tool name" from `enabled=false` or a forbidden approval level. Inspect the
primary setting for that exact tool and use its documented native SDK function.
Never route around a genuinely disabled tool or change permissions silently.
