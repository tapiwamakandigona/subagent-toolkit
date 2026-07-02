# Verification Loop

Template for verifying a claimed result independently of how it was produced — and looping until it actually holds. Use whenever correctness matters more than speed: pre-merge, pre-delivery, or after any subagent reports "done". The core rule: **verification must not reuse the producer's reasoning.** Re-running the producer's own checks only confirms the producer agrees with itself.

## Usage notes

- Run this as the producer (before handoff), as an orchestrator (on a subagent's report), or as a dedicated reviewer agent.
- Derive checks from the **brief/requirements**, never from the artifact — the artifact may have quietly redefined the goal.
- Cap the loop (`{{max_iterations}}`, usually 2–3). A loop that isn't converging means the approach is wrong; escalate instead of iterating forever.

## Template

```text
Claim under test: {{what_is_claimed_to_be_done}}
Source of truth: {{the_brief_or_requirements — NOT the artifact}}

LOOP (max {{max_iterations}} iterations):

1. DERIVE CHECKS from the source of truth:
   - one check per requirement / definition-of-done item
   - at least one NEGATIVE check (an input or condition where the artifact
     should fail, refuse, or handle an error — verify it does)
   - at least one check the producer probably didn't try (unusual input,
     different environment, downstream consumer's perspective)

2. EXECUTE every check by direct observation:
   - run the command / open the file / render the page / re-fetch the source
   - record: check → expected → observed → PASS/FAIL
   - a check you couldn't execute is UNVERIFIED, not passed

3. EVALUATE:
   - all PASS → exit loop, report VERIFIED (attach the check table)
   - any FAIL → diagnose root cause (not just symptom), fix (or send back to
     producer with the failing check), then RE-RUN ALL checks — fixes regress
     other checks more often than expected

4. If iteration budget exhausted with failures remaining:
   report NOT VERIFIED with the failing checks and your root-cause hypothesis.
   Do not soften this to "mostly working".

Output: verdict (VERIFIED / NOT VERIFIED) + check table + unverified items.
```

## Anti-patterns

- **Testing the artifact against itself** — deriving checks from what the code does, rather than what was asked.
- **Partial re-runs after a fix** — the fix that breaks a previously passing check is a classic.
- **Happy-path-only checks** — negative checks catch a disproportionate share of real defects.
- **Verification by re-reading** — reading code or prose and nodding is review, not verification; observation requires execution.
