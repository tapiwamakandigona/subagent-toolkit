# Handoff Report

The standard shape for a subagent's final report to its orchestrator. A uniform report format lets the orchestrator scan, compare, and verify many subagent results quickly — and forces the subagent to separate *what it did* from *what it merely believes*. Every report also emits a machine-readable `report.json` sidecar so orchestrators can triage a swarm programmatically.

## Usage notes

- The report is for a reader with **no access to your working memory** — only paths, commands, and artifacts survive the handoff. Anything not written here is lost.
- **Composing with a role:** if you were assigned a role from `../agents/`, its "Report format" is the *content* of Section 1 (RESULT); this template is the envelope around it. On any other conflict, precedence is: orchestrator objective > role file > prompt templates > skills.
- Run `pre-submit-gate.md` before writing the report; the gate produces the EVIDENCE section's contents.
- **IMPLICIT DECISIONS is mandatory, not optional.** Every action embeds choices the brief didn't specify — style, interpretation, edge-case handling. Unstated, they are exactly the information the next agent lacks and the source of "conflicting decisions" failures; state them.
- **EVIDENCE backs every completion claim.** Orchestrators reject bare assertions: a claim with no proof artifact is treated as unverified.
- Cite paths; don't paste large content. The orchestrator can open files.
- Section 7 (Caveats) is the most valuable section and the most often skipped. An empty caveats section from a nontrivial task is a red flag, not a good sign.
- Keep it under ~400 words for routine tasks; scale up only with genuine complexity. Role formats that mandate tables or per-finding detail (reviewer, researcher) legitimately run longer — keep the envelope lean and let RESULT carry the role's detail.

## Template

```text
TASK: {{one_line_restatement}}
STATUS: {{complete | partial | blocked | failed}}

1. RESULT
   {{the_answer_or_artifact — 1-4 sentences leading with the outcome}}
   Artifacts: {{file_paths_or_locations, one per line}}

2. WHAT I DID
   {{3-8 bullets: key actions, in substance not chronology}}

3. IMPLICIT DECISIONS
   {{choices the brief didn't specify: style, interpretation, edge-case
   handling — one line each with the reason. "None" is almost never true.}}

4. VERIFICATION
   {{exact commands/checks run and their results — "pytest: 42 passed",
   "rendered and inspected page at 1280px". Label each claim VERIFIED
   (you observed it) or ASSUMED (you didn't).}}

5. EVIDENCE
   {{proof-artifact path for every completion claim: test output, logs,
   screenshots, rendered files. A claim without an evidence path is ASSUMED.}}

6. SCOPE NOTES
   Paths touched: {{list — flag anything outside your owned paths}}
   Not done (and why): {{descoped_or_discovered_but_out_of_scope_items}}

7. CAVEATS & RISKS
   {{what could be wrong, what you couldn't verify, what breaks first,
   assumptions that — if false — invalidate the result}}

8. SUGGESTED NEXT STEPS (optional)
   {{only if a concrete cheap step would materially help; not a wish list}}
```

## JSON sidecar: report.json

Write a `report.json` next to your report (in your run trace directory), matching `../harness/schemas/handoff.schema.json`. The exact top-level shape:

```text
{"run_id": str, "agent": str, "status": "complete|partial|blocked|failed", "artifacts": [str], "verified": [str], "assumed": [str], "implicit_decisions": [str], "evidence": [str], "notes": str}
```

Required fields: `run_id`, `agent`, `status`, `artifacts`. The rest mirror the report sections above (VERIFICATION splits into `verified`/`assumed`); `notes` is a one-line free-text summary. Orchestrators can validate sidecars mechanically with `../harness/scripts/check_contract.py`.

**`artifacts` and `evidence` entries must be plain filesystem paths** — nothing else. `check_contract.py` resolves each entry as a path and fails it otherwise, so no annotations (`"out.txt (12 passed)"`), no commands (`"git log feat/x"`), no descriptions (`"branch feat/x @ abc123"`). Annotated claims and commands belong in `verified`; branch/commit identifiers belong in `notes` or the prose report. If evidence is a command's output, write the output to a file and list that path.

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

3. IMPLICIT DECISIONS
   - Left the legacy TSV path untouched (separate code path, not in brief)
   - Quoted all fields rather than minimal quoting — matches Excel's tolerance

4. VERIFICATION
   VERIFIED: pytest tests/test_csv_writer.py — 14 passed (3 new regression tests)
   ASSUMED: Excel import behavior (no Excel here; round-tripped via python csv reader)

5. EVIDENCE
   runs/2026-07-04-csv/code-worker-1/pytest-output.txt (14 passed)
   runs/2026-07-04-csv/code-worker-1/roundtrip-samples.txt (3/3 match)

6. SCOPE NOTES
   Paths touched: src/export/csv_writer.py, tests/test_csv_writer.py (both owned)
   Not done: TSV path has the same bug (out of scope — flagged below)

7. CAVEATS & RISKS
   TSV export (src/export/tsv_writer.py) shares the buggy splitter; will bite next.

8. SUGGESTED NEXT STEPS
   One-line fix + test in tsv_writer.py; ~30 min for whoever owns it.
```

Matching sidecar:

```text
{"run_id": "2026-07-04-csv", "agent": "code-worker-1", "status": "complete",
 "artifacts": ["src/export/csv_writer.py", "tests/test_csv_writer.py"],
 "verified": ["pytest tests/test_csv_writer.py: 14 passed"],
 "assumed": ["Excel import behavior"],
 "implicit_decisions": ["legacy TSV path untouched", "quote-all fields"],
 "evidence": ["runs/2026-07-04-csv/code-worker-1/pytest-output.txt"],
 "notes": "CSV multiline fix verified; TSV path shares the bug, flagged."}
```

## Anti-patterns

- **Narrative instead of report** — a chronological story of your run buries the result. Lead with the outcome.
- **"Everything works"** — verification claims without commands and outputs are assertions, not evidence; orchestrators bounce them.
- **"No implicit decisions"** — you interpreted something; the next agent inherits your interpretation either way, so write it down.
- **Silent scope changes** — descoping is often correct; hiding it never is.
- **Pasting file contents** — bloats the orchestrator's context; that's what paths are for.
