# Monitor Design

## Contents

- Choose the primary trigger
- Use a three-layer monitor
- Keep the tick idempotent
- Use progress as a hint
- Keep the monitor state-driven

## Choose the primary trigger

Use time-interval triggering as the primary monitor mechanism.

Reasons:
- it is easier to implement correctly
- it is easier to reason about than a large event graph
- it does not depend on every worker emitting every progress signal
- it naturally supports recovery through repeated reconciliation

Treat progress-triggered wakeups as an optimization, not as the only control path.

## Use a three-layer monitor

Design the monitor in three layers:

1. Timer layer
   Wake on a fixed interval. Keep this layer simple.

2. Deterministic reconciliation layer
   Read canonical state, resource health, pending handoffs, pending submissions, lease freshness, and retry state. Decide the next action from durable facts, not assumptions.

3. Agent escalation layer
   Escalate only when the deterministic layer cannot classify or repair the situation cleanly. Use this for ambiguous recovery, complex reprioritization, or shared-remediation decisions.

## Keep the tick idempotent

One tick should be safe to replay.

Require:
- atomic canonical writes
- durable logs or ledgers
- duplicate-action suppression where needed
- no reliance on in-memory monitor history alone

The monitor should be able to say: run another tick and reconcile again.

## Use progress as a hint

Workers may still emit:
- task completed
- blocker reported
- lease released
- resource requested
- validation finished

Use those signals to wake the monitor early when helpful, but never require them for correctness.

## Keep the monitor state-driven

Base monitor decisions on files or other durable canonical state, not on conversation memory or fragile callbacks.

At minimum, the monitor should be able to reconstruct:
- what work is active
- what work is pending review
- which resources are leased
- which submissions are in flight
- what the next legal resume action is

If that cannot be reconstructed from canonical state, the monitor design is too fragile.
