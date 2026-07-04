# Agent roles

Drop-in system prompts. Each file constrains an agent to one job with a concrete process, quality bar, and report format. Assign one role per subagent; the role's report format fills the RESULT section of [`../prompts/handoff-report.md`](../prompts/handoff-report.md).

## Roster

| Role | Job | Writes? | Typical phase |
|---|---|---|---|
| [`orchestrator`](orchestrator.md) | plans, delegates, verifies, integrates | briefs & checkpoints only | every phase (top level) |
| [`product-manager`](product-manager.md) | one-line idea → spec with checkable acceptance criteria | spec artifact | Spec |
| [`architect`](architect.md) | stack, module boundaries, interface contracts | architecture artifact | Architecture |
| [`code-worker`](code-worker.md) | scoped code changes, tested before handoff | owned code paths | Foundation / Milestone build |
| [`designer`](designer.md) | visual & interaction design, render-verified | owned design paths | Milestone build |
| [`researcher`](researcher.md) | source-cited findings with confidence levels | report only | any (read-parallel safe) |
| [`qa-engineer`](qa-engineer.md) | test plans/suites as deliverables; E2E as a real user; logs defects, never fixes | owned test paths, defect log | QA |
| [`reviewer`](reviewer.md) | independent critic; verdict + prioritized findings | nothing (runs read-only checks) | any gate |
| [`integrator`](integrator.md) | serialized merges, conflict resolution, regenerates shared files | mainline (during integration only) | Integrate |
| [`release-engineer`](release-engineer.md) | scaffolding, CI, environments, release/rollback | infra & pipeline files | Foundation / Release |
| [`report-writer`](report-writer.md) | synthesizes raw material into a readable deliverable | the document | any final stage |

The full-project sequence these roles slot into is defined in [`../harness/project-lifecycle.md`](../harness/project-lifecycle.md).

## Model tiers

Match model strength to how expensive the role's mistakes are, not to how much text it produces:

- **Frontier / strongest reasoning** — `orchestrator`, `architect`, `product-manager`, and `reviewer` on critical work. Their errors compound through everything downstream.
- **Mid-tier / strong coding or writing model** — `code-worker`, `qa-engineer`, `integrator`, `release-engineer`, `designer`, `report-writer`, `researcher`. Escalate a worker to frontier when its task is the critical path.
- **Cheap tier** — mechanical, fully-specified tasks only (formatting, extraction, file moves with exact instructions). No shipped role targets this tier by default; downgrade deliberately per task.

Each role's `recommended_model` frontmatter carries the per-role hint; `model` is the Claude Code-native setting.

## Role frontmatter spec

Every `agents/*.md` starts with YAML frontmatter:

| Key | Required | Value |
|---|---|---|
| `name` | yes | exactly the file name minus `.md`; ≤64 chars, lowercase-hyphens |
| `description` | yes | ≤1024 chars, third person, states what the role does **and** when to use it — this is the routing function. Write it as a dispatch rule: "Use when… Use proactively when…" |
| `license` | recommended | `MIT` (keeps the file attributable when copied out of the repo) |
| `metadata.version` | recommended | quoted SemVer string, two-space indent under `metadata:` (e.g. `"2.0.0"`) |
| `recommended_capability_profile` | yes | exactly one of: `coordinator` \| `readonly` \| `sandbox` \| `external` (see below) |
| `recommended_model` | no | free-text hint for harness-agnostic model selection |
| `tools` | no | Claude Code tool allowlist, comma-separated (e.g. `Read, Grep, Glob, Bash`). Omit to inherit all tools — omit deliberately, not by accident |
| `model` | no | Claude Code model: `inherit`, `haiku`, `sonnet`, or `opus` |

The body opens with a one-paragraph identity, then a **"When invoked"** block — the numbered first actions that get the agent moving correctly without burning turns deciding how to start — then Process, Quality bar, and Report format.

### Capability profiles (controlled vocabulary)

- **coordinator** — spawns subagents and reads results; minimal direct file editing. Top-level agents only; most harnesses can't nest coordinators.
- **readonly** — reads files/web, may execute checks (tests, builds); does not edit artifacts or deliver externally.
- **sandbox** — edits files and runs commands inside owned paths; no external delivery.
- **external** — may perform external side effects (send messages, call external APIs, deploy). No shipped role needs this; grant it per-task, never by default.

`tools`/`model` are consumed natively when a role is installed as a Claude Code subagent; `recommended_*` keys are advisory for other harnesses (and surfaced by `../harness/scripts/manifest.py`). The body of the file is the system prompt — keep it under ~3000 tokens.
