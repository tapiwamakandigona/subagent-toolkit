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
| [data-analysis](data-analysis/) | Sanity-checking data before analysis, reproducible analysis scripts, honest aggregation (denominators, baselines, Simpson's paradox), chart-vs-table decisions | Computing numbers, statistics, or trends from tabular data |
| [debugging](debugging/) | Reproduce-first discipline, reading the real error, bisection, instrumenting over guessing, one-hypothesis-at-a-time, stop-and-report criteria | Investigating any failure: bugs, failing tests, wrong output, regressions |
| [api-integration](api-integration/) | Docs/spec-first workflow, auth without secret leaks, pagination and rate limits, write idempotency, retryable-vs-not error taxonomy, sandbox-first testing, webhooks | Calling or building against any third-party HTTP API |
| [document-handling](document-handling/) | Library selection per format/operation, template-based generation, styles over inline formatting, mandatory render-and-inspect loop, per-format gotchas | Producing or editing docx, xlsx, pptx, or PDF deliverables |
| [security-review](security-review/) | Untrusted-data tracing, secret handling, injection classes (SQL/shell/path/prompt), authn vs authz, dependency risk, unsafe deserialization; full checklist | Reviewing code, configs, or agent pipelines for security issues |
| [repo-conventions-discovery](repo-conventions-discovery/) | The "read the agent doc first" protocol: locating AGENTS.md/AI_CONTEXT.md/plans.md-style docs, extracting machine-checkable constraints, following commit/branch conventions, updating state docs after shipping | Before editing any repo you did not create in this session |
| [buildless-web-verify](buildless-web-verify/) | Local-server + headless-Chromium smoke harness (console capture, window-global test hooks, JSON verdicts), no-build-step pre-handoff check, GitHub Pages verbatim-upload gotchas, honest perf-claim labeling | Modifying or verifying buildless browser apps/games served as static files |
| [static-export-webapp](static-export-webapp/) | What static export forbids, public env-var matrix, lint→tests→build→serve→smoke chain (incl. money-logic parity tests), read-bundled-docs rule, security-review gate, Capacitor APK variant | Building or modifying framework apps that ship as a static out/ directory |
| [static-site-qa](static-site-qa/) | Serve-and-screenshot at mobile+desktop breakpoints, link/HTML validation, SEO surface (sitemap, robots, og, JSON-LD), directory-per-page consistency, post-deploy live-URL check | Before merging or deploying changes to hand-rolled static sites |
| [appwrite-platform](appwrite-platform/) | Sites tar→POST→poll-to-ready deploys, Functions tested in isolation, mobile OAuth deep-link scheme pitfalls, identifier-vs-secret hygiene, respecting local-key-file deploy styles | Any task deploying to or building on Appwrite Sites, Functions, or Auth |

**Suggested default load-out:** `planning-and-decomposition` + `self-verification` for every non-trivial task, plus whichever domain skill matches the work.

## The SKILL.md format

Skills follow [Anthropic's Agent Skills](https://docs.anthropic.com/en/docs/agents-and-tools/agent-skills) conventions:

```markdown
---
name: my-skill-name          # ≤64 chars, lowercase letters/numbers/hyphens
description: Third-person description of WHAT the skill does and WHEN to use it. ≤1024 chars.
license: MIT
metadata:
  version: "1.1.0"
---

# My Skill

Concise, actionable body (under ~3,000 tokens)...
```

- **`name`** — matches the folder name; lowercase-hyphens only.
- **`description`** — the *only* thing an agent sees before deciding to load the skill, so it must state both what the skill does and when it applies. Written in third person.
- **`license`** — SPDX identifier; `MIT` for everything in this repo.
- **`metadata.version`** — quoted semver string, two-space indented under `metadata:`. Bump it when the skill's content changes materially.
- Optional fields per the Agent Skills spec: **`compatibility`** (environment requirements — intended tools/products, needed system packages or network access; only add it when the skill genuinely doesn't work everywhere) and **`allowed-tools`** (restricts which tools a Claude Code agent may use while the skill is active).
- **Body** — the playbook itself: concrete procedures, rules, checklists. No fluff.

### Progressive disclosure

Skills are designed to be cheap to load and deep on demand, in three levels:

1. **Metadata** (`name` + `description`) — always visible; costs a few dozen tokens. The agent scans these to decide what's relevant.
2. **SKILL.md body** — loaded only when the skill is relevant; kept under ~3,000 tokens so loading it never hurts.
3. **`references/` and `scripts/`** — linked from the SKILL.md and read/executed only when that specific depth is needed (templates, catalogs, taxonomies, runnable code).

The rule of thumb when writing: if a section is needed on *every* use of the skill, it belongs in SKILL.md; if it's needed on *some* uses, it belongs in `references/`; if it's executable, it belongs in `scripts/`.

## Evals

Each skill may ship `skills/<name>/evals/evals.json` — deterministic test cases that check whether an agent *using the skill* produces answers with the properties the skill teaches. Schema:

```json
{
  "skill": "<name>",
  "cases": [
    {
      "id": "<slug>",
      "prompt": "<task prompt exercising the skill>",
      "checks": [
        {"type": "contains", "value": "<substring the answer must include>"},
        {"type": "regex",    "value": "<pattern the answer must match>"},
        {"type": "not_contains", "value": "<substring the answer must avoid>"}
      ]
    }
  ]
}
```

Conventions:

- **5–8 cases per skill**, each targeting one distinct behavior the skill teaches.
- Checks must be **deterministic** — substring/regex assertions on properties any competent with-skill answer exhibits (e.g. the debugging skill's answers mention *reproducing* before theorizing), never on exact wording.
- `check.type` is one of `contains`, `regex` (case-insensitivity via inline `(?i)`), or `not_contains`.
- To use them: run each `prompt` against an agent with and without the skill loaded, apply the checks to both answers, and compare pass rates. The with-skill run should dominate; if it doesn't, sharpen the skill or the checks.

## Adding your own skill

1. Create `skills/<skill-name>/SKILL.md` with the frontmatter above.
2. Write the body as instructions **to the agent** ("do X, check Y") — procedures and checklists, not essays.
3. Move anything long (templates, catalogs, worked examples) to `references/*.md` and link it from the body.
4. Put runnable helpers in `scripts/` with a usage comment at the top; standard-library-only where possible.
5. Keep it generic: no secrets, no company-specific paths, nothing that only works in one environment.
6. Test it: give the skill to a fresh agent on a real task and check whether the output measurably improves. If you can't tell the difference, sharpen the skill.
7. Add `evals/evals.json` per the schema above so the improvement stays checkable.

Then add a row to the index table above.
