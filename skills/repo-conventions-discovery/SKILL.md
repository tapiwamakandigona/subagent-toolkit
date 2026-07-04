---
name: repo-conventions-discovery
description: The "read the agent doc first" protocol for working in an existing repository — locating and fully reading agent-facing state docs (AGENTS.md, AI_CONTEXT.md, HANDOFF.md, plans.md, and kin) before any edit, extracting machine-checkable constraints into task notes, following the repo's commit and branch conventions, and updating the agent docs after shipping. Use at the start of any task that edits a repo you did not create in this session.
license: MIT
metadata:
  version: "2.0.0"
---

# Repo Conventions Discovery

Actively maintained repos accumulate an **agent-facing state doc**: a file written specifically for the next AI assistant (or new contributor) that encodes architecture, hard constraints, and the current plan. Agents that skip it violate constraints the repo spelled out in plain text — introducing a build step into a deliberately buildless repo, adding server features to a static-export app, bumping a pinned toolchain. Reading it costs five minutes; violating it costs a revert.

## 1. Locate and read the agent doc — before any edit

Search the repo root (and `docs/`) for these, in roughly descending authority:

```
AGENTS.md  CLAUDE.md  AI_CONTEXT.md  HANDOFF.md
plans.md  PLAN.md  docs/PLAN.md  ROADMAP.md  todo.md
```

Rules:

- **Read the whole file, top to bottom** — these docs are written expecting exactly that ("new assistants should read this before doing anything" is a common opening line). Skimming misses the one constraint that matters.
- Several may coexist with different jobs: architecture/constraints doc, goal/ownership doc, living plan, task list. Read all that exist; they're short.
- **Agent docs outrank READMEs, and both outrank the hosting platform's repo description.** READMEs and descriptions go stale — a README may claim CDN-loaded dependencies while the agent doc and the `vendor/` tree show everything vendored; a repo description may name a stack the codebase migrated away from entirely. When sources conflict: agent doc > code itself > README > repo description. Verify against the code when it matters.
- No agent doc? Reconstruct the conventions from the CI workflows, the last ~10 commit subjects, and the config files — then note in your report that the repo lacks one (adding one is often a welcome first contribution).

## 2. Extract machine-checkable constraints

Turn the doc's prose constraints into a checklist in your task notes, phrased so they can be re-checked mechanically pre-handoff. Common ones:

| Constraint (prose) | Pre-handoff check |
|---|---|
| "No build step — deploy uploads the tree verbatim" | Diff contains no package.json/bundler config/compiled-language files; no new bare imports or CDN tags |
| "Static export only" | Export-forbidden features absent; build still emits the static output dir |
| "Toolchain pinned (framework/SDK version X)" | No version bumps in lockfiles/CI; code uses only APIs available in X |
| "Wire-protocol compatible with <external protocol> vN" | Protocol-touching changes covered by compatibility tests; no message-shape changes |
| "Deploy via local key file, not CI" | No CI deploy workflow added |

**Re-run this checklist before handoff**, not just at the start — constraints are violated mid-task, when the doc is long forgotten. Copy the constraints into your handoff report so the next agent inherits them.

## 3. Follow the repo's change conventions

Match how the repo actually changes, visible in its history:

- **Commit subjects**: if the log shows conventional commits (`feat:`, `fix:`, `perf:`, `docs:`, `ci:`), write yours the same way. Mirror the observed style even if it's something else.
- **Branch names encode intent**: repos often use prefixes like `feat/*`, `fix/*`, `release/*`, or agent-run prefixes. Use the established pattern; CI may whitelist specific prefixes.
- **PR-based merges**: many solo-maintained repos still merge via PR — it's the review point and the history unit. Don't push to the default branch directly if history shows merges arrive as PRs.
- Mirror surrounding code style rather than imposing your own; run the repo's own format/lint gate if one exists.

## 4. Update the state docs after shipping

The agent doc is only authoritative because previous agents kept it current — do your part:

- **Agent doc / plan**: mark shipped items done, record new constraints or architecture changes you introduced, note anything the next agent must know.
- **CHANGELOG**: add an entry in the existing format.
- **ROADMAP/todo**: check off the item you shipped; don't silently reorder the rest.

A shipped change with stale docs recreates the exact failure this skill exists to prevent.

## 5. The operating loop

Repos with agent docs usually expect this cadence, sometimes stated verbatim:

```
pick ONE increment (top unchecked roadmap item unless told otherwise)
→ implement → verify with the repo's own harnesses/tests
→ update agent doc + CHANGELOG/ROADMAP → deploy → confirm live
→ NEVER leave the default branch broken
```

One verified increment beats three unverified ones. If your increment can't be verified with the repo's affordances, say so in the report instead of shipping on faith.

## Pre-edit checklist

- [ ] Agent-facing docs located and read in full (or their absence noted)
- [ ] Constraints extracted as machine-checkable items in task notes
- [ ] Conflicts between doc/README/description resolved in the doc's favor and verified against code
- [ ] Commit/branch/PR conventions identified from history
- [ ] (Pre-handoff) constraint checklist re-run; state docs updated
