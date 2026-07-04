---
name: deep-research
description: Methodology for multi-source research tasks. Covers decomposing a question into sub-queries, triangulating across independent sources, scoring source credibility, maintaining citation discipline, deciding when to stop searching, and structuring the final research report. Use when a task requires gathering, verifying, and synthesizing information from the web or documents rather than answering from prior knowledge.
license: MIT
metadata:
  version: "2.0.0"
---

# Deep Research

Research quality is determined less by how much you read than by **how you decide what to trust and when to stop**. Follow this loop: decompose → search → triangulate → score → synthesize → cite.

## 1. Decompose the question

Before searching, split the objective into 3–7 answerable sub-questions. A good sub-question has a factual answer that could be wrong (falsifiable), not "learn about X."

Bad: "Research the EV market."
Good:
- What was global EV unit sales in the most recent full year, by region?
- Who are the top 5 manufacturers by units and by revenue?
- What are the 2–3 dominant forecasts for the next 5 years, and where do they disagree?

Write the sub-questions down first. They become your report's section headings and your stopping criterion.

## 2. Search in passes, not one deep dive

- **Pass 1 — landscape (broad):** 2–3 generic queries per sub-question. Goal: learn the vocabulary, key entities, and the shape of disagreement. Skim, don't read.
- **Pass 2 — targeted:** re-query using the precise terms, names, and report titles you learned in pass 1 (e.g., site-restricted queries, exact report names, `filetype:pdf`).
- **Pass 3 — adversarial:** explicitly search for contradicting evidence: "X criticism", "X debunked", "X methodology problems". If you skip this pass, you will confidently report the loudest claim, not the true one.

## 3. Triangulation rule

A claim is **confirmed** only when supported by ≥2 *independent* sources. Independence matters: ten articles that all cite the same press release count as one source. Trace claims to their origin — if every path leads to a single blog post, say so.

Label every material claim in your notes as one of:

| Label | Meaning |
|---|---|
| ✅ Confirmed | ≥2 independent sources agree |
| ⚠️ Single-source | Only one origin found — flag it in the report |
| ❌ Disputed | Credible sources disagree — report both sides with attribution |
| ❓ Unverifiable | Could not confirm — either omit or explicitly mark as unverified |

## 4. Credibility scoring

Quick heuristic (score each source 0–2 on each axis, ≥5 total is high credibility):

1. **Proximity** — primary (original data, filing, paper, announcement) = 2; reporting on primary = 1; aggregator/SEO content = 0.
2. **Incentive** — disinterested party = 2; industry analyst = 1; the entity selling the thing = 0.
3. **Recency & specificity** — dated, specific numbers with methodology = 2; vague or undated = 0.

Prefer one primary source over five secondary ones. When a secondary source cites a primary source, go read the primary source — numbers frequently mutate in transit.

## 5. Citation discipline

- Capture the URL, title, publisher, and date **at the moment you read it**, not at write-up time.
- Every number, quote, and non-obvious claim in the final report gets an inline citation.
- Never cite a search-results page or a homepage; cite the specific page containing the claim.
- Distinguish "Source X *reports*" from "it is the case that" — attribution is not endorsement.

## 6. When to stop

Stop searching when **any** of these holds:

- Every sub-question is Confirmed or explicitly marked Disputed/Unverifiable.
- The last 3 searches produced no new facts, only repetition (saturation).
- Remaining uncertainty wouldn't change the reader's decision (materiality test).
- You've hit the time/token budget — in which case report what's confirmed and list open questions honestly. An honest partial answer beats a padded complete-looking one.

## 7. Report format

Use the template in [references/report-template.md](references/report-template.md). Non-negotiables:

- **TL;DR first** — 3–5 bullets answering the original question directly.
- **Confidence labels** on key findings (confirmed / single-source / disputed).
- **Sources section** with dated links.
- **Open questions** section — what you could not verify and why.
