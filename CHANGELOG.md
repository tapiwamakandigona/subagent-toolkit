# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[1.1.0]: https://github.com/tapiwamakandigona/subagent-toolkit/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/tapiwamakandigona/subagent-toolkit/releases/tag/v1.0.0
