# Handoff Report

The standard shape for a subagent's final report to its orchestrator. A uniform report format lets the orchestrator scan, compare, and verify many subagent results quickly — and forces the subagent to separate *what it did* from *what it merely believes*.

## Usage notes

- The report is for a reader with **no access to your working memory** — only paths, commands, and artifacts survive the handoff. Anything not written here is lost.
- Cite paths; don't paste large content. The orchestrator can open files.
- Section 5 (Caveats) is the most valuable section and the most often skipped. An empty caveats section from a nontrivial task is a red flag, not a good sign.
- Keep it under ~400 words for routine tasks; scale up only with genuine complexity.

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

## Anti-patterns

- **Narrative instead of report** — a chronological story of your run buries the result. Lead with the outcome.
- **"Everything works"** — verification claims without commands and outputs are assertions, not evidence.
- **Silent scope changes** — descoping is often correct; hiding it never is.
- **Pasting file contents** — bloats the orchestrator's context; that's what paths are for.
