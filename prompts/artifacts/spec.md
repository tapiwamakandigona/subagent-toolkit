# Artifact: Product Spec

The required skeleton for a product spec — the output of the Spec phase (usually `../../agents/product-manager.md`) and the input to Architecture. Every phase handoff gets an enforced artifact shape like this one: structured intermediate artifacts raise downstream success rates far more than better role prose does.

## Usage notes

- Fill every section; write "none" deliberately rather than deleting a heading — a missing section reads as an unmade decision.
- Acceptance criteria must be machine-checkable: a command, an observable behavior, or an assertable state. If no machine could ever evaluate it, rewrite it until one could.
- The assumptions log is the escape valve: decisions made without a human go here with reasons, so the spec never stalls on a question that a logged assumption could answer.
- Downstream consumers: the architect reads all of it; builder briefs pin individual requirements verbatim; QA derives its test plan from the criteria alone.

## Template

```text
# Spec: {{project_name}}
Status: {{draft | approved}}   Approved by: {{who_or_pending_gate}}   Date: {{date}}

## Problem
{{one_paragraph — who hurts, how, today}}

## Users
{{primary_user_and_context — who they are, what they know, where they use this}}

## Scope
In:  {{bullet_list_of_whats_included}}
Out: {{bullet_list_of_tempting_adjacent_features_explicitly_excluded}}

## Functional requirements
FR-1: {{requirement_statement}}
  Acceptance: {{machine_checkable_criterion — command, HTTP behavior, or assertable state}}
FR-2: {{...}}
  Acceptance: {{...}}
{{continue_numbering — one acceptance criterion per requirement}}

## Non-goals
{{things_a_reasonable_builder_might_assume_are_wanted_but_arent}}

## Milestones
M1: {{smallest_demonstrable_slice}} — delivers {{FR_ids}}
M2: {{next_slice}} — delivers {{FR_ids}}

## Risks
{{risk — likelihood, impact, and who owns watching it}}

## Open questions & assumptions log
Q-1 [{{gate | assumed}}]: {{question}} → {{answer_or_logged_assumption_with_reason}}
```

## Anti-patterns

- **Vibes criteria** — "fast", "intuitive", "robust" are aspirations; give the number, the behavior, or the command.
- **Scope by omission** — if the out-list is empty, the scope line hasn't been drawn.
- **Implementation smuggling** — "store it in Postgres" is the architect's call unless the requester mandated it; record mandates as constraints.
- **Unanswered open questions at approval** — every Q is either answered, assumed-with-reason, or explicitly parked at a named gate.
