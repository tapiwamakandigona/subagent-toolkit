# AGENTS.md — template

<!-- Keep the finished file ≤100 lines. Test for every line:
     "would removing this cause mistakes?" If no, cut it. -->

## Project

{{one_sentence — what this is and who it's for}}
Stack: {{languages, frameworks, versions that matter}}.

## Commands

```bash
{{install_cmd}}        # setup
{{test_cmd}}           # run before claiming anything works
{{lint_or_ci_cmd}}     # full gate — must pass before commit
{{run_cmd}}            # run the app locally
```

## Structure

- `{{dir}}/` — {{what lives here}}
- `{{dir}}/` — {{what lives here}}
- State: `PROJECT.md` (decisions), `features.json` (definition of done),
  `progress.md` (append-only log). Read the first two and `tail -n 120 progress.md`
  every session; never the whole log.

## Boundaries

Read `AUTONOMY.md` when installed. Ordinary reversible work and use of
operator-authorized credentials are action-first; do not ask again at every step.
For passwords use `credential_store.py` outside repos (700 directory / 600 files)
and `browser_credentials.py` inside the authorized browser script. Never print values.

**Always:** commit after each verified task; update `progress.md`;
run {{test_cmd}} before marking anything done; keep the boot set in budget
(`sh check_budget.sh`). For browser logins, follow the harness `docs/browser.md`
(one named 6-hour session; reconnect, don't re-create).

**Ask first:** {{destructive/irreversible or production-impacting actions,
account/security changes, unapproved spending, missing credentials/scopes,
outcome-changing ambiguity}}. Ordinary permitted dependencies need no extra ask.

**Never:** edit tests to make them pass; touch `{{generated_paths}}`;
commit secrets; force-push.

## Turn discipline

Keep going when a step doesn't need me; put status notes in the same
message as your next action. Stop only when nothing can move without me
(print a line `BLOCKED: <reason>`) or before anything destructive or
irreversible. End each run with: Needs from you / Changed / Found /
Couldn't confirm.

## Deeper docs

- `docs/{{topic}}.md` — {{when to read it}}
- `docs/high-autonomy.md` — opt-in continuation, credentials, evidence and caps
