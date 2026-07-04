---
name: code-quality
description: Practices for writing and reviewing code as an autonomous agent. Covers making the smallest useful change, reading code before writing it, targeted testing, defensive refactoring, and commit hygiene. Use whenever modifying an existing codebase, writing new code that others will maintain, or reviewing code changes.
license: MIT
metadata:
  version: "2.0.0"
---

# Code Quality for Agents

Agents have a specific failure profile: they write plausible code fast, in codebases they've known for minutes, without the accumulated context a human maintainer has. These practices compensate.

## 1. Read before you write

Before changing anything, spend real effort understanding the local territory:

- **Find the pattern:** how does this codebase already do the thing you're about to do (error handling, logging, config, tests)? Match it. A "better" pattern that's inconsistent with the codebase is worse.
- **Trace, don't guess:** follow the actual call path of the code you're changing (grep for callers, read the function top to bottom). Never modify a function whose callers you haven't identified.
- **Read the tests first** — they're the executable spec and the fastest way to learn intended behavior.
- **Check for prior art:** search for existing utilities before writing new ones. Duplicated helpers are a classic agent artifact.

## 2. Smallest useful change

- Solve the stated problem, not the general problem. No speculative parameters, no "while I'm here" refactors, no drive-by formatting of untouched lines — they bloat the diff and hide the real change from reviewers.
- If you notice unrelated problems, **note them in your report** instead of fixing them silently.
- Prefer changing 5 lines in the right place over adding a 50-line parallel path. If the right place is hard to change, that's information — surface it.
- Deleting code is a first-class outcome. The best fix is often removal.

## 3. Targeted tests

- **Reproduce first:** for bug fixes, write or run a test that fails *before* your change and passes after. A fix without a failing-then-passing test is a hypothesis.
- Test the behavior you changed plus the nearest edge cases (empty, null, boundary, error path) — not an exhaustive suite for code you didn't touch.
- Run the *existing* test suite (or the relevant subset) after your change. Your job includes not breaking what worked.
- If the project has no test infrastructure, verify by executing the changed path manually and record exactly what you ran and observed.
- **Run the repo's configured linters/formatters/type-checkers** (look for configs: `.eslintrc`, `ruff.toml`, `pyproject.toml`, `mypy.ini`, `.pre-commit-config.yaml`, CI workflows) before submitting — cheap, high-signal, and a common agent omission.
- Never weaken an assertion or delete a failing test to get green. A failing test is a message; read it.

## 4. Defensive refactoring

When you must restructure code:

- **Refactor and behavior-change in separate steps** (ideally separate commits). A diff that does both is unreviewable.
- Keep the system working at every step — small moves, run tests between moves.
- Preserve public interfaces unless the task explicitly includes changing them; if you must break one, find and update every caller in the same change.
- Leave seams, not scars: extracted functions get real names and the same error behavior as before. Don't swallow exceptions that used to propagate.

## 5. Commit hygiene

- One logical change per commit. If your commit message needs "and", split it.
- Message format: imperative summary line (≤72 chars) saying *what*, body saying *why* and any non-obvious consequences:

  ```
  Fix session expiry check to use UTC

  Sessions created in non-UTC server timezones expired early because
  expiry was compared against local time. Adds regression test.
  ```
- Never commit: secrets, credentials, generated artifacts, editor droppings, commented-out code, debug prints. Check `git diff --staged` line by line before committing — this is where agents ship their scaffolding.
- Don't rewrite published history; don't force-push shared branches.

## 6. Reviewing code (yours or others')

Review in this order — it front-loads what matters:

1. **Correctness:** does it do what it claims? Trace the main path and one failure path by hand.
2. **Safety:** input validation, injection, race conditions, resource leaks, secret handling.
3. **Blast radius:** what else calls this? What breaks if this throws/returns differently?
4. **Tests:** do they actually assert the new behavior, or just execute it?
5. Only then: style, naming, structure.

Review your own diffs with the same checklist before submitting — read the full `git diff`, not your memory of what you changed.

## Pre-submit checklist

- [ ] Full diff read line-by-line; every changed line is intentional
- [ ] Failing-then-passing test exists for the core change (or manual verification recorded)
- [ ] Existing tests run and passing
- [ ] No secrets, debug output, or dead code in the diff
- [ ] Unrelated issues noted in the report, not silently fixed
- [ ] Commit message explains *why*
