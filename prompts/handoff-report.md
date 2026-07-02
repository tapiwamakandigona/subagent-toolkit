# Handoff Report

The standard shape for a subagent's final report to its orchestrator. A uniform report format lets the orchestrator scan, compare, and verify many subagent results quickly — and forces the subagent to separate *what it did* from *what it merely believes*.

## Usage notes

- The report is for a reader with **no access to your working memory** — only paths, commands, and artifacts survive the handoff. Anything not written here is lost.
- **Composing with a role:** if you were assigned a role from `../agents/`, its "Report format" is the *content* of Section 1 (RESULT); this template is the envelope around it. On any other conflict, precedence is: orchestrator objective > role file > prompt templates > skills.
- Cite paths; don't paste large content. The orchestrator can open files.
- Section 5 (Caveats) is the most valuable section and the most often skipped. An empty caveats section from a nontrivial task is a red flag, not a good sign.
- Keep it under ~400 words for routine tasks; scale up only with genuine complexity. Role formats that mandate tables or per-finding detail (reviewer, researcher) legitimately run longer — keep the envelope lean and let RESULT carry the role's detail.

## Template

```text
TASK: {{one_line_restatement}}
STATUS: {{complete | partial | blocked}}

1. RESULT
   {{the_answer_or_artifact — 1-4 sentences leading with the outcome}}
   Artifacts: {{file_paths_or_locations, one per line}}

2. WHAT I DID
   {{3-8 bullets: key actions and decisions, including judgment calls the
   brief didn't cover and why you made them}}

3. VERIFICATION
   {{exact commands/checks run and their results — "pytest: 42 passed",
   "rendered and inspected page at 1280px", "cross-checked figure against
   source X". Distinguish VERIFIED claims from ASSUMED ones.}}

4. SCOPE NOTES
   Paths touched: {{list — flag anything outside your owned paths}}
   Not done (and why): {{descoped_or_discovered_but_out_of_scope_items}}

5. CAVEATS & RISKS
   {{what could be wrong, what you couldn't verify, what breaks first,
   assumptions that — if false — invalidate the result}}

6. SUGGESTED NEXT STEPS (optional)
   {{only if a concrete cheap step would materially help; not a wish list}}
```

### Example (filled)

```text
TASK: Fix the CSV export dropping rows with embedded newlines (#412)
STATUS: complete

1. RESULT
   Export now quotes multiline fields correctly; all 3 reported samples round-trip.
   Artifacts: src/export/csv_writer.py, tests/test_csv_writer.py

2. WHAT I DID
   - Root-caused to a hand-rolled line splitter; replaced with stdlib csv.writer
   - Kept the existing delimiter config; no API change
   - Judgment call: left the legacy TSV path untouched (separate code path, not in brief)

3. VERIFICATION
   VERIFIED: pytest tests/test_csv_writer.py — 14 passed (3 new regression tests)
   ASSUMED: Excel import behavior (no Excel here; round-tripped via python csv reader)

4. SCOPE NOTES
   Paths touched: src/export/csv_writer.py, tests/test_csv_writer.py (both owned)
   Not done: TSV path has the same bug (out of scope — flagged below)

5. CAVEATS & RISKS
   TSV export (src/export/tsv_writer.py) shares the buggy splitter; will bite next.

6. SUGGESTED NEXT STEPS
   One-line fix + test in tsv_writer.py; ~30 min for whoever owns it.
```

## Anti-patterns

- **Narrative instead of report** — a chronological story of your run buries the result. Lead with the outcome.
- **"Everything works"** — verification claims without commands and outputs are assertions, not evidence.
- **Silent scope changes** — descoping is often correct; hiding it never is.
- **Pasting file contents** — bloats the orchestrator's context; that's what paths are for.
