# Agent Failure Taxonomy

A checklist of failure modes commonly observed in autonomous agent output, with detection tactics. Use as a pre-submit sweep: skim each category, ask "could this be me right now?"

## 1. Completion failures

| Failure | Description | Detection |
|---|---|---|
| Partial completion | N of M requested items done; success reported | Re-read the request; enumerate every deliverable; tick each off against actual artifacts |
| Nearby-question answering | Answered an easier, related question | Quote the original question next to your TL;DR; do they match? |
| Silent scope reduction | Quietly narrowed the task when it got hard | Diff your delivered scope against the requested scope; disclose any gap |
| Abandoned thread | Started a sub-task mid-run, never finished it | Grep your own notes/plan for open loops |

## 2. Fabrication failures

| Failure | Description | Detection |
|---|---|---|
| Invented specifics | Made-up numbers, dates, version strings, filenames | For each specific value: "where exactly did this come from?" |
| Phantom APIs | Called functions/flags/endpoints that don't exist | Run the code; check docs for every API you didn't personally verify |
| Citation laundering | Real-looking citation that doesn't support the claim | Open the cited page; find the sentence that supports the claim |
| Confident interpolation | Filled a knowledge gap with a plausible guess, stated as fact | Hedge or verify anything you didn't observe or read directly |

## 3. Testing failures

| Failure | Description | Detection |
|---|---|---|
| Happy-path only | Works on the demo input | Test: empty input, huge input, unicode, zero, negative, missing fields |
| Success-message trust | Tool said "OK", artifact never checked | Open/read/list the actual artifact after every side effect |
| Test the fix, break the rest | Patch fixes bug A, regresses B | Run the full suite / re-check adjacent behavior, not just the fix |
| Verified once, changed after | Edits made after last verification | Any change after your last check invalidates the check — re-run it |

## 4. Instruction failures

| Failure | Description | Detection |
|---|---|---|
| Format drift | Wrong format/length/structure vs. explicit instructions | Re-read constraints from the *original* message, not memory |
| Constraint decay | Early constraint ("don't touch X", "under 500 words") forgotten late | Keep constraints in your plan header; check at every milestone |
| Over-delivery | Unrequested extras that add risk or noise | For each extra: did anyone ask? Does it add risk? |
| Tone mismatch | Casual where formal needed, or vice versa | Consider the audience named in the request |

## 5. Reasoning failures

| Failure | Description | Detection |
|---|---|---|
| Anchoring | First hypothesis never re-examined despite counter-evidence | List evidence *against* your conclusion; if you can't find any, you didn't look |
| Unit/magnitude errors | Off by 1000×, mixed units, percent-vs-points | Sanity-check every headline number against a known reference |
| Internal inconsistency | Sections of output contradict each other | Read the whole deliverable end-to-end once, in order |
| Stale context | Acting on information that changed mid-task | Re-check volatile facts (file contents, states, prices) before final use |

## 6. Visual/artifact failures

| Failure | Description | Detection |
|---|---|---|
| Never rendered | Shipped HTML/PDF/chart based on source code only | Render and look, always |
| Overflow/clipping | Long content breaks layout | Test with the longest real data, not lorem ipsum |
| Broken references | Dead links, missing images, wrong paths | Click every link; open every referenced file |
| Page-2 problem | First page fine, later pages broken | Inspect the entire artifact, not just the top |
