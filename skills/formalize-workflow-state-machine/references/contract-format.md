# State-Machine Proposal Format

Intent: Keep formalization reviewable before it becomes code. Write facts from the source once, then make any change from those facts explicit.

## Proposal Sections

1. Intent: why explicit lifecycle rules help this workflow.
2. Source extraction ledger: one stable ID, kind, and exact quote for every phase, action, gate, failure path, terminal condition, and invariant.
3. States: initial, terminal, source-derived states with source IDs, and explicitly added states with approved reasons.
4. Transitions: name, from, to, actor, gate, enforcement boundary, required evidence references, source IDs, and any semantic-change reason.
5. Invariants and invalid moves: conditions that must always hold and meaningful rejected moves.
6. Coverage matrix: every extraction-ledger item maps to a compatible state, transition, or invariant; omissions remain visible.
7. Semantic changes and unresolved ambiguities: do not hide either.
8. Execution-level recommendation: documentation-only, validator-only, or persistent single-process runtime, with justification.

## Mapping Rules

- A phase maps to a state.
- An action maps to its containing state or the transition it performs.
- A gate or failure path maps to a transition.
- A terminal condition maps to a terminal state or an incoming terminal transition.
- An invariant maps to the invariant list.
- An actor is recorded on the transition it is allowed to perform.
- An item that cannot be mapped stays unresolved; do not invent a mapping to make the table complete.

For persistent generation, classify each gate as `none` or `required_evidence_presence`. Any gate requiring value inspection, timing, external verification, or workflow-specific predicates exceeds the bundled runtime and requires validator-only output or a separately approved design.

## Approval Gate

Do not patch the target workflow or generate code until the user approves the proposal and, when relevant, its execution level. Do not generate executable output while unresolved ambiguities remain.

## KISS Checks

- Every state has a source reason or an explicit added-state reason.
- Every source item is mapped according to its kind or remains visibly unresolved.
- Every transition is source-derived or names an approved semantic change.
- No implementation claim exceeds the selected execution level.
- Evidence references are called references unless code verifies them.
- Runtime persistence is not added merely to make the output look formal.
- A persistent runtime states its single-process boundary plainly.
