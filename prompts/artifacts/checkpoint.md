# Artifact: Checkpoint

A phase-boundary snapshot of project state, written by the orchestrator to `checkpoints/NN-<phase>.md`. A checkpoint is what makes long runs survivable: a successor (or a fork) re-briefs from the latest checkpoint plus the state files, never from the dying context window.

## Usage notes

- Write one at every phase boundary of `../../harness/project-lifecycle.md`, on orchestrator succession (see `../../harness/context-management.md`), and before any human gate.
- Decisions carry reasons. A successor who knows *what* was decided but not *why* will relitigate it — recording the reason is what kills the loop.
- Artifact paths, not artifact contents: the checkpoint is a map, and the state files (spec, architecture, task list, features.json, progress log) remain the territory.
- Resume = read the latest checkpoint, then the artifacts it points to, then act. Fork = copy a checkpoint, edit the decisions you're revisiting, and re-brief from the copy — the original history stays intact.

## Template

```text
# Checkpoint {{NN}}: {{phase_name}}
Run: {{run_id}}   Date: {{date}}   Written by: {{agent}}

## Phase & gate result
{{phase_just_completed}} — gate: {{go | no-go | human_gate_pending}}
{{one_line_of_gate_evidence — what passed, what was demonstrated}}

## Decisions this phase (with reasons)
- {{decision}} — because {{reason}}; alternatives rejected: {{brief}}
- {{...}}

## Artifact map
Spec: {{path}}   Architecture: {{path}}   Task list: {{path}}
Features: {{path_to_features_json}}   Progress log: {{path}}
Other: {{phase_outputs_with_paths}}

## Open items
- {{unfinished_or_deferred_item}} — owner: {{who}}, blocking: {{yes/no}}

## Next step
{{the_single_next_action — precise enough that a cold successor starts correctly}}
```

## Anti-patterns

- **Checkpoint as diary** — a narrative of what happened buries the state; a successor needs decisions, artifacts, and the next step.
- **Decisions without reasons** — invites relitigation and contradictory re-decisions downstream.
- **Pointing at context** — "as discussed above" is dead text to every future reader; checkpoints reference files only.
- **Skipping the no-go** — a failed gate is exactly when the checkpoint matters most; record what failed and why before replanning.
