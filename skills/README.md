# Skills

Curated, self-contained skills that any agent can load to level up on a specific kind of work. Each skill is a folder with a `SKILL.md` playbook, plus optional `references/` (deep-dive material) and `scripts/` (runnable helpers).

## Index

| Skill | What it gives the agent | When to load |
|---|---|---|
| [deep-research](deep-research/) | Query decomposition, source triangulation, credibility scoring, citation discipline, stopping criteria | Any task requiring gathering and verifying information from the web or documents |
| [planning-and-decomposition](planning-and-decomposition/) | Turning fuzzy objectives into staged plans: todo structure, dependency ordering, checkpoints, replanning triggers | At the start of any multi-step task, and whenever reality diverges from plan |
| [self-verification](self-verification/) | The verify-before-submit loop: rubric review, empirical testing of claims/code/numbers, render-and-inspect, failure taxonomy | Before submitting **any** deliverable — arguably always |
| [code-quality](code-quality/) | Smallest useful change, read-before-write, targeted tests, defensive refactoring, commit hygiene | Whenever writing or reviewing code in a real codebase |
| [frontend-design](frontend-design/) | Committed aesthetic direction, typography/spacing systems, screenshot review loop; catalog of 8 design directions | Building any user-facing UI where visual quality matters |
| [report-writing](report-writing/) | TL;DR-first structure, evidence citation, tables vs. prose, tone calibration, length discipline | When the deliverable is a written document for busy readers |
| [web-data-extraction](web-data-extraction/) | Fetch→markdown pipelines, pagination, rate limiting, structured extraction, data validation; includes a reference fetcher script | Collecting data from websites, APIs, or feeds at non-trivial scale |
| [prompt-engineering](prompt-engineering/) | Delegation briefs, output schemas, few-shot selection, instruction hierarchies, degradation checks; includes a brief template | Spawning subagents or calling models inside pipelines |

**Suggested default load-out:** `planning-and-decomposition` + `self-verification` for every non-trivial task, plus whichever domain skill matches the work.

## The SKILL.md format

Skills follow [Anthropic's Agent Skills](https://docs.anthropic.com/en/docs/agents-and-tools/agent-skills) conventions:

```markdown
---
name: my-skill-name          # ≤64 chars, lowercase letters/numbers/hyphens
description: Third-person description of WHAT the skill does and WHEN to use it. ≤1024 chars.
---

# My Skill

Concise, actionable body (aim well under 3000 tokens)...
```

- **`name`** — matches the folder name; lowercase-hyphens only.
- **`description`** — the *only* thing an agent sees before deciding to load the skill, so it must state both what the skill does and when it applies. Written in third person.
- **Body** — the playbook itself: concrete procedures, rules, checklists. No fluff.

### Progressive disclosure

Skills are designed to be cheap to load and deep on demand, in three levels:

1. **Metadata** (`name` + `description`) — always visible; costs a few dozen tokens. The agent scans these to decide what's relevant.
2. **SKILL.md body** — loaded only when the skill is relevant; kept concise (<3000 tokens) so loading it never hurts.
3. **`references/` and `scripts/`** — linked from the SKILL.md and read/executed only when that specific depth is needed (templates, catalogs, taxonomies, runnable code).

The rule of thumb when writing: if a section is needed on *every* use of the skill, it belongs in SKILL.md; if it's needed on *some* uses, it belongs in `references/`; if it's executable, it belongs in `scripts/`.

## Adding your own skill

1. Create `skills/<skill-name>/SKILL.md` with the frontmatter above.
2. Write the body as instructions **to the agent** ("do X, check Y") — procedures and checklists, not essays.
3. Move anything long (templates, catalogs, worked examples) to `references/*.md` and link it from the body.
4. Put runnable helpers in `scripts/` with a usage comment at the top; standard-library-only where possible.
5. Keep it generic: no secrets, no company-specific paths, nothing that only works in one environment.
6. Test it: give the skill to a fresh agent on a real task and check whether the output measurably improves. If you can't tell the difference, sharpen the skill.

Then add a row to the index table above.
