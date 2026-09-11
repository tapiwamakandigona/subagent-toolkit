# subagent-toolkit

**A minimal harness for autonomous AI agent work.** One protocol file, a
handful of templates, one regression suite. v3 replaced the v2 ability pack
(104 files, 11 agent roles, 18 skills, orchestration playbooks) after field
results showed the swarm-first approach produced worse output than a single
well-harnessed agent — see `CHANGELOG.md` for the evidence trail. v4 imports
the load-bearing mechanisms of the big harnesses (Codex's two-phase runs,
capability/approval split, trust-by-hash hooks; Anthropic's evidence-gated
feature lists and fresh-context evaluator; Ralph's fresh-context loop) as
portable shell + stdlib Python, and says plainly what it cannot enforce.

Works with any agent that can run shell commands and read files: Claude
Code, Codex CLI, Viktor, or a homegrown loop.

## What's here

```
HARNESS.md                   ← the whole operating protocol; start here
docs/HARNESS-COMPARISON.md   ← how this compares to Codex, Claude Code, Ralph, OpenHands…
templates/
├── AGENTS.md                ← lean always-loaded rules file (≤100 lines when filled)
├── PROJECT.md               ← goal + standing decisions; resume point for fresh agents
├── PLANNER.md               ← one-time initializer prompt: brief → features/checks/init
├── PROMPT.md                ← per-iteration brief (one task, report.json contract)
├── EVALUATOR.md             ← optional read-only fresh-context reviewer prompt
├── features.json            ← machine-readable definition of done (run-bound evidence)
├── progress.md              ← append-only log starter
├── init.sh                  ← phase 1: setup with network, once, before the loop
├── verify.sh                ← phase 2 gate: deterministic checks that write evidence
├── sandbox.sh               ← best-effort isolation prefix (env allowlist, no network)
├── hooks.lock               ← sha256-pinned trusted hooks (pre/post iteration)
├── check_features.py        ← fail-closed gate, integrity guard, report validator, ledger
└── loop.sh                  ← the fresh-context loop with all guards (exit codes 0–7)
tests/test_harness.py        ← 55 offline behavioural tests (synthetic git/agent fixtures)
```

## Usage

```bash
git clone --depth 1 https://github.com/tapiwamakandigona/subagent-toolkit.git
```

Have the agent read `HARNESS.md` (~3k tokens) and copy `templates/` into the
project. Run `PLANNER.md` once (or fill `features.json`/`verify.sh` by hand),
review the checks, commit, then:

```bash
AGENT_CMD='claude -p' SANDBOX_CMD=./sandbox.sh ./loop.sh 30
# optional second opinion after every iteration:
EVALUATOR_CMD='claude -p' AGENT_CMD='codex exec' ./loop.sh 30
```

Exit codes: 0 complete · 1 repeated failure · 2 stalled · 3 setup · 4 cap ·
5 approval required (see `APPROVAL_REQUESTED.md`) · 6 integrity · 7 operator stop.

## The five ideas

1. One agent, always. No subagents — sequence the work instead.
2. The repo is the brain; agents are disposable workers.
3. Checks (tests/lint/gates) are the highest-leverage harness component.
4. Lean context wins — every always-loaded line must earn its place.
5. Small steps, verified with evidence, committed. Loop until green.

MIT License.
