# Drift Verification

## Contents

- Verify semantics, not timing
- Define invariants
- Compare against the serial reference
- Use scenario suites
- Use replay and shadow mode
- Check metamorphic properties
- Check monitor-specific robustness

## Verify semantics, not timing

Do not require identical execution order. Parallelization changes timing, task order, and retry shape.

Require equivalence in:
- final outputs
- final statuses
- acceptance decisions
- failure classifications
- retry-policy meaning
- canonical state consistency

## Define invariants

Define what must never happen.

Examples:
- the same task is leased to two workers at once
- a result is promoted without required evidence
- canonical state points to two accepted outputs for one logical item
- a blocked case is silently reported as resolved

Also define liveness expectations.

Examples:
- every lease is eventually completed, released, or reclaimed
- every submission reaches terminal reconciliation
- every worker handoff becomes canonical state or a requeued task

## Compare against the serial reference

Treat the original single-process workflow as the reference model.

Use differential tests:
- run the serial and parallel versions on the same inputs
- normalize harmless ordering differences
- compare final semantic outcomes

Good comparison surfaces:
- accepted artifacts
- per-item final status
- per-family or per-stage final status
- blocker classification
- retry outcomes

## Use scenario suites

Build cases for:
- clean success
- no-op exhaustion
- environment blocker
- worker failure and retry
- stale lease reclamation
- conflicting candidate outputs
- shared-remediation acceptance or rejection

Do not trust only the happy path.

## Use replay and shadow mode

Replay historical runs when possible.

Use shadow mode before cutover:
- keep the serial workflow authoritative
- run the parallel workflow on the same inputs
- compare outcomes without auto-promoting the parallel result

## Check metamorphic properties

Verify that harmless scheduling changes do not change semantics.

Examples:
- changing worker count from 1 to 2 does not change final accepted outputs
- pausing and resuming does not change terminal classification
- re-running monitor reconciliation does not duplicate promotion
- reordering independent task completion does not change canonical truth

## Check monitor-specific robustness

Verify that the monitor design is resilient even when progress signaling is incomplete.

Check:
- missing one worker progress event does not strand the workflow
- re-running a tick does not duplicate acceptance or submission
- a silent worker failure is detected by interval review and lease expiry
- resource repair state is recovered from canonical files, not agent memory
- the monitor can resume from disk after interruption without inventing new workflow semantics
