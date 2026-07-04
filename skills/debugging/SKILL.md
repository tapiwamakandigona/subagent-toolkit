---
name: debugging
description: A systematic procedure for finding out why something already broken is broken. Covers reproducing the failure before touching anything, reading the actual error instead of pattern-matching on it, bisecting across inputs/commits/config, instrumenting with logging instead of guessing, testing one hypothesis at a time, and knowing when to stop and report. Use when investigating any failure — a bug report, a failing test, a crashed pipeline, wrong output, or a regression.
license: MIT
metadata:
  version: "2.0.0"
---

# Debugging

Debugging fails in one dominant way: **fixing the code you suspect instead of the code that's broken.** Everything here forces evidence before edits.

## 1. Reproduce first — no reproduction, no debugging

- Get the failure to happen **on demand, in front of you**, before changing anything. A bug you can't reproduce is a bug you can't verify you've fixed; any "fix" is a guess shipped with confidence.
- Capture the reproduction as a runnable command or script the moment you have it — it's your test oracle for the rest of the session.
- Shrink it: cut the failing input/scenario in half repeatedly while the failure persists. A 5-line reproduction localizes the fault; a 5,000-line one hides it.
- If you genuinely can't reproduce (heisenbug, prod-only): switch goals from "fix" to "instrument" — add logging/assertions around the suspected region so the *next* occurrence yields evidence. Say so in your report.

## 2. Read the actual error

- Read the **entire** message and the **full** stack trace, bottom to top, before forming any theory. Agents pattern-match on the first familiar phrase and chase the wrong error; the real cause is often in a `caused by:` three frames down, or in the *first* error of a cascade, not the last.
- Distinguish the error's **location** from its **origin**: the frame that threw is where the invariant was noticed, not necessarily where it was violated. A `NoneType has no attribute` throw site is downstream of whoever produced the `None`.
- Check timestamps and versions: is this error from the run you think it's from? Stale logs, cached builds, and old deployments produce ghost-chasing. When in doubt, add a marker (`print("BUILD 7")`) and confirm you're executing the code you're editing — this single check kills a startling fraction of "impossible" debugging sessions.
- Unfamiliar error? Search the codebase for the message first (it may be a project-defined error with a known meaning), then the web.

## 3. Bisect the space

The fastest search through any failure space is binary. Pick the axis that varies:

- **Input:** does half the failing input still fail? Which half? Repeat.
- **Commit:** did it work before? `git bisect` between last-known-good and first-known-bad — mechanical, logarithmic, and immune to your theories. 1,000 commits is 10 tests.
- **Config/environment:** works on machine A, fails on B → diff the environments (versions, env vars, locale, data), then flip differences one at a time.
- **Code path:** disable half the pipeline (return early, stub a stage) to find which stage corrupts the data.

Bisection needs a **cheap, reliable failure check** — that's your §1 reproduction script.

## 4. Instrument, don't stare

- When reading code hasn't found it in ~10 minutes, stop reading and **make the program tell you**: log the actual values of the variables in your hypothesis at the suspect boundary. The bug is almost always "a value I was sure was X was actually Y."
- Log at boundaries: function entry/exit, before/after the suspect transformation, on both sides of a serialization or network hop. Include enough identity (IDs, lengths, types) to correlate lines.
- Prefer assertions to logs for invariants (`assert total >= 0, f"total={total} inputs={rows}"`): they fail at the first violation instead of scrolling past it.
- Remove or gate every instrumentation line before submitting — grep for your markers (use a distinctive tag like `DBG:` so cleanup is one search).

## 5. One hypothesis at a time

- Write the hypothesis down as a falsifiable sentence: *"The cache returns stale entries after a write — if true, disabling the cache makes the reproduction pass."* Then run exactly that experiment.
- **Change one thing per experiment.** Three simultaneous changes that "fix" it teach you nothing and usually smuggle in a regression. If you shotgunned in desperation, re-narrow: revert all, re-apply one at a time.
- Keep a short experiment log (hypothesis → test → result) in your notes. Two failed hypotheses without a log becomes circular re-testing of the same idea; the log is also the skeleton of your report.
- When a hypothesis dies, kill it fully — don't let "but it *might* still be the cache" drag you back without new evidence.

## 6. Fix the cause, verify the fix

- Distinguish **symptom patches** (catch the exception, add a null check) from **cause fixes** (stop producing the null). Patch symptoms only knowingly and say so in your report.
- Verification is mechanical because of §1: reproduction fails before the fix → passes after → the surrounding test suite still passes. All three, every time.
- Ask "where else?": the same wrong pattern usually has siblings. Grep for them; note them in the report even if out of scope.

## 7. When to stop and report

Stop debugging and write up when **any** of these hits:

- **Budget:** you've spent the time the fix is worth (default: escalate after ~3 dead hypotheses or 2× your initial estimate).
- **Access wall:** the evidence you need (prod logs, credentials, another team's system) is beyond your reach.
- **Blast radius:** the true fix requires changes outside your assigned scope.

A good stuck-report is a deliverable, not a failure: the reproduction script, what you ruled out (with evidence), the surviving hypotheses ranked, and the exact next experiment you'd run. That report saves the next debugger — possibly you — a full session. See [references/worked-example.md](references/worked-example.md) for a complete session transcript showing the method end-to-end.
