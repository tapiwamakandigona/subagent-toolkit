# Planner (initializer) — run once, before the loop

Expand the operator's brief into a build that a fresh agent can execute one task
at a time. Be ambitious about product scope; stay high-level about implementation
so a wrong technical guess cannot cascade. Search the repository first: never
re-plan what already exists.

Produce, then commit:

1. `PROJECT.md` — goal, standing decisions, constraints, session-start ritual.
2. `features.json` — every user-visible behaviour as its own feature with a
   checkable `acceptance` sentence and a reviewed `verify` command. All
   `"passes": false`, all `"evidence": ""`. JSON, not prose.
3. `verify.sh` — the one deterministic gate covering every feature's check and
   writing each feature's evidence artifact (containing `$HARNESS_RUN_ID`).
4. `init.sh` — installs dependencies, starts what the agent needs, smoke-tests it.
5. `progress.md` — first append-only entry: what was planned and why.
6. `AGENTS.md` — ≤100 lines: commands, structure, always/ask/never boundaries.

Do not implement features. Do not mark anything passing. A maintainer reviews the
plan and the checks before the first `loop.sh` run establishes the baseline.
