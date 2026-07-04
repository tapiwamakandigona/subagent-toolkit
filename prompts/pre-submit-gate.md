# Pre-Submit Gate

The mandatory pass between "worker believes it's done" and the handoff report. The worker lists every change it made, cleans up, reverts anything out of scope, re-runs the named verification, and attaches evidence — *then* submits. Forcing the diff back through the agent's own eyes catches scratch files, drive-by edits, and stale verification at the cheapest possible moment.

## Usage notes

- Run this after `self-review-rubric.md` (which judges the *content*); this gate judges the *change set and its evidence*. For code, both; for quick tasks, at minimum this gate.
- "Named verification" means the command your brief or task row designates as the definition of done — re-run it *now*, after cleanup, because cleanup breaks things more often than expected.
- Evidence is what survives the handoff: the orchestrator rejects completion claims without proof artifacts (evidence-of-done — see `../agents/orchestrator.md`). Passing this gate is what makes your STATUS: complete believable.
- If a step fails, fix and restart the gate from step 1 — a gate you partially passed is a gate you didn't pass.

## Template

```text
PRE-SUBMIT GATE for: {{task_id_or_brief_reference}}

1. LIST ALL CHANGES
   {{git diff --stat / git status, or an explicit file list for non-git work}}
   For each changed path: owned per my brief? [yes / NO → step 3]

2. REMOVE SCRATCH
   Delete debug output, temp files, dead code, commented-out experiments,
   reproduction scripts that shouldn't ship. List what was removed: {{list_or_none}}

3. REVERT OUT-OF-SCOPE EDITS
   Any change outside owned paths or beyond the brief: revert it
   (git checkout -- {{path}} / undo), and record it as a finding for the
   report instead. Reverted: {{list_or_none}}

4. RE-RUN NAMED VERIFICATION
   Command: {{the_verification_command_from_the_brief}}
   Output: {{pass_fail_counts_or_key_lines — after cleanup, not from memory}}

5. ATTACH EVIDENCE
   {{paths_to_proof_artifacts: test output, logs, screenshots, rendered files}}
   Every completion claim in my report maps to an item here.

6. SUBMIT
   Gate passed → write the handoff report (prompts/handoff-report.md).
   Any step failed → fix, then restart from step 1.
```

## Anti-patterns

- **Verification from memory** — "tests passed earlier" is not step 4; the run after cleanup is the one that counts.
- **Shipping the scratch** — reproduction scripts, debug prints, and `.bak` files in the diff are the most common handoff pollution.
- **Keeping the helpful drive-by** — an out-of-scope fix may be correct, but it belongs in the report as a suggestion, not in the change set; the path's owner decides.
- **Evidence-free claims** — a report whose VERIFICATION section cites nothing from step 5 will (correctly) bounce.
