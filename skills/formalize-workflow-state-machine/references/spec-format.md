# State-Machine Spec Format

Intent: Define the reviewed JSON input for the optional persistent single-process generator. A spec is implementation input, not a substitute for source inspection and approval.

## Source Summary

`source_summary` requires:

- `source_path`: UTF-8 workflow path, resolved relative to the JSON spec unless absolute.
- `source_sha256`: lowercase SHA-256 of the exact inspected source bytes.
- `source_items`: a non-empty extraction ledger. Every item has a unique `id`, a `kind`, and an exact `quote` that occurs once in the source.
- `original_states`: a non-empty list of source phase mappings. Every item has `name`, `mapped_state`, and non-empty `source_refs` containing at least one `phase` item.
- `invariants`: a list of `{name, rule, source_refs}` objects. Each invariant references at least one `invariant` source item.
- `semantic_changes`: approved changes introduced during formalization; use `[]` when none were introduced.
- `unresolved_ambiguities`: unresolved source questions. Persistent generation requires `[]`.
- `added_states`: `{name, reason}` objects for states without source mappings. Each reason must exactly match an approved `semantic_changes` item.

Allowed source-item kinds are `phase`, `action`, `gate`, `failure_path`, `terminal_condition`, and `invariant`. Every item must be consumed by a compatible state, transition, or invariant mapping. Every generated state must be source-mapped or explicitly added.

## Workflow Fields

- `workflow_name`, `purpose`, `actors`, `states`, `initial_state`, `terminal_states`, and `transitions` are required.
- Every transition has `name`, `from`, `to`, `actor`, `required_evidence`, `gate`, `gate_enforcement`, `source_refs`, and `semantic_change`.
- `required_evidence` may be `[]` only for a bookkeeping transition. Otherwise it contains durable reference names, not verified proofs.
- `gate_enforcement` is `none` only when `gate` is `none` and no evidence is required. Otherwise it is `required_evidence_presence`, with a described gate, at least one evidence key, and a referenced `gate` source item.
- A source-derived transition has non-empty `source_refs`. A source-free transition names a `semantic_change` already approved in `source_summary.semantic_changes`.
- Terminal states have no outgoing transitions in this runtime.

## Structural Rules

- Every state must be reachable from `initial_state`.
- Every non-terminal state must have an outgoing transition.
- Every terminal state must be reachable.
- Every source-derived terminal state cites a `terminal_condition` through the state mapping or an incoming transition.
- The generator refuses a non-empty output directory and does not replace or delete it.
- Generated validator tests cover every transition and meaningful invalid inputs.
- Generated runtime tests execute one path from the initial state to every terminal state and prove initialization cannot reset the resulting state record.

## Runtime Limit

Generated scripts are for one process at a time. They validate state, actor, transition, and non-empty evidence references. They do not interpret evidence values, enforce prose invariants, inspect external paths, coordinate locks, suppress duplicate actions, or provide crash-durable transactions. If a source gate needs any omitted capability, do not use the persistent generator for that proposal.
