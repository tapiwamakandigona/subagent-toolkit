# Artifact: Project State Files

The required shapes for four of the five project-state files of `../../harness/context-management.md` §6 — `PROJECT.md`, `features.json`, `progress.md`, `init.sh`; the fifth, `checkpoints/NN-<phase>.md`, has its own sibling template (`checkpoint.md`). Created in the Foundation phase (`../../harness/project-lifecycle.md` §1) and kept true for the rest of the run. The other artifacts in this folder are phase *outputs*; these files are the project's *memory*, and the successor-completeness rule is judged against them.

## Usage notes

- Instantiate the whole file set with `python3 harness/scripts/scaffold_project.py <dir> --name N --goal G [--features seed.json]` — it validates the seed first, writes the baseline snapshot to `checkpoints/features.baseline.json`, and leaves `init.sh` as a failing stub so a cold start can't be reported green by accident.
- The orchestrator creates all four in Foundation and owns `PROJECT.md` and the frozen fields of `features.json`; workers only flip `passes`/fill `evidence`, anyone appends to `progress.md`, and whoever changes the environment keeps `init.sh` true.
- Snapshot `features.json` (e.g. to `checkpoints/features.baseline.json`) whenever the orchestrator edits it; every gate runs `python3 harness/scripts/check_features.py features.json --gate [--milestone M] --against <baseline>` so criteria edits by workers are caught mechanically.
- `evidence` paths are relative to the directory containing `features.json` (override with `--base`); point at proof artifacts — test output, E2E logs, screenshots — not at the code itself.
- Keep milestone tags aligned with the task list so `--milestone` gates one bite at a time.

## Template: PROJECT.md

```text
# {{project_name}}
{{one_paragraph_goal — what exists when this is done, for whom}}

Spec: {{path}}   Architecture: {{path}}   Task list: {{path}}
Features: ./features.json   Progress: ./progress.md   Env: ./init.sh

## Standing decisions
- {{decision}} — because {{reason}}
```

## Example: features.json

Passes `check_features.py` verbatim once the referenced evidence files exist; entry shape is pinned by `../../harness/schemas/features.schema.json`.

```json
[
  {
    "id": "signup-basic",
    "title": "User can sign up with email and password",
    "acceptance": "POST /signup with a fresh email returns 201 and the user can then log in; covered by tests/test_signup.py::test_happy_path",
    "passes": true,
    "evidence": "artifacts/m1/signup-test-output.txt",
    "milestone": "m1"
  },
  {
    "id": "signup-dup-409",
    "title": "Duplicate signup is rejected",
    "acceptance": "POST /signup with an existing email returns 409 and creates no user row",
    "passes": false,
    "evidence": null,
    "milestone": "m1"
  }
]
```

## Template: progress.md

```text
# Progress — append only, never rewrite history
2026-07-08 orchestrator: Foundation gate GO — init.sh yields running skeleton, empty suite green (checkpoints/01-foundation.md)
2026-07-08 code-worker-a: signup-basic passes — evidence artifacts/m1/signup-test-output.txt
{{date}} {{agent}}: {{one_line — what completed, what was decided, or gate result}}
```

## Notes on init.sh

One idempotent script from fresh clone to running system: install, migrate, start, smoke-test — exit non-zero on any failure so "environment is up" is machine-checkable. If setup needs a secret, read it from the environment and fail with a named variable ("missing $STRIPE_KEY"), never a baked-in value.

## Anti-patterns

- **Prose definition of done** — if completion lives in `PROJECT.md` paragraphs instead of `features.json` entries, nothing can gate it mechanically.
- **Evidence pointing at code** — "the feature is implemented in src/auth.py" proves editing, not passing; evidence is the *output* of a verification.
- **Rewriting progress.md** — a cleaned-up log is a falsified log; append corrections as new lines.
- **Stale init.sh** — an environment change without an `init.sh` update fails the next fresh-clone resume, exactly when no one remembers why.
