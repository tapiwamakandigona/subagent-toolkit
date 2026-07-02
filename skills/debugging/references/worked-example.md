# Worked Example: A Debugging Session, Annotated

A realistic end-to-end session showing the method from `SKILL.md` applied. The bug is fictional but the shape is the most common one agents face: wrong output, no crash, unfamiliar codebase.

## The report

> "The weekly usage report emailed to customers shows 0 active users for some accounts since last Tuesday. Not all accounts — maybe 10%."

## Step 1 — Reproduce (don't theorize yet)

Resist the urge to grep for "active users" and start reading. First: make it fail on demand.

```
$ python -m reports.weekly --account acme-corp --date 2024-03-12
active_users: 0        # confirmed failing
$ python -m reports.weekly --account acme-corp --date 2024-03-01
active_users: 412      # confirmed working before Tuesday
```

Two commands, and we have: a reproduction, a last-known-good, and a first-known-bad. Saved as `repro.sh`.

**Experiment log started:**

| # | Hypothesis | Test | Result |
|---|---|---|---|
| — | (reproduction) | acme-corp @ 03-12 vs 03-01 | fails / passes |

## Step 2 — Read the actual output, not just the number

Run with verbose logging. No exception anywhere — the pipeline "succeeds" with 0. So this is a data-flow bug, not a crash: the error's *origin* is upstream of wherever 0 is computed.

## Step 3 — Bisect the axis that varies

Three candidate axes: **time** (broke Tuesday), **account** (only ~10% affected), **code** (was there a deploy?).

`git log --since=2024-03-04` shows a deploy Monday night containing a refactor of `usage/aggregate.py`. Time axis and code axis point at the same event — promising but not proof.

Account axis: pull 5 affected + 5 unaffected account IDs. Affected accounts all have >100k events/week; unaffected are smaller. **A size-correlated failure suggests pagination or a limit.**

| # | Hypothesis | Test | Result |
|---|---|---|---|
| 1 | Monday's refactor broke aggregation for large accounts | checkout pre-deploy commit, run repro | **passes** → regression confirmed in that deploy |

## Step 4 — Instrument the suspect boundary

The refactor moved event-fetching to a new `fetch_events()` helper. Log its output size at the boundary:

```python
events = fetch_events(account, week)
log.warning("DBG: account=%s events=%d", account.id, len(events))  # DBG: tag for cleanup grep
```

```
DBG: account=acme-corp events=10000
```

Exactly 10,000 — a suspiciously round number. Read `fetch_events`: it calls the events API with `limit=10000` and **no pagination loop**. The old code paginated. Large accounts get a truncated event list; downstream, the "active in last 7 days" filter happens to see only events older than the window (the API returns oldest-first) → 0 active users.

| # | Hypothesis | Test | Result |
|---|---|---|---|
| 2 | `fetch_events` truncates at 10k, oldest-first | log len(events); read API docs for ordering | confirmed: exactly 10000, oldest-first |

Note what instrumentation did here: the hypothesis "aggregation math is wrong" died without ever being tested, because the *value* (`len(events)`) was wrong before the math ran. Logging actual values beats reading the math.

## Step 5 — Fix the cause, not the symptom

- Symptom patch (rejected): "if active_users == 0 for a large account, fall back to old code."
- Cause fix: restore pagination in `fetch_events`, following the cursor until exhausted.

## Step 6 — Verify mechanically

1. `repro.sh` before fix: `active_users: 0` ❌ → after fix: `active_users: 397` ✅ (cross-checked against the pre-deploy commit's output for the same week: 397 ✓)
2. Existing test suite: passes.
3. New regression test: `fetch_events` against a mock API serving 25k events across 3 pages → asserts all 25k returned.
4. "Where else?": grep for other callers of the same API client — one more call site with the same missing loop, **noted in the report as out of scope, not silently fixed** (per code-quality).
5. `grep -rn "DBG:"` → instrumentation removed.

## The shape to copy

1. Reproduction + last-known-good **before any theory** (5 minutes, saved hours).
2. Bisect on the axis that varies; converging axes (time + code) = high-value clue.
3. A size-correlated failure pattern → limits/pagination as the prior.
4. Instrument the boundary; let a concrete value (`10000`) kill the wrong hypothesis.
5. Experiment log kept; it became the report's method section verbatim.
6. Cause fixed, fix verified against the reproduction, sibling bug reported not smuggled.
