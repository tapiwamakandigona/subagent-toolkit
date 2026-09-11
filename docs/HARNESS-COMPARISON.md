# How this harness compares to the big ones (September 2026)

Research date: 2026-09-11. Sources are the primary vendor pages and repos
listed at the end; third-party rankings are labeled as such. Claims about
this toolkit are VERIFIED against `tests/test_harness.py` (55 tests) unless
marked otherwise. Claims about other products come from their documentation
and are only as current as that documentation.

## What "GPT-6 Astra" actually is

OpenAI released **GPT-6 Astra** in early September 2026 (openai.com, model
docs: `reasoning.effort` low → max; computer use, code interpreter, tool
search). Astra is a **model**. The harness it runs in is **Codex** (CLI, IDE,
cloud, `codex exec`), which OpenAI updated alongside the launch. Third-party
results: Endor Labs measured Codex + Astra at 82.1% FuncPass / 34.1% SecPass
on their real-world task set, versus 87.2% / 36.9% for Claude Code + Fable 5.1
(Endor Labs blog, 2026-09-08). "Welcome to the AGI era" (Brockman) is a launch
statement, not a measured capability; every comparison below is about
**mechanisms**, which are what a harness controls.

## The mechanisms that matter, and where each harness stands

Legend: ✅ enforced by the system · ◐ present but convention/best-effort ·
✗ absent · n/a not applicable. "This (v4)" is `templates/` on this branch.

| Mechanism | Codex (Astra) | Claude Code / Agent SDK | Anthropic long-running harness | Ralph loop | OpenHands | This (v3.0.1) | This (v4) |
|---|---|---|---|---|---|---|---|
| Fresh context per task, state in files | ◐ (`codex exec resume`) | ◐ (`-p`, hooks) | ✅ initializer + coding agent, progress file | ✅ the whole idea | ◐ (README: not stated) | ✅ | ✅ |
| Definition of done as data, default-FAIL | ✗ | ◐ `/goal` (model-judged) | ✅ `feature_list.json` | ◐ (todo.md / promise marker) | ✗ (README: not stated) | ◐ flags only | ✅ + run-bound evidence |
| Completion judged independently of the builder | ◐ auto-review reviewer | ✅ `/goal` fast-model evaluator | ✅ evaluator agent (Playwright) | ✗ (agent prints DONE) | ✗ (README: not stated) | ✗ (marker) | ✅ deterministic gate + optional evaluator |
| Check/test integrity frozen during run | ✗ | ✗ | ◐ prompt ("unacceptable to edit tests") | ✗ | ✗ | ✗ | ✅ sha-frozen, run-local checker |
| Kernel-level sandbox | ✅ Seatbelt / Landlock+seccomp / Windows | ◐ permission modes | n/a | ✗ | ◐ Docker sandbox optional ("Option 1: Without a Sandbox") | ✗ | ◐ bwrap → netns → env-scrub, mode reported |
| Network off by default | ✅ | ✗ | n/a | ✗ | ✗ (README: not stated) | ✗ | ✅ (`HARNESS_NET=1` opt-in) |
| Two-phase run (setup online → agent offline, secrets removed) | ✅ cloud environments | ✗ | ✗ | ✗ | ✗ (README: not stated) | ✗ | ✅ `init.sh` + `sandbox.sh` |
| Capability vs approval separated; risk tiers | ✅ sandbox / approval policy / auto-review | ✅ permission modes, hooks | n/a | ✗ (`--yolo`) | ◐ (agent backends) | ◐ prose tiers | ✅ report → exit 5 halt |
| Lifecycle hooks, trusted by hash | ✅ | ✅ hooks (settings-scoped) | ◐ | ◐ stop hook | ✗ (README: not stated) | ✗ | ✅ `hooks.lock` |
| Structured machine-readable final output | ✅ `--output-schema`, JSONL events | ◐ | ✗ | ✗ | ✗ (README: not stated) | ✗ | ✅ `report.json` validated |
| Durable invocation log, tamper-evident | ◐ session rollouts | ◐ transcripts | ✗ | ✗ | ✗ (README: not stated) | ✗ | ✅ hash-chained ledger |
| Single-writer lock, stale-lock reconciliation | n/a | n/a | ✗ | ✗ | ✗ | ✗ | ✅ |
| Wall-clock / output caps | ✅ | ✅ | ◐ | ◐ `--max-iterations` | ◐ (README: not stated) | ✗ | ✅ |
| Operator kill switch + mid-run steering | ✅ (pause, monitoring) | ✅ (`AGENT_STOP`, `STEER.md` in cwc repo) | ✗ | ✗ | ◐ (interactive UI) | ✗ | ✅ |
| Asynchronous safety monitoring that pauses tasks | ✅ (Astra) | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Subagents / parallel fan-out | ✅ | ✅ | ✅ (planner/generator/evaluator) | ◐ | ◐ | ✗ by design | ✗ by design |
| Hosted runtime, runs with laptop closed | ✅ Codex cloud | ✅ Routines / Managed Agents | ✅ | ✗ | ✅ OpenHands Cloud | ✗ | ✗ |
| Semantic repo index | ✗ (agentic search) | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |

### Scoring against the Kendr 10-dimension rubric (third-party, dated 2026-08-14)

Kendr Research scores 50 harnesses out of 100 on ten architectural dimensions
(loop, edit safety, context, isolation, permissions, durability, model,
extensibility, surface, cloud). Their published leaders: Claude Code 88, Codex
82, Cursor 80. **Our own estimate for this toolkit (ASSUMED — self-scored with
their anchors, not scored by Kendr):**

| Dimension | v3.0.1 | v4 | Why |
|---|---|---|---|
| Loop (steering, breakers, completion contract) | 4 | 8 | caps, stall halt, kill switch, steer, deterministic gate |
| Edit safety (typed tools, atomic edits, undo) | 2 | 2 | agent-side; the wrapper does not own the editor |
| Context (instruction hierarchy, compaction, memory) | 5 | 6 | lean AGENTS.md, fresh restarts, PLANNER; no index |
| Isolation | 1 | 5 | best-effort bwrap/netns, honest mode reporting |
| Permissions (gates, durable approvals, subagent parity) | 3 | 6 | approval halt with file, hooks by hash; no durable allow-rules |
| Durability (log as truth, leases, reconciliation, tamper evidence) | 1 | 8 | hash-chained ledger, single-writer lock, stale reclaim |
| Model (provider breadth, cost controls) | 5 | 5 | any `AGENT_CMD`; no routing or cost metering |
| Extensibility (hooks, skills, SDK) | 2 | 5 | trusted hooks, evaluator slot; no plugin/MCP layer |
| Surface (terminal/IDE/web, headless, parallel) | 3 | 3 | headless shell only, deliberately |
| Cloud (hosted runners, CI-native) | 1 | 2 | CI runs the suite; no hosted loop |
| **Total** | **27** | **50** | roughly where Kendr places the stronger independent CLI harnesses |

That gap to 82–88 is almost entirely the dimensions we do not want: hosted
runtime, IDE surfaces, plugin ecosystems, model routing. On the dimensions a
single-agent loop controls — loop contract, durability, permissions, and
verifiable completion — v4 is at or above what the big harnesses ship, with
one structural exception: **kernel-level isolation**, which only Codex and the
Docker-based agents actually enforce.

## What we imported, and from where

| Imported into v4 | Source | Adaptation |
|---|---|---|
| Two-phase run (setup online, agent offline; secrets removed before agent phase) | Codex cloud environments | `init.sh` runs once unsandboxed before the baseline; iterations run under `sandbox.sh` |
| Capability/approval split; approval requests halt for a human | Codex sandbox vs approval policy; auto-review risk tiers | `report.json → approval_requests` → `APPROVAL_REQUESTED.md`, exit 5 |
| Hooks trusted by exact hash; changed hooks skipped until re-trusted | Codex hooks trust flow | `hooks.lock`, `check_features.py hooks` |
| Structured final output validated against a schema | Codex `--output-schema` / `--output-last-message` | `report.json` with mandatory VERIFIED/ASSUMED labels |
| Default-FAIL feature contract as JSON; only `passes` may flip; evidence must be opened/produced, not asserted | Anthropic "Effective harnesses", cwc `verify-gate.sh` | evidence must be written by `verify.sh` and contain the run id |
| Initializer/planner session that expands a brief into the contract | Anthropic initializer agent; harness-design planner | `PLANNER.md` |
| Fresh-context, read-only, skeptical evaluator whose findings feed the next brief | Anthropic generator/evaluator; cwc `evaluator.md` | `EVALUATOR_CMD`, fingerprint-enforced read-only, `NEEDS_WORK` blocks completion |
| Kill switch and steering files | cwc `kill-switch.sh`, `steer.sh` | `AGENT_STOP`, `STEER.md` |
| Fresh context per iteration, one item per loop, "search before assuming" | Ralph (Huntley) | already in v3; v4 makes the report and gate the completion contract instead of a printed marker |
| Durable log as source of truth, single-writer lease, restart reconciliation, tamper evidence | Kendr durability dimension; DvalinCode hash-chained audit trail | `.harness/runs/*.jsonl` hash chain, `.harness/lock` |
| Wall-clock and output caps | Codex/Claude Code timeouts; `ralph --max-iterations` | `ITER_TIMEOUT`, `MAX_MINUTES`, `OUTPUT_CAP` |

## What we deliberately did not import

- **Subagents and fan-out.** Anthropic's own March 2026 post shows the
  planner/generator/evaluator harness cost 20× a solo run and that model
  upgrades made the sprint decomposition and per-sprint evaluation
  unnecessary. The parts that stayed load-bearing (planner, evaluator) are
  imported as *sequential* passes. Parallel writers remain out.
- **Kernel sandboxing.** Cannot be done portably in shell; `sandbox.sh` is
  explicit about which mode ran and can refuse to run unsandboxed.
- **Model-judged completion (`/goal`).** A fast model reading the transcript
  is convenient but is exactly the "looks done" signal HARNESS.md rejects.
  We keep the deterministic gate and offer the evaluator as an *additional*
  check, never a replacement.
- **Hosted runtime, IDE surfaces, plugin/MCP layer.** Out of scope for a
  portable loop; use the vendor harness for those and keep this as the
  protocol they run inside.

## "AGI-level" autonomy: what the evidence supports

- Anthropic (2025-11, 2026-03): the failure modes of long autonomous runs
  are one-shotting, premature "done", undocumented half-features, generous
  self-grading. Every one is a **harness** problem and each has a
  mechanical fix, now in v4.
- Anthropic (2026-03): "every component in a harness encodes an assumption
  about what the model can't do on its own" — re-test after each model
  release and strip what is no longer load-bearing. Applied here: the
  evaluator and planner are optional slots, not requirements.
- Endor Labs (2026-09): the best Codex + Astra configuration still ships
  insecure code in roughly two out of three tasks that pass functionally
  (34.1% SecPass). Autonomy without independent checks is not capability.
- Kendr (2026-08): durability is "the one place where the field is broadly
  weak"; almost no harness treats the invocation log as authoritative
  state. v4 does.

The conclusion for this toolkit: the frontier models are now good enough
that the loop's job is not to make them smarter, it is to make their
claims **checkable** and their failures **cheap**. That is what v4 adds.

## Sources (fetched 2026-09-11; primary unless noted)

- OpenAI, GPT-6 Astra model page: https://developers.openai.com/api/docs/models/gpt-6-astra
- OpenAI, "GPT-6 Astra: A new generation of intelligence" (403 to scripted fetch; quoted via search excerpt): https://openai.com/index/gpt-6-astra/
- Codex docs — non-interactive mode (`codex exec`, JSONL, `--output-schema`): https://developers.openai.com/codex/noninteractive
- Codex docs — agent approvals & security (sandbox vs approval, two-phase cloud runtime, auto-review, safety monitoring): https://developers.openai.com/codex/sandbox
- Codex docs — hooks (events, trust by hash): https://developers.openai.com/codex/hooks
- Codex docs — AGENTS.md discovery and precedence: https://developers.openai.com/codex/guides/agents-md
- Anthropic, "Effective harnesses for long-running agents" (2025-11-26): https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
- Anthropic, "Harness design for long-running application development" (2026-03-24): https://www.anthropic.com/engineering/harness-design-long-running-apps
- anthropics/cwc-long-running-agents README (default-FAIL contract, evaluator, kill switch, steer): https://github.com/anthropics/cwc-long-running-agents
- Claude Code `/goal` docs: https://code.claude.com/docs/en/goal
- anthropics/claude-code ralph-wiggum plugin README: https://github.com/anthropics/claude-code/blob/main/plugins/ralph-wiggum/README.md
- Geoffrey Huntley, "Ralph": https://ghuntley.com/ralph/
- Kendr Research, "AI Coding Agent Comparison 2026: 50 Harnesses Scored" (third-party rubric, 2026-08-14): https://kendr.org/blog/coding-agent-harness-comparison-2026.html
- Endor Labs, "Codex with GPT-6 Astra posts 82.1% FuncPass and 34.1% SecPass" (third-party benchmark, 2026-09-08): https://www.endorlabs.com/learn/gpt-6-astra-on-codex---the-biggest-codex-leap-to-date
- OpenHands README (Docker sandbox optional, agent backends, OpenHands Cloud): https://github.com/All-Hands-AI/OpenHands
- SWE-agent README — fetched but not scored: it now points users to mini-swe-agent and describes neither sandboxing nor completion contracts: https://github.com/SWE-agent/SWE-agent

The OpenHands column is scored from its README only; "not stated" means the
mechanism may exist in deeper docs that were not read for this comparison.
