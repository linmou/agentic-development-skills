---
name: formalize-workflow-state-machine
description: Turn a natural-language or documented workflow into a source-verified state-machine proposal. Use when lifecycle phases, gates, failure paths, terminal conditions, or invariants must be formalized without silently changing semantics; generate bounded enforcement only after approval.
---

# Formalize Workflow State Machine

## Intent

Make a workflow's legal lifecycle inspectable without silently redesigning it or manufacturing a runtime framework it does not need.

## Workflow

1. Read the complete source workflow. Build an extraction ledger of phases, actions, gates, failure paths, terminal conditions, and invariants. Give every item a stable ID, kind, and exact source quote. Record actors on the actions or gates they control; do not turn an actor or activity into a state merely because it is a noun.

2. Map every extracted item to a state, transition, or invariant. Mark anything that cannot be mapped as unresolved ambiguity. A source-derived transition cites its source item IDs; an added state or transition names an explicit semantic change and reason.

3. Produce a proposal before editing the target. It must contain the extraction ledger, source-to-state mapping, legal transition table, invariants, coverage matrix, added semantics, unresolved ambiguities, and execution recommendation. Do not create scripts or patch the target in this step. Read [references/contract-format.md](references/contract-format.md) for the proposal contract.

4. Ask for approval when the proposal would change semantics, contains ambiguity, or lacks an execution-level choice. Unresolved ambiguity blocks executable generation. The choices are:

   - Documentation-only: add the approved transition table and invariants to the existing workflow document.
   - Validator-only: add a pure transition validator and tests; the caller owns persistence.
   - Persistent single-process runtime: generate state and transition scripts for one process at a time. Use this only when resume state has a stable instance identity and the workflow benefits from durable recovery.

5. After approval, implement only the chosen level. Do not add runtime state, logs, retries, leases, concurrency control, or external evidence verification unless the approved contract requires them and they can be tested deterministically.

6. For persistent single-process output, read [references/spec-format.md](references/spec-format.md) and use the bundled generator only with a reviewed, source-verified spec. Every gate must be fully represented by current state, actor, and required evidence presence. If a gate or invariant needs value inspection or workflow-specific logic, use validator-only output with approved deterministic checks instead.

   ```bash
   python scripts/create_state_machine_package.py --spec workflow_spec.json --output-dir workflow_state_machine
   ```

   The output directory must be new or empty. The generator refuses non-empty caller directories.

7. Verify the result against the source and the approved proposal. Test every transition, at least one path to every terminal state, invalid actors, invalid source states, missing required evidence references, terminal mutation, source provenance, extraction coverage, and output-directory safety.

## Persistent Runtime Boundary

The bundled runtime is intentionally small:

- It validates transition name, current state, actor, and non-empty evidence references.
- It rejects transitions out of terminal states and refuses to initialize over an existing state record. Reopening is not supported.
- It is single-process only. It provides no locks, compare-and-swap, duplicate suppression, concurrent-writer safety, verified external evidence, or crash-durable log transaction.
- A workflow that needs any of those properties needs a separately approved design; do not imply they exist through documentation.

## Required Proposal Contents

- inspected source path and source evidence
- extraction ledger with stable IDs, kinds, and exact quotes
- original phase/action to generated-state mapping
- every added state, named explicitly with its reason
- legal transitions, actor, gate, enforcement boundary, source references, and required evidence references
- initial and terminal states
- invalid moves and invariants
- coverage showing every extracted item is mapped exactly where its kind permits
- semantic changes and unresolved ambiguity
- recommended execution level with justification

## Resources

- [references/contract-format.md](references/contract-format.md): proposal and contract checklist.
- [references/spec-format.md](references/spec-format.md): reviewed JSON input for the optional persistent single-process generator.
- [scripts/create_state_machine_package.py](scripts/create_state_machine_package.py): safe generator for the persistent single-process level.
