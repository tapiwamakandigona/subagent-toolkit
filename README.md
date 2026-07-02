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

One line at the start of a run:

```bash
curl -fsSL https://raw.githubusercontent.com/tapiwamakandigona/subagent-toolkit/main/bootstrap.sh | sh
```

Or, if you prefer to inspect first (you should):

```bash
git clone --depth 1 https://github.com/tapiwamakandigona/subagent-toolkit.git ./.abilities
sh ./.abilities/bootstrap.sh
```

`bootstrap.sh` clones/updates the repo into `./.abilities` (override with the first argument or `$ABILITIES_DIR`), prints a manifest of every skill, role, and prompt it found, and emits a **context primer** — a ready-to-paste block that tells the agent what it now has and how to load more detail on demand.

## Repo layout

```
subagent-toolkit/
├── README.md            ← you are here
├── bootstrap.sh         ← installer + manifest + context primer
├── skills/              ← Agent Skills (Anthropic conventions): one folder per
│   │                      skill, each with SKILL.md (frontmatter: name,
│   │                      description), references/ for depth, scripts/ for code
│   └── <skill-name>/SKILL.md
├── agents/              ← role definitions: system prompts with YAML frontmatter
│   ├── orchestrator.md
│   ├── researcher.md
│   ├── code-worker.md
│   ├── reviewer.md
│   ├── designer.md
│   └── report-writer.md
├── prompts/             ← reusable templates with {{placeholders}}
│   ├── task-briefing.md
│   ├── plan-then-execute.md
│   ├── self-review-rubric.md
│   ├── handoff-report.md
│   └── verification-loop.md
└── harness/             ← orchestration patterns and context discipline
    ├── patterns.md
    ├── context-management.md
    └── scripts/manifest.py   ← JSON manifest of the whole pack (stdlib only)
```

## Using the toolkit

### A. Generic agents (anything that can run bash)

1. Run `bootstrap.sh` (or have your orchestrator include it in the objective — see below).
2. Read the context primer it prints. That is your index.
3. When a task matches a skill's description, read that `SKILL.md`. Only open its `references/` files if the body says you need them.
4. Adopt a role from `agents/` if you were assigned one; otherwise pick the closest match and say so in your report.
5. Use `prompts/handoff-report.md` to structure your final report.

### B. Claude Code

Claude Code discovers skills and subagent definitions from `.claude/`:

```bash
git clone --depth 1 https://github.com/tapiwamakandigona/subagent-toolkit.git ./.abilities
mkdir -p .claude/skills .claude/agents
cp -r ./.abilities/skills/*  .claude/skills/
cp    ./.abilities/agents/*.md .claude/agents/
```

Skills are then auto-invoked when their `description` matches the task; role files become named subagents you can delegate to (`orchestrator`, `researcher`, `code-worker`, `reviewer`, `designer`, `report-writer`).

### C. Any orchestrator spawning subagents

- Include the bootstrap command in every subagent objective (snippet below).
- Assign each subagent one role file from `agents/` and paste its body as (or into) the system prompt.
- Brief with `prompts/task-briefing.md`; require reports in the `prompts/handoff-report.md` shape so results are machine-comparable across subagents.
- Pick a delegation pattern from `harness/patterns.md` **before** spawning — especially path ownership rules for parallel fan-out.
- For a machine-readable inventory (e.g., to build a skill-routing table), run:
  `python3 .abilities/harness/scripts/manifest.py .abilities`

## How an orchestrator should prompt a subagent to use this repo

Copy-paste this into the top of a subagent objective:

```text
ABILITY PACK — do this before anything else:
1. Run: git clone --depth 1 https://github.com/tapiwamakandigona/subagent-toolkit.git ./.abilities 2>/dev/null || git -C ./.abilities pull --ff-only
2. Run: sh ./.abilities/bootstrap.sh ./.abilities
3. Read the context primer it prints. It lists available skills, roles, and prompt
   templates with one-line descriptions.
4. Your role for this task: ./.abilities/agents/{{ROLE}}.md — read it and follow its
   process and report format exactly.
5. Before starting work, check the skill list for anything matching this task and read
   the matching SKILL.md files. Load references/ files only when a SKILL.md points you
   to them for your specific situation.
6. Structure your final report using ./.abilities/prompts/handoff-report.md.
Do not paste whole files into your report — cite paths instead.
```

Replace `{{ROLE}}` with one of: `orchestrator`, `researcher`, `code-worker`, `reviewer`, `designer`, `report-writer`.

## Design principles

- **Skills follow Anthropic's Agent Skills conventions.** Each skill is a folder with a `SKILL.md`: YAML frontmatter with `name` (≤64 chars, lowercase-hyphens) and `description` (≤1024 chars, third person, states what it does *and* when to use it). Bodies stay under ~3000 tokens; depth moves to `references/`, code to `scripts/`.
- **Progressive disclosure everywhere.** Nothing in this repo assumes it will all be read. Every index earns its next hop.
- **Generic and self-contained.** No secrets, no tokens, no company- or workspace-specific references. Safe to clone into any environment.
- **Minimal dependencies.** `bootstrap.sh` needs only `git`, `grep`, `sed`, `awk`. `manifest.py` is Python 3 stdlib only, and bootstrap degrades gracefully without it.

## Contributing

Add a skill: create `skills/<name>/SKILL.md` with valid frontmatter, keep the body lean, push depth into `references/`. Add a role: match the frontmatter shape in `agents/`. Run `python3 harness/scripts/manifest.py .` before opening a PR — it doubles as a lint for missing frontmatter.

## License

[MIT](LICENSE) © 2026 Tapiwa Makandigona
