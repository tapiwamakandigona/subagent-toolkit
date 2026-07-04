---
name: self-verification
description: The verify-before-submit loop for agent output. Covers rubric-based self-review, empirically testing your own claims, code, and numbers, render-and-inspect verification for visual artifacts, and a taxonomy of the most common agent failure modes to check against. Use before submitting any deliverable — code, reports, data, documents, or UI — especially when no human will review intermediate steps.
license: MIT
metadata:
  version: "2.0.0"
---

# Self-Verification

The single highest-leverage habit for an agent: **never submit output you haven't checked the way a skeptical reviewer would.** You are the last line of defense; assume there is no human review after you.

## The core loop

```
produce → step back → verify empirically → fix → re-verify → submit
```

"Step back" is literal: re-read the original request, then review your output *as if someone else wrote it*. The mental shift from author to reviewer catches a large share of errors on its own.

## 1. Rubric self-review

Before submitting, score your output against an explicit rubric. Default rubric (adapt per task):

| Criterion | Question | Pass? |
|---|---|---|
| Completeness | Does it address **every** part of the request, including sub-clauses? | |
| Correctness | Is every claim/number/behavior verified, not just plausible? | |
| Instructions | Were all format/length/tool/constraint instructions followed? | |
| Evidence | Can I point to where each key claim was checked? | |
| Usability | Can the recipient act on this without asking follow-ups? | |

Re-reading the original request at review time is essential — long tasks drift, and the most common failure is answering a *nearby* question, not the asked one.

## 2. Test your own claims, code, and numbers

Verification must be **empirical**, not "it looks right":

- **Code:** run it. Run the tests. If no tests exist, write a minimal one or execute the changed path by hand. "It compiles" is not verification. Check the *unchanged* behavior too (regression).
- **Numbers:** recompute at least the headline figures independently (different method or a quick script). Check units, orders of magnitude, and that percentages/totals are internally consistent (do the rows sum to the total?).
- **Factual claims:** for each load-bearing claim, ask "where exactly did I learn this?" If the answer is "I just know," verify it or hedge it explicitly.
- **File operations:** after writing/moving/deleting files, list the directory or re-read the file. Confirm the side effect actually happened.
- **Commands and links:** every command and URL you tell someone to use, you have run/opened yourself.

Rule of thumb: verification should consume **10–20% of total task effort**. If it consumed 0%, the task isn't done.

## 3. Render-and-inspect (visual output)

Anything visual — HTML, PDFs, slides, charts, generated documents — must be **rendered and looked at**, not inferred from source:

1. Render to the final format (screenshot the page, export the PDF, open the image).
2. Inspect at actual size for: clipped/overflowing text, overlapping elements, broken images, wrong fonts, empty sections, pagination breaks, unreadable contrast.
3. Check the *worst case*: longest data row, smallest viewport, page 2 of the PDF — defects hide off the happy path.
4. Fix and re-render. Never ship a visual artifact you haven't seen.

## 4. Failure taxonomy

Check output against the common failure modes in [references/failure-taxonomy.md](references/failure-taxonomy.md). Top five by frequency:

1. **Partial completion** — did 4 of 5 requested things, reported success.
2. **Plausible fabrication** — invented a number, API, filename, or citation that "sounds right."
3. **Untested happy path** — code/logic works for the demo input, breaks on edge cases.
4. **Instruction drift** — format/length/constraint stated early in the task, forgotten by the end.
5. **Stale-state assumption** — verified something once, changed things after, never re-verified.

## 5. When you find a problem

- Fix it, then **re-run the full check** — fixes introduce regressions.
- If it's unfixable within budget, disclose it prominently rather than hiding it. A flagged limitation preserves trust; a discovered one destroys it.
- Track your own repeated failure modes; check those first next time.

## What verification is not

- Not re-reading your output and nodding.
- Not "the tool returned success" (check the actual artifact).
- Not restating confidence in stronger words. Confidence must come from evidence you can point to.

*Related repo asset: [`prompts/self-review-rubric.md`](../../prompts/self-review-rubric.md) is the fill-in template version of the §1 rubric — keep the two consistent.*
