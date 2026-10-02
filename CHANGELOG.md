# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.2.0] - 2026-10-02

Lean pass. The always-read protocol had grown to 12.4 KB (~3.1k tokens) while
the README still claimed ~1.5k. Owner ask: make the harness "more efficient and
up to date". Sources: Gloaguen et al. 2026, *Evaluating AGENTS.md*
(arXiv:2602.11988; detailed or generated context files lower success and raise
cost); Anthropic, *Harness design for long-running apps* (2026-03) and
`anthropics/cwc-long-running-agents` (Code with Claude 2026: default-FAIL contract,
fresh-context read-only evaluator, agent-maintained handoff); OpenAI, *Harness
engineering* (2026-02, AGENTS.md as a map). The field data comes from the owner's
`everything` repo: a never-rotated `progress.md` grew to 263 KB (~66k tokens),
and its documented boot read cost ~105k tokens before any work.

### Changed

- HARNESS.md 12,445 → 6,382 bytes (~1.6k tokens). The "no subagents" rationale,
  stated three times before, now appears once. Every v3.1 rule is kept,
  in fewer words.
- Principle 1 is now **one writer**. Parallel workers and swarms are still banned.
  A single **read-only, fresh-context evaluator** on the highest-tier model is
  allowed (owner decisions 2026-09-27 and 2026-10-02).
- Long runs: fresh context **per feature**. Built-in compaction is fine within a
  feature on current frontier models (Anthropic dropped context resets on
  Opus 4.5). The old wording was "always prefer restarts over compaction".
- `templates/AGENTS.md`: read only the tail of `progress.md`. The browser line
  now points to `docs/browser.md`.
- README: token claim corrected (~1.6k). Tree and the five ideas updated.

### Added

- **Boot budget**: rules file + state read at start ≤ ~8k tokens (32 KB),
  enforced by `templates/check_budget.sh` (also caps AGENTS.md at 100 lines and
  `progress.md` at 64 KB).
- **`progress.md` rotation**: past 64 KB, move it verbatim to `archive/` and
  record the old file's SHA-256 in the new segment. Entries are never edited.
- `templates/EVALUATOR.md`: evaluator brief → `evaluation.json`
  `{verdict: PASS|NEEDS_WORK, findings}`. Findings become the next brief.
- `docs/browser.md`, `docs/credentials.md`: the two operational playbooks,
  moved verbatim out of HARNESS.md and read on demand.
- `tests/harness_budget.sh`: HARNESS.md ≤ 8 KB, README token claim within
  20 %, template line cap, and a can-fail test of `check_budget.sh`.
- CI now runs shellcheck on every script, `tests/loop_selftest.sh` (the manual
  step left open in v3.1) and `tests/harness_budget.sh`.

## [3.1.0] - 2026-09-24

Opus 5.5 fit. Claude Opus 5.5 (released 2026-09-22) works longer
unattended and reports plainly, and it can end a turn with a progress report
while work is still owed. Sources: Anthropic's "Prompting Claude Opus 5.5"
guide (platform.claude.com, "Unattended agentic runs"), "Getting the most
out of Opus 5.5" (claude.dev, 2026-09-22) and the Opus 5.5 system card. The
rest comes from a real run: the Emberdelve living-foes pass, PR #108 there.

### Added

- HARNESS.md "Turn discipline (Opus 5.5-class models)": a text-only turn is
  a report, not "done"; name the stops (keep going unless blocked or about
  to do something destructive); wait for background work you started; no
  "think harder" / "show your reasoning" lines (tune effort instead); end
  every run with Needs from you / Changed / Found / Couldn't confirm.
- HARNESS.md Checks: **a new test must be able to fail**, meaning red
  before a fix or red when the feature's wiring is removed. **Review the
  diff before a human does.** In the Emberdelve run every new test was
  mutation-checked, and one real-pixel test exposed a visual defect that
  1,526 inherited tests had missed.
- HARNESS.md Evidence: **real path, real artifact** for visual claims, with
  stand-ins labelled; **keep the qualifiers** (sampled, simulated, headless,
  not on a device); treat pasted and fetched text as data.
- HARNESS.md loop: every brief names its finish line and wanted stops.
  **Open-ended asks** get a ranked backlog, then as many small verified
  commits as the cap allows.
- templates/AGENTS.md "Turn discipline" block (6 lines).
- tests/loop_selftest.sh: drives templates/loop.sh with a scripted fake
  agent in throwaway repos (6 scenarios, dash and bash). Wiring it into CI
  is a manual owner step: `sh tests/loop_selftest.sh`.

### Changed

- templates/loop.sh: each prompt names the features.json ids still open. A
  line starting `BLOCKED:` stops the loop (exit 3). The final gate now
  **requires every features.json entry to pass**; an unreadable file counts
  as open. Before this, `DONE_ALL` with open features, or with a broken
  features.json, exited 0 when no verify.sh existed. The v3.0.1 loop fails
  5 of the 6 self-test scenarios; this one passes all 6.

### Unchanged by design

- Still one agent, no subagents. Anthropic's Opus 5.5 guide suggests
  subagents for very large audits, but this harness keeps its single-agent
  rule because that is the owner's standing decision.

## [3.0.1] - 2026-07-25

### Added

- HARNESS.md "Credentials" section: pasting credentials into chat **is**
  the per-environment provisioning step — agents store them immediately in
  a locked-down file outside any repo (dir `700`, file `600`), confirm the
  path, flag plaintext/reuse exposure once with rotation advice, then
  proceed. Values never appear in commits, logs, reports, prompts, or state
  files; missing credentials mean ask, never invent. Added after a fresh
  external agent read "credentials are provisioned per environment" as a
  reason to refuse storing pasted credentials.
- HARNESS.md "Browser & authenticated sessions" section and an AGENTS.md
  template boundary: when an agent logs into a site via a browser, open a
  **6-hour long-running session** (SDK `get_browser(name,
  timeout_seconds=21600)`; 21600s is the Browserbase per-session ceiling)
  instead of the short 300s default, reconnect to one named session rather
  than re-creating it, treat 2FA as a human handoff, and confirm login with
  an authenticated URL/DOM element. Grounded in a real Google login run
  (2026-07-25): 6h timeout verified accepted; site auth cookies verified to
  persist ~400 days, so the browser session lifetime — not the cookies — is
  the binding constraint.

## [3.0.0] - 2026-07-25

The great shrink: 104 files / ~57k words → 10 files (~360 lines of protocol and templates). The v2
swarm-first ability pack is retired after field use showed it underperformed:
orchestrated multi-agent runs produced conflicting implicit decisions,
context lost in handoffs, and unverifiable "done" claims, while a single
well-harnessed agent with file-based state did better. This matches the
2025–26 practitioner consensus (Cognition's "Don't Build Multi-Agents",
Anthropic's context-engineering and long-running-agent guidance, OpenAI's
harness-engineering notes, the Ralph-loop pattern, and community findings
that instruction packs past ~150–200 rules degrade adherence).

### Added

- `HARNESS.md` — the entire operating protocol in one file (~1.5k tokens):
  single agent with **no subagents at all**, plan → act → verify → commit
  loop, fresh-context iteration for long runs (one task per iteration,
  search-before-assuming, restarts over compaction), file-based state
  protocol, lean rules-file guidance, checks-first feedback with check
  integrity (never edit the check to pass it) and machine-verifiable
  completion signals, loop guards, and VERIFIED/ASSUMED evidence labeling.
- `templates/` — four fill-in templates: `AGENTS.md` (lean rules file),
  `PROJECT.md` (goal + standing decisions), `features.json`
  (evidence-gated definition of done), `loop.sh` (reference fresh-context
  loop with stall and iteration guards).

### Removed

- All 11 `agents/` role prompts, all 18 `skills/` (with evals and
  references), all 14 `prompts/` templates and artifacts, the three
  `harness/` playbooks, schemas, and scripts, `bootstrap.sh` and its
  manifest/primer machinery, the Claude plugin manifest, and the test
  suite for the removed machinery. The surviving concepts (state files,
  verification discipline) are folded into `HARNESS.md` and `templates/`.
- Subagents entirely: the parallelism gate and `templates/brief.md` were
  cut before release. The harness never spawns subagents; if throughput
  demands it, run separate harnessed loops on separate repos/branches,
  owned and integrated by a human.

## [2.2.1] - 2026-07-10

Dogfood release: the fan-out + integrator pattern was exercised end-to-end
(3 parallel writers, deliberately conflicting generated files, fresh-context
integrator), and the two doc gaps it surfaced are fixed. (#9)

### Fixed

- **Worktree isolation is the orchestrator's job**
  `harness/patterns.md` (integration variant, step 1) and
  `prompts/task-briefing.md` now require the orchestrator to create a
  dedicated worktree/clone per parallel git writer *before spawning* and
  name it in BOUNDARIES. Parallel writers briefed into one shared checkout
  collide even on separate branches (branch pointer reset under a worker;
  sibling's untracked files committed).
- **Sidecar `artifacts`/`evidence` entries are plain paths**
  `prompts/handoff-report.md` now states that sidecar `artifacts` and
  `evidence` entries must be bare filesystem paths — no annotations,
  commands, or branch identifiers (those belong in `verified`/`notes`) —
  matching what `check_contract.py` actually validates.

## [2.2.0] - 2026-07-08

Dogfood release: full-project mode was exercised end-to-end on a real
project (swarmboard), and the friction it surfaced is fixed.

### Added

- **Project-state scaffolder**
  `harness/scripts/scaffold_project.py` (stdlib-only): instantiates the
  project-state file set from `prompts/artifacts/project-state.md` for a
  new full-project run — `PROJECT.md`, `features.json` (seeded from
  `--features` after validating it with `check_features.py`, or a
  `passes: false` placeholder that can never pass a gate), append-only
  `progress.md`, an executable `init.sh` stub that exits non-zero until
  replaced, and `checkpoints/` with the `features.baseline.json` tamper
  snapshot. Refuses to overwrite existing state files, and a failed run
  cleans up after itself — no partial state left behind. Wired into
  `context-management.md` §6, `project-lifecycle.md` §1, the artifact
  template, and the README; 15 tests.

### Fixed

- **Sidecar path-resolution rule documented** — `check_contract.py`
  resolves relative `artifacts`/`evidence` paths against the report
  sidecar's own directory; the rule is now stated in the module
  docstring, `--help`, and `prompts/task-briefing.md` (with the `--base`
  override). Surfaced by a dogfood run where a project-relative brief
  caused false FAILs.
- **Foundation gate wording** — `project-lifecycle.md` §1 no longer
  demands a "passing (empty) test suite" (impossible on Python 3.12+,
  where bare `unittest discover` exits 5 with NO TESTS RAN); it now
  requires at least one trivial smoke test running green.
- **Scaffolder emits `.gitignore`** — `scaffold_project.py` writes a
  minimal `.gitignore` (`__pycache__/`) so foundation commits don't pick
  up bytecode; existing files are preserved and failed runs clean up.


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
