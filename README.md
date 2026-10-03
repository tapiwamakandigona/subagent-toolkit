# subagent-toolkit

**A minimal harness for autonomous AI agent work.** One protocol file, six
templates, two on-demand playbooks. v3 replaced the v2 ability pack (104 files, 11
agent roles, 18 skills, orchestration playbooks) after field results showed
the swarm-first approach produced worse output than a single well-harnessed
agent — see `CHANGELOG.md` for the evidence trail.

Works with any agent that can run shell commands and read files: Claude
Code, Codex CLI, Viktor, or a homegrown loop.

## High-autonomy upgrade (opt-in)

This package adds an evidence-tested profile derived from v3.2.0; it is not a
new upstream release. Start with [STANDING_SETUP.md](STANDING_SETUP.md) for
action-first instructions and explicitly authorized password/browser use,
then [docs/high-autonomy.md](docs/high-autonomy.md) for installation.
The legacy runner and its tests remain unchanged. New helpers use only the
Python standard library; a live browser is supplied by your agent platform.
Run `sh verify.sh` to check the new profile locally.

## What's here

```
HARNESS.md              ← the whole operating protocol; start here
templates/
├── AGENTS.md           ← lean always-loaded rules file (≤100 lines when filled)
├── PROJECT.md          ← goal + standing decisions; resume point for fresh agents
├── features.json       ← machine-readable definition of done (evidence-gated)
├── loop.sh             ← reference fresh-context loop with stall/iteration guards
├── check_budget.sh     ← CI gate: boot set ≤ 32 KB, AGENTS.md ≤ 100 lines, progress.md ≤ 64 KB
└── EVALUATOR.md        ← brief for the optional read-only, fresh-context evaluator
docs/
├── browser.md          ← authenticated browser sessions (read only for login tasks)
└── credentials.md      ← storing operator-pasted credentials (read only when needed)
tests/                  ← self-tests for loop.sh and the harness budget (not copied into projects)
```

v3.2 halves the always-read protocol (12.4 KB → 6.4 KB) and adds a boot budget
enforced in CI, `progress.md` rotation, and an optional read-only evaluator.
v3.1 added turn discipline for Opus 5.5-class models. See `CHANGELOG.md`.

## Usage

```bash
git clone --depth 1 https://github.com/tapiwamakandigona/subagent-toolkit.git
```

Then have the agent read `HARNESS.md` (~1.6k tokens) and copy templates into
the project as needed. No bootstrap script, no manifest, no pinning
ceremony — the pack is small enough to read whole.

## The five ideas

1. One writer, always. No swarms or parallel workers; sequence the work. The only
   second agent is an optional read-only evaluator.
2. The repo is the brain; agents are disposable workers.
3. Checks (tests/lint/gates) are the highest-leverage harness component.
4. Lean context wins. Every always-loaded line must earn its place, and CI enforces the budget.
5. Small steps, verified with evidence, committed. Loop until green.

MIT License.
