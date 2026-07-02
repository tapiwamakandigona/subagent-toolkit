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

- `ABILITIES_REF=<tag|branch|commit>` — bootstrap checks out exactly this ref after cloning (e.g. `ABILITIES_REF=v1.1.0`).
- `ABILITIES_NO_UPDATE=1` — skip the auto-`git pull` on an existing checkout, so instructions can't change mid-run.

Unpinned, bootstrap tracks `main` and updates on every run — fine for exploration, not for reproducible orchestration.

## Repo layout

```
subagent-toolkit/
├── README.md            ← you are here
├── bootstrap.sh         ← installer + manifest + context primer
├── .claude-plugin/      ← Claude Code plugin/marketplace manifest
├── skills/              ← Agent Skills (Anthropic conventions): one folder per
│   │                      skill, each with SKILL.md (frontmatter: name,
│   │                      description), references/ for depth, scripts/ for
│   └── <skill-name>/      code, evals/ for test cases
├── agents/              ← role definitions: system prompts with YAML frontmatter
│   │                      (spec in agents/README.md)
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

Skills are then auto-invoked when their `description` matches the task; role files become named subagents you can delegate to (`researcher`, `code-worker`, `reviewer`, `designer`, `report-writer`). The exception is `orchestrator` — it's a system prompt for the *top-level* agent, not a delegate: subagents typically can't spawn subagents. Role frontmatter carries Claude-Code-native `tools:`/`model:` keys (see [`agents/README.md`](agents/README.md)), so read-only roles like `reviewer` don't inherit write access.

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

Replace `{{ROLE}}` with one of: `researcher`, `code-worker`, `reviewer`, `designer`, `report-writer`. (`orchestrator` is for the agent doing the delegating, not for subagents.)

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

Run `python3 harness/scripts/manifest.py --check .` before opening a PR — strict mode fails on any warning. CI runs the same check plus shellcheck on `bootstrap.sh`, ruff and pytest on the Python, and the evals schema check.

## License

[MIT](LICENSE) © 2026 Tapiwa Makandigona
