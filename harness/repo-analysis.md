# Repo Analysis Protocol

When the owner says "analyse the repo" / "get context on the project", they mean **full onboarding, not a skim**. The failure mode this prevents: an agent reads the README plus two files, produces a plausible summary, and then makes decisions that contradict facts sitting in a handbook, a PDF, or a decisions log it never opened.

## The protocol

1. **Inventory before reading.** List *every* file first (`git ls-files` or a full tree), including binaries — PDFs, DOCX, XLSX, images. Note sizes and recency. Nothing is "probably irrelevant" until you know what it is.
2. **Entry documents first, completely.** README, any `handbook/`, `docs/`, `ORCHESTRATOR`/onboarding files, CONTRIBUTING, ROADMAP. Read them **start to finish — never head-truncated**: decisions logs, gotchas and corrections usually live at the bottom.
3. **Follow the reference graph.** Entry docs cite other files ("see X", "source of truth is Y"). Read what they point at. A file the handbook calls canonical outranks your inference from code.
4. **Open the binaries.** Extract text from PDFs/DOCX (e.g. pymupdf, python-docx) and read them — submitted proposals, signed letters, and specs are often *only* in binary form. If a binary can't be parsed, say so explicitly rather than skipping silently.
5. **Read the git metadata.** `git log` (what changed recently and why), branches, tags (`as-submitted`-style tags mark frozen states), open PRs. The history explains constraints the files alone don't.
6. **Extract, don't just summarise.** Produce: canonical facts (names, dates, numbers, IDs), decisions + rationale, constraints/invariants ("main must match submitted state"), open loops, and gotchas. Quote exact wording for anything that will be cited downstream.
7. **Label the digest.** Every claim in the output is **VERIFIED** (you read it in a file — cite the path) or **ASSUMED** (inference). Unread files get listed as unread, not absorbed into vibes.

## Delegation shape

For large repos, fan out readers by directory/file-type with disjoint scopes, each returning the §6 extraction for its slice; the orchestrator merges and resolves conflicts (a conflict between two files is a finding, not an annoyance). Budget: reading is cheap, re-doing work built on a wrong summary is not.

## Acceptance test

You are done when you can answer, with file citations: What is this project? What state is it in right now? What must never be changed, and why? What are the open loops? What would surprise a newcomer? If any answer is a guess, the analysis isn't finished.
