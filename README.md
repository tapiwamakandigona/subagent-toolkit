# subagent-toolkit

**An ability pack for AI subagents.** Clone this repo at the start of a run and a bare agent instantly gains curated skills, focused role definitions, battle-tested prompt templates, and orchestration patterns — no fine-tuning, no plugins, just files the agent can read.

Works with any agent that can run `bash` and read files: Viktor subagents, Claude Code agents, or homegrown LLM orchestrators.

---

## Why ability packs work

A subagent starts every run with an empty working memory and whatever its orchestrator crammed into the objective. That's fragile. This repo turns three chronic weaknesses into strengths:

| Weakness | Fix | Where |
|---|---|---|
| **No memory** — the agent re-derives the same procedures every run, inconsistently | **Skills as memory.** Curated `SKILL.md` files encode proven procedures the agent loads on demand | [`skills/`](skills/) |
| **No focus** — a generalist prompt produces generalist output | **Roles as focus.** Drop-in system prompts that constrain an agent to one job with a concrete process and quality bar | [`agents/`](agents/) |
| **No process** — orchestrators improvise delegation and get unverifiable results | **Harnesses as process.** Named orchestration patterns (fan-out, pipeline, critic loop) with known failure modes, plus prompt templates for briefing and reporting | [`harness/`](harness/), [`prompts/`](prompts/) |

Everything follows **progressive disclosure**: index files are short, detail lives one hop away, and the agent only loads what the task needs. Context stays clean; capability stays deep.

## Quickstart

Clone, inspect, run — you're about to inject this repo into an agent's context, so look at it first:

```bash
git clone --depth 1 https://github.com/tapiwamakandigona/subagent-toolkit.git ./.abilities
sh ./.abilities/bootstrap.sh
```

If you've already vetted a release, the pinned one-liner:

```bash
curl -fsSL https://raw.githubusercontent.com/tapiwamakandigona/subagent-toolkit/v1.1.0/bootstrap.sh | ABILITIES_REF=v1.1.0 sh
```

(Piping an unpinned `main` to `sh` also works, but you're trusting whatever the branch says today.)

`bootstrap.sh` clones/updates the repo into `./.abilities` (override with the first argument or `$ABILITIES_DIR`), prints a manifest of every skill, role, and prompt it found, and emits a **context primer** — a ready-to-paste block that tells the agent what it now has and how to load more detail on demand. When run from inside an existing checkout (as above), it uses that checkout in place — the primer's paths then point at the checkout, not `./.abilities`.

### Pinning a version

The pack's files become part of your agents' effective system prompt — in production fan-outs, pin them so every subagent gets identical, vetted instructions:

- `ABILITIES_REF=<tag|branch|commit>` — bootstrap checks out exactly this ref after cloning (e.g. `ABILITIES_REF=v2.1.0`). Refs that resolve locally are checked out with **no network access**, so pinned fan-outs stay frozen and fast even offline.
- `ABILITIES_NO_UPDATE=1` — skip the auto-`git pull` on an existing checkout, so instructions can't change mid-run.

Pin **tags or commit SHAs** for reproducibility — a branch ref is a moving target, not a pin. Unpinned, bootstrap tracks `main` and updates on every run — fine for exploration, not for reproducible orchestration.

## Repo layout

```
subagent-toolkit/
├── README.md            ← you are here
├── CHANGELOG.md         ← release notes (Keep a Changelog format)
├── bootstrap.sh         ← installer + manifest + context primer
├── .claude-plugin/      ← Claude Code plugin/marketplace manifest
├── .github/             ← CI workflow (lint, tests, smoke tests)
├── skills/              ← Agent Skills (Anthropic conventions): one folder per
│   │                      skill, each with SKILL.md (frontmatter: name,
│   │                      description), references/ for depth, scripts/ for
│   └── <skill-name>/      code, evals/ for test cases
├── agents/              ← role definitions: system prompts with YAML frontmatter
│   │                      (spec + roster table in agents/README.md)
│   ├── orchestrator.md      ├ product-manager.md   ┐
│   ├── researcher.md        ├ architect.md         │ new in v2:
│   ├── code-worker.md       ├ qa-engineer.md       │ full-project
│   ├── reviewer.md          ├ integrator.md        │ lifecycle roles
│   ├── designer.md          └ release-engineer.md  ┘
│   └── report-writer.md
├── prompts/             ← reusable templates with {{placeholders}}
│   ├── task-briefing.md       ├ phase-chain.md      ┐
│   ├── plan-then-execute.md   ├ replan.md           │ new in v2
│   ├── self-review-rubric.md  ├ pre-submit-gate.md  │
│   ├── handoff-report.md      └ standing-setup.md   ┘
│   ├── verification-loop.md
│   └── artifacts/       ← project-state templates: spec, architecture,
│                          task-list, checkpoint
├── harness/             ← orchestration patterns and context discipline
│   ├── patterns.md
│   ├── context-management.md
│   ├── project-lifecycle.md   ← full-project playbook (spec → release)
│   ├── schemas/         ← JSON Schemas: manifest.py output, handoff sidecar,
│   │                      features.json feature list
│   └── scripts/         ← manifest.py (JSON manifest + lint), run_evals.py
│                          (eval validation/runner), check_placeholders.py
│                          (leftover {{placeholder}} check), check_contract.py
│                          (handoff sidecar validator), check_features.py
│                          (features.json validator + milestone gate) — stdlib only
└── tests/               ← pytest suite + bootstrap smoke test
```

## Using the toolkit

### A. Generic agents (anything that can run bash)

1. Run `bootstrap.sh` (or have your orchestrator include it in the objective — see below).
2. Read the context primer it prints. That is your index.
3. When a task matches a skill's description, read that `SKILL.md`. Only open its `references/` files if the body says you need them.
4. Adopt a role from `agents/` if you were assigned one; otherwise pick the closest match and say so in your report.
5. Use `prompts/handoff-report.md` as your final report's envelope — an assigned role's report format fills its RESULT section.

### B. Claude Code

Install as a plugin (the repo ships a `.claude-plugin/` marketplace):

```text
/plugin marketplace add tapiwamakandigona/subagent-toolkit
/plugin install subagent-toolkit@subagent-toolkit
```

Or copy files in manually:

```bash
git clone --depth 1 https://github.com/tapiwamakandigona/subagent-toolkit.git ./.abilities
mkdir -p .claude/skills .claude/agents
cp -r ./.abilities/skills/*  .claude/skills/
cp    ./.abilities/agents/*.md .claude/agents/
```

Skills are then auto-invoked when their `description` matches the task; role files become named subagents you can delegate to (`researcher`, `code-worker`, `reviewer`, `designer`, `report-writer`, `product-manager`, `architect`, `qa-engineer`, `integrator`, `release-engineer`). The exception is `orchestrator` — it's a system prompt for the *top-level* agent, not a delegate: subagents typically can't spawn subagents. Role frontmatter carries Claude-Code-native `tools:`/`model:` keys (see [`agents/README.md`](agents/README.md)); read-only roles like `reviewer` may execute read-only checks but never edit files.

### C. Any orchestrator spawning subagents

- Include the bootstrap command in every subagent objective (snippet below).
- Assign each subagent one role file from `agents/` and paste its body as (or into) the system prompt.
- Brief with `prompts/task-briefing.md`; require reports in the `prompts/handoff-report.md` shape so results are uniformly structured and easy to scan and compare across subagents.
- Pick a delegation pattern from `harness/patterns.md` **before** spawning — especially path ownership rules for parallel fan-out.
- For a machine-readable inventory (e.g., to build a skill-routing table), run:
  `python3 .abilities/harness/scripts/manifest.py .abilities`

## How an orchestrator should prompt a subagent to use this repo

Copy-paste this into the top of a subagent objective:

```text
ABILITY PACK — do this before anything else:
1. Run: git clone --depth 1 https://github.com/tapiwamakandigona/subagent-toolkit.git ./.abilities 2>/dev/null || git -C ./.abilities pull --ff-only
   (production runs: pin with ABILITIES_REF=<tag> and set ABILITIES_NO_UPDATE=1 — see "Pinning a version")
2. Run: sh ./.abilities/bootstrap.sh ./.abilities
3. Read the context primer it prints. It lists available skills, roles, and prompt
   templates with one-line descriptions.
4. Your role for this task: ./.abilities/agents/{{ROLE}}.md — read it and follow its
   process exactly.
5. Before starting work, check the skill list for anything matching this task and read
   the matching SKILL.md files. Load references/ files only when a SKILL.md points you
   to them for your specific situation.
6. Structure your final report using ./.abilities/prompts/handoff-report.md as the
   envelope; your role's report format fills its RESULT section.
Do not paste whole files into your report — cite paths instead.
```

Replace `{{ROLE}}` with one of: `researcher`, `code-worker`, `reviewer`, `designer`, `report-writer`, `product-manager`, `architect`, `qa-engineer`, `integrator`, `release-engineer`. (`orchestrator` is for the agent doing the delegating, not for subagents.)

## Full-project mode

v2 adds everything needed to run a *whole project* — not just a task — through a swarm:

- [`harness/project-lifecycle.md`](harness/project-lifecycle.md) — the phase playbook (Spec → Architecture → Foundation → Milestone loop → Release), with instructor/worker pairs, gate criteria, and default `[HUMAN GATE]`s.
- [`prompts/artifacts/`](prompts/artifacts/) — the project-state artifacts each phase produces: `spec.md`, `architecture.md`, `task-list.md`, `checkpoint.md`.
- [`prompts/phase-chain.md`](prompts/phase-chain.md), [`prompts/replan.md`](prompts/replan.md), [`prompts/pre-submit-gate.md`](prompts/pre-submit-gate.md) — chaining phases, recovering from failed plans, and gating every handoff on cleaned-up, re-verified work.
- [`prompts/standing-setup.md`](prompts/standing-setup.md) — a template for the *operator's* standing system prompt, so the orchestrator itself runs on vetted instructions.
- Machine-checkable handoffs: every report ships a `report.json` sidecar matching [`harness/schemas/handoff.schema.json`](harness/schemas/handoff.schema.json); validate with `python3 harness/scripts/check_contract.py <report.json>` — artifacts must exist and be non-empty before a handoff is accepted.
- Durable project state (`PROJECT.md`, `features.json`, `progress.md`, `checkpoints/`) and orchestrator succession, per [`harness/context-management.md`](harness/context-management.md) §6 — so a run survives context exhaustion and agent restarts.
- Machine-checkable feature gates: `features.json` matches [`harness/schemas/features.schema.json`](harness/schemas/features.schema.json); `python3 harness/scripts/check_features.py <features.json> --gate [--milestone M] [--against baseline]` enforces evidence-of-done, the milestone gate, and that workers didn't edit their own acceptance criteria.

## Design principles

- **Skills follow Anthropic's Agent Skills conventions.** Each skill is a folder with a `SKILL.md`: YAML frontmatter with `name` (≤64 chars, lowercase-hyphens, matching the folder), `description` (≤1024 chars, third person, states what it does *and* when to use it), `license`, and `metadata.version`. Bodies stay under ~3000 tokens; depth moves to `references/`, code to `scripts/`, tests to `evals/`.
- **Progressive disclosure everywhere.** Nothing in this repo assumes it will all be read. Every index earns its next hop.
- **Generic and self-contained.** No secrets, no tokens, no company- or workspace-specific references. Safe to clone into any environment.
- **Minimal dependencies.** `bootstrap.sh` needs only `git`, `grep`, `sed`, `awk`. `manifest.py` is Python 3 stdlib only, and bootstrap degrades gracefully without it.

## Contributing

- **Skills:** create `skills/<name>/SKILL.md` with valid frontmatter (spec in [`skills/README.md`](skills/README.md)), keep the body lean, push depth into `references/`, code into `scripts/`. Add deterministic test cases in `evals/evals.json` (5–8 prompts with `contains`/`regex`/`not_contains` checks).
- **Roles:** follow the frontmatter spec in [`agents/README.md`](agents/README.md) — controlled capability-profile vocabulary, optional Claude Code `tools:`/`model:` keys.
- **Prompts:** match the existing shape — H1, one-paragraph description (the first prose line becomes the manifest description), Usage notes, Template with `{{placeholders}}`, a filled Example, Anti-patterns.
- **Harness patterns:** state when to use it, how it works, and how it characteristically fails — a pattern without named failure modes isn't done.

Run `python3 harness/scripts/manifest.py --check .` before opening a PR — strict mode fails on any warning. Also run `python3 harness/scripts/check_placeholders.py skills agents harness` to catch leftover `{{placeholder}}` tokens outside `prompts/`. CI runs both checks plus shellcheck on `bootstrap.sh`, ruff and pytest on the Python, and the evals schema check.

## License

[MIT](LICENSE) © 2026 Tapiwa Makandigona
