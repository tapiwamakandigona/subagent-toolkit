# Self-Review Rubric

A structured pass an agent runs on its own output **before** handing off. Self-review catches the cheap defects (omissions, unverified claims, scope drift) so human or reviewer-agent attention is spent on the expensive ones. It is weaker than independent review — use it in addition to, not instead of, a reviewer when stakes are high.

## Usage notes

- Run this as a **separate pass** after you believe you're done, not interleaved with production. Fresh eyes, even your own, need distance.
- Answer every item in writing with evidence (a path, a command output, a quote), not with "yes". An unevidenced ✅ is a ❌.
- Append the filled rubric to your handoff report.

## Template

```text
Self-review of: {{artifact_or_task}}
Definition of done (from the brief): {{criteria}}

1. COMPLETENESS
   For each item in the definition of done: met / partial / missing, with the
   evidence path. Then: what did the brief imply but not state, and did I cover it?

2. CORRECTNESS
   - What did I actually run/render/test, and what were the results?
     (exact commands and outputs, not "tests pass")
   - What is the single claim in my output most likely to be wrong? Re-verify
     that one now.

3. SCOPE
   - Did I touch only my owned paths? (list any exceptions)
   - Did I add anything not asked for? If so, is it justified in one sentence,
     or should it be removed?

4. CONSUMER TEST
   Read the deliverable as its intended consumer, cold. Can they use it without
   asking me anything? List every question they'd have to ask — each one is a
   defect; fix or address it in the report.

5. HYGIENE
   - Debug output, temp files, dead code, leftover {{placeholders}} removed?
   - Any secrets, tokens, or machine-specific paths in the output?

6. HONEST CAVEATS
   What would a hostile reviewer flag first? Either fix it now or state it
   plainly in the report — hidden weaknesses cost more than admitted ones.

Verdict: SHIP / FIX-FIRST (list the fixes, then re-run items they touch)
```

## Anti-patterns

- **Rubber-stamping** — filling the rubric with unevidenced yeses defeats its purpose entirely.
- **Fixing while reviewing** — note everything first, then fix; interleaving loses findings.
- **Skipping item 4** — the consumer test catches the most defects per minute of any item here.
