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
  `progress.md` (append-only log). Read these first every session.

## Boundaries

**Always:** commit after each verified task; update `progress.md`;
run {{test_cmd}} before marking anything done; open browser logins as
6-hour sessions (SDK: `get_browser(name, timeout_seconds=21600)`) and
reconnect to one named session instead of re-creating it.

**Ask first:** {{destructive ops, schema migrations, spending money,
new dependencies}}.

**Never:** edit tests to make them pass; touch `{{generated_paths}}`;
commit secrets; force-push.

## Deeper docs

- `docs/{{topic}}.md` — {{when to read it}}
