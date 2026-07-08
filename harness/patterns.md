# Orchestration Patterns

Named patterns for coordinating subagents. Pick the pattern **before** spawning anything — retrofitting coordination onto already-running agents is where orchestration goes to die. Each pattern below states when to use it, how it works, and how it characteristically fails.

Pair this with [`context-management.md`](context-management.md) (what goes into a brief) and the templates in [`../prompts/`](../prompts/) (how to write the brief and read the report).

---

## 1. Plan → Delegate → Verify

The default backbone. Everything else is a variation.

**When:** any task worth delegating at all.

**How:**
1. **Plan** — orchestrator decomposes the goal into tasks with written definitions of done (use `../prompts/plan-then-execute.md` on yourself).
2. **Delegate** — one brief per task (`../prompts/task-briefing.md`), each naming a role from `../agents/` and a report format (`../prompts/handoff-report.md`).
3. **Verify** — orchestrator independently checks each result against the *brief*, not the report (`../prompts/verification-loop.md`), then integrates.

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

**When path ownership can't partition the work** — real codebases have inherently shared files (lockfiles, `package.json`, route tables, migrations, DI registries). Don't force a partition that doesn't exist; switch to the integration pattern:

1. **Isolate writers**: one branch or worktree per agent. The **single-writer rule** still holds inside each isolation unit — at most one agent may write a given path set at a time; every other parallel agent is a reader, advisor, or verifier.
2. **Freeze the interfaces** the parallel work shares before spawning (publish them verbatim in every brief, from the architecture artifact if one exists — see [`project-lifecycle.md`](project-lifecycle.md)). Writers may not change a frozen interface; a needed change goes back to the orchestrator as a report, not an edit.
3. **Serialize integration.** The orchestrator (or a dedicated integrator role) merges branches **one at a time, in a deliberate order** — foundations first, then dependents. Never merge in parallel or "whichever finishes first".
4. **Resolve conflicts in fresh context.** A merge conflict is its own task for an agent that saw neither writer's transcript — it judges from the diff, the interfaces, and the briefs.
5. **Regenerate, don't hand-merge, generated and shared files** (lockfiles, route tables, migration indexes): the integrator re-runs the generator after each merge instead of textually reconciling two generated versions.

**Failure modes:**
- *Ownership overlap.* Two agents editing one file without branch isolation is a planning bug; last-writer-wins destroys work silently. Default to disjoint path ownership; when that's impossible, use the integration pattern above — never "both edit and hope".
- *Hidden coupling.* Tasks that look independent but share an interface (naming scheme, data format). Pin the interface in every brief ("skill folders are named lowercase-hyphens; frontmatter keys are exactly `name`, `description`").
- *Fan-out for its own sake.* Two coupled tasks run in parallel produce two half-answers plus a reconciliation task. When in doubt, pipeline.
- *Actions carry implicit decisions.* Every edit or output embeds choices (naming, structure, interpretation) the brief didn't specify. Parallel writers each decide differently, and the conflicts surface only at integration. This is why fan-out suits read-heavy work and betrays write-heavy work — see "When NOT to multi-agent" below.
- *Uneven task sizes.* One 3-hour task among five 10-minute tasks means you wait 3 hours anyway. Split the big one or start it first.

**Variations:**
- **Delta shard (mid-run scope addition).** When the goal grows *while* a fan-out is running ("also cover X"), don't re-brief running agents — their briefs are immutable in practice and mid-flight edits produce half-old, half-new work. Spawn one new shard scoped explicitly to the *difference* ("only what differs about X vs. the areas siblings already own; their scopes are excluded — assume their coverage exists"). Cheap, conflict-free, and the integration step already exists.
- **Convergence check (research fan-outs).** For read-only fan-outs, verification has a cheap extra tool: compare *independent* shards' claims about the same load-bearing facts (dates, prices, limits, policy). Independent agreement from disjoint source sets is strong evidence; disagreement marks exactly where the orchestrator must dig before integrating. Contradictions a shard itself flags in its sources are findings to preserve, not defects to reconcile away. This supplements — never replaces — artifact checks, and only works if shards were briefed on disjoint scopes with independent sourcing.

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
1. Producer agent builds the artifact (any role in `../agents/`).
2. A **separate** reviewer agent (`../agents/reviewer.md`) reviews against the original brief and returns APPROVE / APPROVE-WITH-FIXES / REJECT with located findings.
3. On non-approval, producer addresses findings (with the review in its brief) and resubmits.
4. Cap at ≤3 rounds. Non-convergence means the brief is wrong or the approach is — escalate, don't loop.

**Failure modes:**
- *Self-review masquerading as review.* The same agent (or same context window) reviewing its own work inherits its own blind spots. Independence is the entire point.
- *Reviewer without the brief.* A reviewer judging only the artifact will polish a solution to the wrong problem. The reviewer gets the original requirements, always.
- *Nit loops.* Rounds spent on [Nit]-severity findings. Only [Blocking] findings force a new round.
- *Producer relitigating.* The producer's job on REJECT is to fix or escalate — not to argue with the reviewer inside the loop.

---

## 5. Failure & recovery

**When:** always — every pattern above assumes subagents return usable reports, and eventually one won't.

**How — classify the failure first; the class picks the response:**

| Class | Symptom | Response |
|---|---|---|
| **Stalled** | no report within the timebox | put the timebox in the brief at spawn time (most harnesses can't kill a running agent); treat overdue as Malformed — inspect the trace dir and artifacts, salvage or retry once with a tighter scope |
| **Failed** | report says the approach didn't work | retry once with a *sharpened* brief that cites the failure verbatim and rules out the dead end |
| **Blocked** | report says a dependency/permission/path is missing | fix the blocker yourself (it's usually a briefing bug), then re-run; don't re-brief the same hole |
| **Malformed** | empty, truncated, or off-format report but artifacts may exist | inspect the artifacts directly; if usable, salvage and note it; if not, treat as Failed |

1. **One retry, maximum.** The retry brief is a rework round (see the variant in `../prompts/task-briefing.md`): it names what failed, quotes the failing check or finding, and narrows the definition of done. A retry with the same brief is a coin flip, not a plan.
2. **After the failed retry, change the plan, not the brief:** reassign to a different role/model, descope the task and note it, or escalate to your own requester. Say which you chose and why.
3. **Kill criteria — decide them at planning time, not mid-crisis:** total budget (time/tokens) for the run, max retries per task (one), and max fraction of tasks failing before you stop spawning and replan (a third of a fan-out failing means the partition is wrong).

**Failure modes:**
- *Retry loops.* Retrying more than once without changing the plan burns budget on hope. Two failures is evidence about the plan.
- *Silent descoping.* Dropping a failed task without a note in the final answer turns a known gap into a hidden one.
- *Salvage neglect.* A malformed report often sits on top of perfectly good artifacts. Check the disk before re-running the work.

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

### When NOT to multi-agent

Default to a single agent; multi-agent is the exception you justify.

- **Single-threaded first.** If one focused agent can finish inside its context window and your deadline, delegation only adds briefing overhead, integration work, and new failure modes. A multi-agent run commonly burns ~15× the tokens of a single-agent chat — the value of the result has to carry that.
- **Parallelize read-heavy, serialize write-heavy.** Research, review, and data-gathering fan out well — reads don't conflict. Coding, design, and anything where outputs must fit together serialize better, because actions carry implicit decisions (pattern 2) and parallel writers make them differently. Extra agents contribute intelligence (research, review, advice) more safely than actions (edits).
- **Coupled tasks are one task.** If two tasks share an interface you can't pin verbatim in both briefs, they aren't independent — pipeline them or merge them.

### Budgets & effort scaling

Agents overspend when effort isn't stated. Put explicit numbers in every brief (the BUDGET line in `../prompts/task-briefing.md`) and scale them to the task class:

| Task class | Agents | Budget per agent |
|---|---|---|
| Trivial (lookup, one-file tweak) | 0 — do it yourself | — |
| Simple fact-find or bounded fix | 1 | ~3–10 tool calls |
| Comparison / multi-source question | 2–4 | ~10–15 calls each |
| Genuinely wide, disjoint shards | 5+ (rare) | stated per shard |
| Engineering milestone (build + verify a feature set) | 1 writer + readers/verifiers | a per-milestone envelope — often hundreds of calls; state it, plus a timebox, in the brief |

When in doubt, fewer agents with bigger budgets beats more agents with vague ones.

- **Timeboxing over killing:** put the timebox in the brief; treat overdue as Malformed (§5). Don't plan around a kill switch you may not have.
- **Per-milestone envelopes:** for project-scale work, budget at the milestone level (see [`project-lifecycle.md`](project-lifecycle.md)) and let the milestone's orchestrating brief subdivide it, rather than guessing per-task numbers up front.
- **Stop criteria:** every budget names what happens at exhaustion — report partial results and stop. An agent that "pushes on to finish" past budget is defecting, not being diligent.

### Loop guards

Unbounded loops are how runs die quietly. Decide these caps at planning time and write them into the plan:

- **Review cycles ≤ 3.** A producer/reviewer pair that hasn't converged in three rounds has a wrong brief or a wrong approach — escalate, don't run round four.
- **No-progress detection.** Two consecutive iterations with no diff and no test-result delta means the agent is spinning: halt that line of work and replan. Repetition is evidence, not persistence.
- **Iteration and budget caps on every loop** (retry loops, fix loops, polling loops), each with a named action at the cap — report partial, escalate, or descope with a note.
- **Risk-tiered action gating.** Read-only actions: automatic. Workspace writes inside owned paths: automatic. Destructive operations, production systems, spending money: human gate — a named pause for approval, never a prompt-level "be careful". Deny by default what you can't undo.

### Tracing: file-based run logs

Multi-agent failures are undebuggable without a trace. The no-infra convention:

- The orchestrator assigns a **run ID** at planning time and puts it in every brief (the RUN_ID line in `../prompts/task-briefing.md`).
- The orchestrator also picks an **absolute base path** for the trace tree and puts it in every brief. Agents spawned in different working directories writing to a relative `runs/` scatter the trace; the absolute path is what keeps it one tree.
- Each subagent writes only inside **its own directory**, `<base>/runs/<run-id>/<agent-slug>/` — its report, key intermediate artifacts, and (on failure) whatever it had. Per-agent directories are what let ten parallel agents trace without filename collisions.
- The orchestrator keeps `<base>/runs/<run-id>/decisions.md`: one line per delegation, verification outcome, retry, and descope, as they happen.
- Reports cite the trace path, so any later agent (or human) can reconstruct the run from disk alone.

---

Three rules worth restating: default to a single agent and justify every additional one; at most one writer per path set at a time; cap every loop and name what happens at the cap.
