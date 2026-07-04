# Artifact: Task List

The backlog for a milestone or project — the output of decomposition and the orchestrator's dispatch queue. Every task carries the triple that makes delegation verifiable: what to do, the command that auto-verifies it, and one sentence telling a human how to eyeball it. A task missing any leg of the triple isn't ready to delegate.

## Usage notes

- The auto-verify command is the definition of done; if you can't write it yet, the task is under-specified — split it or spec it further.
- The human-verify sentence keeps the human gate cheap: someone skimming the list can spot-check any "done" claim in under a minute.
- One owner per task at a time (single-writer rule — `../../harness/patterns.md`); the branch column is how worktree-isolated parallel work stays traceable to the integrator.
- Status vocabulary is fixed: `todo | in-progress | blocked | review | done`. Only flip to `done` after the auto-verify command passed and evidence is attached to the handoff.

## Template

```text
# Task list: {{project_or_milestone}}
Spec: {{path}}   Architecture: {{path}}   Updated: {{date}}

| ID | Task (what to do) | Auto-verify (command) | Human-verify (one sentence) | Owner | Status | Branch |
|----|-------------------|-----------------------|------------------------------|-------|--------|--------|
| T-1 | {{concrete_change_with_target_paths}} | {{command_that_proves_it}} | {{how_a_human_eyeballs_it}} | {{agent_or_role}} | {{status}} | {{branch_or_dash}} |
| T-2 | {{...}} | {{...}} | {{...}} | {{...}} | {{...}} | {{...}} |

## Blocked notes
{{task_id}}: {{what_its_waiting_on_and_who_owns_unblocking}}
```

### Example row (filled)

```text
| T-4 | Add rate limiting to POST /login (src/auth/) | pytest tests/test_rate_limit.py | Try 6 rapid logins in the browser; the 6th shows a "try again later" message | code-worker-2 | review | feat/rate-limit |
```

## Anti-patterns

- **"Improve X" tasks** — no observable difference stated, so no verify command possible; not dispatchable.
- **Verify-by-owner-opinion** — the auto-verify command must be runnable by anyone, especially the QA engineer and the orchestrator.
- **Two owners, one path** — if two rows touch the same files, serialize them or redraw the boundary before dispatch.
- **Status flipped without evidence** — `done` without the command's passing output attached is a claim, and claims get rejected at the gate.
