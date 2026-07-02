---
name: report-writing
description: Produces executive-quality written deliverables. Covers TL;DR-first structure, citing evidence for claims, choosing tables versus prose, calibrating tone to the audience, and length discipline. Use when the deliverable is a written document — status updates, research summaries, analyses, memos, or recommendations — read by busy people.
license: MIT
metadata:
  version: "1.1.0"
---

# Report Writing

The reader is busy, skeptical, and will decide within ten seconds whether to read past the first paragraph. Write for that reader.

## 1. TL;DR first, always

Open with 3–5 bullets that a reader could act on **without reading anything else**:

- Lead with the answer/recommendation, not the background. "Migrate to X; it cuts costs ~40% with two days of work" — not "This report examines options for…"
- Include the one number that matters and the one caveat that matters.
- If the reader must do something, the ask is in the TL;DR, bolded, with a deadline.

Write the TL;DR **last**, place it first. If you can't compress your findings into five bullets, you don't understand them yet.

## 2. Structure: inverted pyramid

Order sections by decision-relevance, not by the order you did the work:

```
TL;DR → Recommendation / Answer → Key findings (with evidence)
→ Details & analysis → Method / caveats → Appendix
```

- Each section should survive the reader stopping after it.
- Headings carry content: "Costs drop 40% under Option B", not "Analysis".
- Never narrate your process ("First I searched for… then I found…") except in a Method appendix. The reader buys the building, not the scaffolding.

## 3. Evidence discipline

- Every material claim carries its evidence inline: a number, a citation, a link, a test result. "Latency improved significantly" → "p95 latency fell 340ms → 120ms (load test, 2024-03-15)."
- Distinguish observation ("the logs show X"), inference ("which suggests Y"), and opinion ("I recommend Z"). Blurring these three is how reports lose trust.
- State confidence honestly: *confirmed / likely / uncertain*. A report that flags its own weak points reads as more credible, not less.
- Numbers get units, dates, and sources. Comparisons get baselines ("40% cheaper *than what*?").

## 4. Tables vs. prose

- **Table** when the reader will compare ≥3 items across ≥2 attributes, or scan for their own row. Options analyses, before/after, status-by-workstream: always tables.
- **Prose** for causality, narrative, nuance, and recommendation rationale — tables can't say "because."
- **Bullets** for parallel independent points; never nest more than two levels.
- Tables need takeaways: one sentence above or below saying what the table shows ("Option B dominates on every axis except setup time"). Never make the reader derive the conclusion.
- Charts only when shape matters (trends, distributions). A 3-number comparison is a sentence, not a chart.

## 5. Tone calibration

Match three dials to the audience:

| Dial | Executive | Peer/practitioner | External/formal |
|---|---|---|---|
| Detail | Conclusions + one supporting layer | Full reasoning, edge cases | Complete but guarded |
| Hedging | Minimal — decide, then caveat | Explicit uncertainties | Precise, legally careful |
| Vocabulary | No jargon without payoff | Domain terms fine | Define terms on first use |

Universal rules: active voice; verbs over nominalizations ("we decided" not "a decision was made"); no filler ("It is worth noting that…" — if it's worth noting, note it); confidence proportional to evidence.

## 6. Length discipline

- Default ceiling: **one page / ~400 words** for status and decision documents; research reports 1–3 pages plus appendix. Exceed only when the reader asked for depth.
- Cut in this order: process narration → restated context the reader already knows → adjectives → redundant examples → hedging chains ("possibly might potentially").
- The appendix is where length goes to be optional. Anything the primary reader doesn't need to decide moves there.
- Editing pass targeting **−20% words** improves nearly any draft. Do it every time.

## Pre-submit checklist

- [ ] TL;DR readable standalone; contains the answer and the ask
- [ ] Every number has a unit, date, and source; every claim has evidence
- [ ] Section headings state findings, not topics
- [ ] Comparisons are tables with a stated takeaway
- [ ] Tone matches the named audience
- [ ] One −20% editing pass completed
- [ ] Read once end-to-end for internal contradictions

*Related repo asset: for subagent→orchestrator handoff reports specifically, [`prompts/handoff-report.md`](../../prompts/handoff-report.md) defines the standard shape — keep the two consistent.*
