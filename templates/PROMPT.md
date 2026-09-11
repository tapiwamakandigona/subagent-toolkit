# One iteration, one task

Read `AGENTS.md`, `PROJECT.md`, `features.json`, and the tail of `progress.md`.
Search the repository before assuming work is missing. Pick one unfinished
feature, make the smallest useful change, run its approved checks, and record
the outcome, including any failure.

Never spawn subagents. Never change acceptance criteria, verification commands,
check scripts, or tests merely to get green. Report a necessary spec/check change
instead; a maintainer must review it before a fresh run establishes a new baseline.

Set `passes` to true only after verification, and set `evidence` to a nonempty
project-relative artifact file. Commit the verified work through the environment's
permitted Git workflow. Do not put credentials in source, prompts, output, or logs.

Print `DONE_ALL` on a line by itself only if every feature is complete. The wrapper
will independently check the verifier, feature evidence, and check integrity.
The marker alone never proves completion.
