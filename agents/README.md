# Agent roles

Drop-in system prompts. Each file constrains an agent to one job with a concrete process, quality bar, and report format. Assign one role per subagent; the role's report format fills the RESULT section of [`../prompts/handoff-report.md`](../prompts/handoff-report.md).

## Role frontmatter spec

Every `agents/*.md` starts with YAML frontmatter:

| Key | Required | Value |
|---|---|---|
| `name` | yes | exactly the file name minus `.md`; ≤64 chars, lowercase-hyphens |
| `description` | yes | ≤1024 chars, third person, states what the role does **and** when to use it — this is the routing function |
| `license` | recommended | `MIT` (keeps the file attributable when copied out of the repo) |
| `metadata.version` | recommended | quoted SemVer string, two-space indent under `metadata:` (e.g. `"1.1.0"`) |
| `recommended_capability_profile` | yes | exactly one of: `coordinator` \| `readonly` \| `sandbox` \| `external` (see below) |
| `recommended_model` | no | free-text hint for harness-agnostic model selection |
| `tools` | no | Claude Code tool allowlist, comma-separated (e.g. `Read, Grep, Glob, Bash`). Omit to inherit all tools — omit deliberately, not by accident |
| `model` | no | Claude Code model: `inherit`, `haiku`, `sonnet`, or `opus` |

### Capability profiles (controlled vocabulary)

- **coordinator** — spawns subagents and reads results; minimal direct file editing. Top-level agents only; most harnesses can't nest coordinators.
- **readonly** — reads files/web, may execute checks (tests, builds); does not edit artifacts or deliver externally.
- **sandbox** — edits files and runs commands inside owned paths; no external delivery.
- **external** — may perform external side effects (send messages, call external APIs, deploy). No shipped role needs this; grant it per-task, never by default.

`tools`/`model` are consumed natively when a role is installed as a Claude Code subagent; `recommended_*` keys are advisory for other harnesses (and surfaced by `../harness/scripts/manifest.py`). The body of the file is the system prompt — keep it under ~3000 tokens.
