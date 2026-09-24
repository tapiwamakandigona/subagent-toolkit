# subagent-toolkit

**A minimal harness for autonomous AI agent work.** One protocol file, five
templates, ~600 lines total. v3 replaced the v2 ability pack (104 files, 11
agent roles, 18 skills, orchestration playbooks) after field results showed
the swarm-first approach produced worse output than a single well-harnessed
agent — see `CHANGELOG.md` for the evidence trail.

Works with any agent that can run shell commands and read files: Claude
Code, Codex CLI, Viktor, or a homegrown loop.

## What's here

```
HARNESS.md              ← the whole operating protocol; start here
templates/
├── AGENTS.md           ← lean always-loaded rules file (≤100 lines when filled)
├── PROJECT.md          ← goal + standing decisions; resume point for fresh agents
├── features.json       ← machine-readable definition of done (evidence-gated)
└── loop.sh             ← reference fresh-context loop with stall/iteration guards
tests/loop_selftest.sh  ← self-test of loop.sh's guards (not copied into projects)
```

v3.1 adds turn discipline for Opus 5.5-class models: a text-only turn is a
report, not "done". It also requires that new tests be seen failing, and
keeps the qualifiers on every claim. See `CHANGELOG.md`.

## Usage

```bash
git clone --depth 1 https://github.com/tapiwamakandigona/subagent-toolkit.git
```

Then have the agent read `HARNESS.md` (~1.5k tokens) and copy templates into
the project as needed. No bootstrap script, no manifest, no pinning
ceremony — the pack is small enough to read whole.

## The five ideas

1. One agent, always. No subagents — sequence the work instead.
2. The repo is the brain; agents are disposable workers.
3. Checks (tests/lint/gates) are the highest-leverage harness component.
4. Lean context wins — every always-loaded line must earn its place.
5. Small steps, verified with evidence, committed. Loop until green.

MIT License.
