# One iteration, one task

Read `AGENTS.md`, `PROJECT.md`, `features.json`, and the tail of `progress.md`.
Search the repository before assuming work is missing. Pick the single most
important unfinished feature, make the smallest useful change, run its approved
checks, and record the outcome in `progress.md`, including any failure.

Never spawn subagents. Never change acceptance criteria, verification commands,
check scripts, hooks, or tests merely to get green; report a needed spec/check
change instead so a maintainer can review it before a fresh run re-baselines.

Set `passes` to true only after the reviewed checks pass; leave `evidence`
pointing at the artifact `verify.sh` writes for that feature. Commit verified
work through the environment's permitted Git workflow. Never put credentials in
source, prompts, output, reports, or logs.

Before exiting, write `report.json` in the project root — the wrapper rejects the
iteration without it:

```json
{
  "task": "what you worked on",
  "status": "progress | blocked | complete",
  "claims": [
    {"text": "tests pass", "label": "VERIFIED", "evidence": "artifacts/tests.txt"},
    {"text": "UI looks right on phones", "label": "ASSUMED", "evidence": null}
  ],
  "approval_requests": [],
  "next": "the next single task"
}
```

Every claim is `VERIFIED` (with a project-relative evidence file) or `ASSUMED`.
Put destructive/irreversible actions, spending, missing credentials, or genuine
ambiguity in `approval_requests` and stop; the wrapper halts for a human. The
wrapper independently checks the verifier, feature evidence, and check integrity;
`"status": "complete"` alone never proves completion.
