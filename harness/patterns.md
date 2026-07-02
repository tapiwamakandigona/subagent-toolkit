# Orchestration Patterns

Named patterns for coordinating subagents. Pick the pattern **before** spawning anything — retrofitting coordination onto already-running agents is where orchestration goes to die. Each pattern below states when to use it, how it works, and how it characteristically fails.

Pair this with [`context-management.md`](context-management.md) (what goes into a brief) and the templates in [`../prompts/`](../prompts/) (how to write the brief and read the report).

---

## 1. Plan → Delegate → Verify

The default backbone. Everything else is a variation.

**When:** any task worth delegating at all.

**How:**
1. **Plan** — orchestrator decomposes the goal into tasks with written definitions of done (use `prompts/plan-then-execute.md` on yourself).
2. **Delegate** — one brief per task (`prompts/task-briefing.md`), each naming a role from `agents/` and a report format (`prompts/handoff-report.md`).
3. **Verify** — orchestrator independently checks each result against the *brief*, not the report (`prompts/verification-loop.md`), then integrates.

**Failure modes:**
- *Trusting reports.* Subagents report success optimistically. Verification against artifacts is not optional.
- *Ambiguity passed downward.* If the orchestrator can't write a definition of done, the subagent certainly can't infer one. Resolve ambiguity before delegating.
- *Integration as an afterthought.* Budget explicit time for merging results; two individually-correct outputs can still contradict each other.

---

## 2. Parallel Fan-Out with Path Ownership

**When:** tasks are independent and touch *disjoint* artifacts — building different directories of a repo, researching different questions, processing different data shards. This is the biggest wall-clock win available.

**How:**
1. Partition the work so every file/directory/resource has **exactly one owner**. Write the ownership map before spawning.
2. Each brief states the agent's owned paths and explicitly forbids writing elsewhere ("if the right fix is outside your paths, stop and report").
3. Spawn all agents at once; collect reports; verify each; integrate.
4. Shared files (a README both agents' work feeds into, an index) are owned by the **orchestrator** or by exactly one agent — never "whoever gets there first".

**Failure modes:**
- *Ownership overlap.* Two agents editing one file is a planning bug; last-writer-wins destroys work silently. There is no acceptable merge strategy — fix the partition.
- *Hidden coupling.* Tasks that look independent but share an interface (naming scheme, data format). Pin the interface in every brief ("skill folders are named lowercase-hyphens; frontmatter keys are exactly `name`, `description`").
- *Fan-out for its own sake.* Two coupled tasks run in parallel produce two half-answers plus a reconciliation task. When in doubt, pipeline.
- *Uneven task sizes.* One 3-hour task among five 10-minute tasks means you wait 3 hours anyway. Split the big one or start it first.

---

## 3. Pipeline

**When:** stages have a strict data dependency and benefit from different roles/models: research → build → review → report is the classic.

**How:**
1. Define each stage's **output contract** — the exact artifact shape stage N hands to stage N+1 (a findings file with citations; code with passing tests; a review verdict).
2. Run stages sequentially, each as a fresh agent with the previous stage's artifact paths in its brief.
3. Insert a cheap validity check between stages (does the file exist, parse, meet the contract?) — catching contract violations at the seam costs minutes; catching them two stages later costs the run.

**Failure modes:**
- *Error amplification.* A subtly wrong stage-1 output becomes a confidently wrong stage-3 output. The inter-stage check is the immune system; don't skip it.
- *Contract drift.* Stage 2 "helpfully" outputs a different format than stage 3 expects. Contracts belong in briefs verbatim, not paraphrased.
- *Context smuggling.* Passing the entire stage-1 transcript to stage 2 instead of its distilled artifact. Pass artifacts, not histories.

---

## 4. Critic Loop (Producer / Reviewer)

**When:** quality matters more than latency, and defects are cheaper to catch than to ship: user-facing deliverables, risky code changes, published documents.

**How:**
1. Producer agent builds the artifact (any role in `agents/`).
2. A **separate** reviewer agent (`agents/reviewer.md`) reviews against the original brief and returns APPROVE / APPROVE-WITH-FIXES / REJECT with located findings.
3. On non-approval, producer addresses findings (with the review in its brief) and resubmits.
4. Cap at 2–3 rounds. Non-convergence means the brief is wrong or the approach is — escalate, don't loop.

**Failure modes:**
- *Self-review masquerading as review.* The same agent (or same context window) reviewing its own work inherits its own blind spots. Independence is the entire point.
- *Reviewer without the brief.* A reviewer judging only the artifact will polish a solution to the wrong problem. The reviewer gets the original requirements, always.
- *Nit loops.* Rounds spent on [Nit]-severity findings. Only [Blocking] findings force a new round.
- *Producer relitigating.* The producer's job on REJECT is to fix or escalate — not to argue with the reviewer inside the loop.

---

## Choosing a pattern

| Situation | Pattern |
|---|---|
| One nontrivial task | Plan → Delegate → Verify (single worker) |
| Independent tasks, disjoint artifacts | Parallel fan-out with path ownership |
| Stages feed each other | Pipeline |
| High-stakes deliverable | Critic loop (wrapped around any of the above) |
| Independent tasks *then* synthesis | Fan-out → pipeline into `report-writer` |

Patterns compose: a pipeline stage can itself fan out; a critic loop can gate a pipeline's final stage. Compose deliberately and write the composition down in your plan — if you can't draw the flow in five boxes, simplify it.
