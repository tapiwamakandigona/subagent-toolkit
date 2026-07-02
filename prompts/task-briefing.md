# Task Briefing

Template for briefing a subagent. A good brief transfers everything the subagent cannot discover on its own and nothing it can. Most delegation failures are briefing failures: missing context, unstated constraints, or no definition of done.

## Usage notes

- Fill every placeholder or delete its line deliberately — a leftover `{{...}}` means you skipped a decision.
- **Context** is the highest-leverage section: include decisions already made, things already tried, and links/paths to source material. The subagent starts with zero memory of your thread.
- **Owned paths** is mandatory for any parallel fan-out (see `harness/patterns.md`).
- Keep the brief under ~500 words; move bulk material into files and reference the paths.

## Template

```text
ROLE: Adopt {{abilities_dir}}/agents/{{role}}.md as your operating role.

GOAL:
{{one_paragraph_goal — what to produce and for whom}}

DEFINITION OF DONE:
{{checkable_completion_criteria — bullet list; each item verifiable by inspection or command}}

CONTEXT YOU CANNOT INFER:
- Background: {{decisions_already_made, prior_attempts, why_this_task_exists}}
- Inputs: {{file_paths, URLs, data_locations}}
- Audience/consumer of the output: {{who_uses_the_result_and_how}}

CONSTRAINTS:
- Owned paths (you may create/edit ONLY these): {{path_list}}
- Do not: {{forbidden_actions — e.g., add dependencies, contact users, modify shared config}}
- Budget: {{time_or_effort_guidance, e.g., "timebox research to ~15 min"}}

QUALITY BAR:
{{2-4 specific bullets — what distinguishes acceptable from excellent here}}

REPORT:
Structure your final report per {{abilities_dir}}/prompts/handoff-report.md.
Cite file paths and commands; do not paste large file contents.
If blocked or if the correct fix requires paths you don't own, stop and report
rather than improvising.
```

## Anti-patterns

- **"Improve X"** — not a goal. State the observable difference between before and after.
- **Hidden acceptance criteria** — if you'll reject the result for missing tests, say "tests required" in the brief.
- **Context by osmosis** — "as discussed" means nothing to an agent that wasn't there.
- **Unbounded scope** — every brief needs a "do not" list and a budget, or diligent agents will gold-plate.
