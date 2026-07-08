# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2026-07-08

Hardening release: the `features.json` project-state protocol becomes
machine-checkable, and the harness docs absorb operational lessons on
compaction, fan-out scope changes, and orchestrator succession.

### Added

- **features.json validator + milestone gate**
  `harness/scripts/check_features.py` (stdlib-only, mirrors
  `check_contract.py`): validates the project feature list against the new
  `harness/schemas/features.schema.json`, enforces evidence-of-done (every
  `passes: true` needs evidence paths that exist and are non-empty), runs
  the milestone gate from `project-lifecycle.md` §2 (`--gate
  [--milestone M]`), and diff-checks the worker-frozen fields
  (`id`/`title`/`acceptance`, no additions/removals) against the
  orchestrator's baseline (`--against`). Previously the gate and the
  "workers may only flip `passes`" rule were documented but only manually
  checkable. Wired into `context-management.md` §6,
  `project-lifecycle.md` §2, and the README; 17 tests.
- **Project-state file templates**
  `prompts/artifacts/project-state.md`: required shapes for `PROJECT.md`,
  `progress.md`, `init.sh`, and a worked `features.json` example that
  passes `check_features.py` verbatim — the state files three harness docs
  lean on previously had no template anywhere in the pack.

### Changed

- `harness/schemas/features.schema.json` aligned with the validator:
  `title`/`acceptance` must contain non-whitespace, evidence strings must
  be non-empty, and `evidence: null` is explicitly allowed while
  `passes` is false; `check_features.py` now rejects empty-string
  evidence in kind.

- `harness/context-management.md`: compaction is a session boundary;
  unambiguous status vocabulary for notes; successor-completeness rule
  (state files must suffice for a zero-memory successor).
- `harness/patterns.md`: fan-out variations — delta shard for mid-run scope
  additions, convergence check for research fan-outs.

## [2.0.0] - 2026-07-04

Full-project autonomy release: the pack graduates from task-level delegation
to running an entire project — spec to release — through a swarm, with
machine-checkable handoffs and durable project state. Informed by a
multi-source research pass over production multi-agent systems (MetaGPT,
ChatDev, AutoGen, OpenHands, SWE-agent, GPT-Pilot, Claude Code, Anthropic's
multi-agent and long-running-agent work) and published agent-failure
taxonomies.

### Added

- **5 new lifecycle roles**: `product-manager` (idea → spec with
  machine-checkable acceptance criteria), `architect` (stack rationale,
  single-owner module map, verbatim interface contracts, design freeze),
  `qa-engineer` (adversarial test plans, E2E as a real user, defect log —
  never fixes), `integrator` (serialized merges, fresh-context conflict
  resolution), `release-engineer` (init.sh scaffold, CI parity,
  deny-by-default destructive ops). Roster table + model-tier guidance in
  `agents/README.md`.
- **Full-project playbook** `harness/project-lifecycle.md`: Spec →
  Architecture → Foundation → Milestone loop → Release, with
  instructor/worker pairs per phase, gate criteria, evidence-of-done rules,
  and default `[HUMAN GATE]`s (spec approval, destructive ops, release).
- **Project-state artifacts** `prompts/artifacts/{spec,architecture,task-list,checkpoint}.md`
  — task-list rows carry the task / auto-verify command / human-verify
  sentence triple.
- **New prompts**: `phase-chain.md` (ChatDev-style phase table with cycle
  caps and gates), `replan.md` (verified-and-kept / sunk / failed-assumptions
  / new-plan audit), `pre-submit-gate.md` (diff back, remove scratch, revert
  out-of-scope, re-verify, attach evidence), `standing-setup.md` (generic
  operator standing-prompt template, <2k tokens).
- **Machine-checkable handoffs**: `harness/schemas/handoff.schema.json`
  (report.json sidecar shape; required: run_id, agent, status, artifacts;
  status enum complete|partial|blocked|failed) + stdlib-only validator
  `harness/scripts/check_contract.py` that also existence-checks artifact
  and evidence paths; `prompts/handoff-report.md` pins the shape verbatim
  and gains mandatory IMPLICIT DECISIONS and EVIDENCE sections.
- **Project state protocol** (`harness/context-management.md` §6):
  `PROJECT.md`, `features.json` (workers may only flip `passes` + attach
  `evidence`), append-only `progress.md`, `init.sh`, `checkpoints/`;
  constant-context restart, condensation recipe, and orchestrator
  succession.
- **5 project-archetype skills**: `buildless-web-verify` (headless-Chromium
  harness for no-build-step browser apps), `appwrite-platform` (Sites
  tar-deploy + poll-to-ready, Functions, OAuth deep links, secret hygiene),
  `static-export-webapp` (static-export constraints, money-logic parity
  tests, Capacitor APK variant), `static-site-qa` (breakpoint screenshots,
  link/HTML/SEO checks before deploy), `repo-conventions-discovery`
  (agent-doc-first protocol; agent docs outrank READMEs; constraint
  extraction and pre-handoff re-check).
- **Orchestration upgrades** (`harness/patterns.md`): a real merge/integration
  pattern (branch isolation, single-writer rule, interface freeze,
  serialized integrator-owned merges) replacing the old "no acceptable merge
  strategy" guidance; effort-scaling table with an engineering-milestone
  row; loop guards (review ≤3 cycles, no-progress halt after 2 iterations);
  risk-tiered gating (read auto / workspace-write auto / destructive+prod+spend
  = human gate); per-agent trace dirs `runs/<run-id>/<agent-slug>/`.
- **Role hardening**: every role gains a "When invoked: 1, 2, 3" block;
  orchestrator gains the effort table, single-writer and evidence-of-done
  rejection rules; code-worker gains repo-map step 0, anchored exact-match
  edits, and the pre-submit gate; reviewer gains a numbered regulation
  checklist and a tamper diff-check; task briefings restructured to
  OBJECTIVE / OUTPUT CONTRACT / TOOL & SOURCE GUIDANCE / BOUNDARIES with
  word caps (research ≤500, engineering ≤900).
- CI validates all `harness/schemas/*.json` parse; 13 new tests for
  `check_contract.py` (60 total).

### Fixed

- `bootstrap.sh`: locally-resolvable refs are checked out with **zero
  network access**, so `ABILITIES_REF` + `ABILITIES_NO_UPDATE=1` now truly
  freezes instructions mid-run (and pinned fan-outs stop hammering the
  remote); an existing target dir missing `agents/` or `skills/` is rejected
  instead of half-trusted.
- `bootstrap.sh`: running from inside a checkout with an `ABILITIES_REF`
  that doesn't match HEAD now logs a loud warning (the checkout is never
  mutated, but a pinned caller must not get unpinned instructions
  silently); and under `ABILITIES_NO_UPDATE=1`, a locally-resolvable ref
  whose checkout fails (dirty worktree) dies with a clear error instead of
  falling through to network fetches. Both covered by new smoke tests.
- All 5 new archetype skills ship `evals/evals.json` (6–7 cases each),
  keeping the "every skill has evals" convention intact (117 cases total).
- `agents/reviewer.md` contradiction (readonly profile vs Bash tool)
  resolved: reviewers MAY execute read-only checks, MUST NOT edit.
- `harness/scripts/manifest.py` now discovers nested prompts
  (`prompts/artifacts/*.md`).

### Changed

- README documents that branch refs are not reproducible pins (use tags or
  SHAs) and adds the "Full-project mode" section.
- All agents and skills bumped to `metadata.version: "2.0.0"` (prompt files
  carry no version metadata by design).
- The 5 new archetype skills were added beyond the original two-builder file
  plan as a deliberate design addendum: a portfolio-research pass identified
  recurring project archetypes (buildless web apps, static-export webapps,
  platform deploys, site QA, convention discovery) that the pack had no
  generic coverage for; they were built by a dedicated third builder with
  disjoint file ownership (`skills/**` only).

## [1.1.0] - 2026-07-02

### Added

- **5 new skills**: `data-analysis`, `debugging`, `api-integration`,
  `document-handling`, and `security-review`, closing the biggest coverage
  gaps in the original research/writing-heavy pack.
- **Per-skill evals**: skills may ship `skills/<name>/evals/evals.json`
  (5–8 deterministic test cases each); new `harness/scripts/run_evals.py`
  validates eval sets (`--validate`, the CI gate), lists them (`--list`),
  and optionally runs them against a caller-supplied runner command,
  writing a per-skill pass-rate `benchmark.json`.
- **CI** (`.github/workflows/ci.yml`): shellcheck on shell scripts, ruff
  (syntax/pyflakes rules) on Python, pytest suite, strict manifest lint,
  eval validation, and a bootstrap smoke test run under both `sh` and `dash`.
- **Claude Code plugin packaging** (`.claude-plugin/plugin.json` +
  `marketplace.json`): install with
  `/plugin marketplace add tapiwamakandigona/subagent-toolkit` then
  `/plugin install subagent-toolkit@subagent-toolkit`, replacing the manual
  `cp` into `.claude/`.
- **Version pinning**: `ABILITIES_REF` env var checks out a specific
  tag/branch/commit after clone, and `ABILITIES_NO_UPDATE=1` skips the
  auto `git pull` on existing checkouts — so parallel fan-outs get
  identical instructions mid-run.
- **Spec-complete skill frontmatter**: all skills now carry `license: MIT`
  and `metadata.version` per the Agent Skills spec's optional fields.
- **Strict lint mode**: `harness/scripts/manifest.py --check <root>` exits
  non-zero on any warning, plus new checks (name↔dirname match, nested
  `metadata` map tolerated by the parser).
- **Manifest JSON Schema** (`harness/schemas/manifest.schema.json`,
  draft-07) so orchestrators can validate `manifest.py` output
  programmatically.
- **Harness content**: precedence chain (objective > role > templates >
  skills), budgets & effort-scaling heuristics, "when NOT to multi-agent"
  guidance, failure & recovery pattern, untrusted-content / prompt-injection
  rules, memory/compaction and file-based tracing conventions.
- Roles gained Claude-Code-native `tools:` and `model:` frontmatter and a
  controlled `recommended_capability_profile` vocabulary
  (coordinator | readonly | sandbox | external).
- A pytest suite (`tests/`) covering the frontmatter parsers, fetch_page
  helpers, and a bootstrap smoke test (`tests/smoke_bootstrap.sh`).

### Fixed

- `bootstrap.sh`: an explicitly passed `TARGET_DIR` is no longer silently
  ignored when running from inside a checkout; `git pull` output no longer
  pollutes the manifest/primer stream.
- `skills/web-data-extraction/scripts/fetch_page.py`: script/style/nav
  content no longer leaks into "clean" markdown; HTTP-date `Retry-After`
  no longer crashes (and delays are capped); tiny pages no longer hard-fail
  after pointless retries; non-http(s) URL schemes (e.g. `file://`) are
  rejected; responses are decoded with the declared charset instead of
  hardcoded UTF-8; binary content types are skipped. robots.txt is now
  checked before every fetch by default (skip with `--no-robots`), so
  fetches disallowed by a site's robots.txt newly fail.
- The two frontmatter parsers (`bootstrap.sh` awk vs `manifest.py` regex)
  now agree on CRLF files and files without a trailing newline.
- `.fetch_cache/` added to `.gitignore`; placeholder User-Agent URL replaced
  with the real repository.

### Changed

- README quickstart demotes raw `curl | sh` in favor of inspect-first and
  tag-pinned installs; the Claude Code section documents plugin install and
  corrects the claim that `orchestrator` works as a delegatable subagent.
- Prompt templates gained filled worked examples; `task-briefing.md` is
  self-sufficient for cold-start agents and carries `BUDGET:` and
  `CONSTRAINTS:` lines.

## [1.0.0] - 2026-07-02

### Added

- Initial release: 8 skills (code-quality, deep-research, frontend-design,
  planning-and-decomposition, prompt-engineering, report-writing,
  self-verification, web-data-extraction), 6 agent roles (orchestrator,
  code-worker, researcher, reviewer, designer, report-writer), 5 prompt
  templates (task-briefing, handoff-report, plan-then-execute,
  self-review-rubric, verification-loop), the orchestration harness docs
  (`harness/patterns.md`, `harness/context-management.md`), the
  `manifest.py` lint/manifest script, and the `bootstrap.sh` installer.

[2.1.0]: https://github.com/tapiwamakandigona/subagent-toolkit/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/tapiwamakandigona/subagent-toolkit/compare/v1.1.0...v2.0.0
[1.1.0]: https://github.com/tapiwamakandigona/subagent-toolkit/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/tapiwamakandigona/subagent-toolkit/releases/tag/v1.0.0
