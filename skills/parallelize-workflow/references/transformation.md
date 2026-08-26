# Transformation Pattern

## Contents

- Define the serial semantics
- Split the work
- Separate control from execution
- Generate persistent agent instructions
- Implement state-machine enforcement
- Design the monitor loop
- Lease scarce resources
- Centralize acceptance
- Add recovery rules

## Define the serial semantics

Write down the original workflow contract before parallelizing it.

Capture:
- inputs and outputs
- legal state transitions
- acceptance gates
- terminal statuses
- retry and escalation rules
- canonical source of truth

Do not optimize a workflow that has no explicit semantic contract.

## Split the work

Choose task units that are:
- small enough to rebalance
- large enough that scheduling overhead does not dominate
- owned by exactly one worker at a time

Prefer one task lease per worker when evidence review is important or task duration is uneven.

## Separate control from execution

Make the monitor own:
- scheduling
- task and resource allocation
- canonical state
- acceptance and promotion
- retry and backpressure policy
- failure recovery

Make workers own:
- isolated execution
- local artifacts
- evidence production
- lease heartbeats

Do not let workers mutate canonical truth directly.

Classify every original workflow step as one of:
- monitor-owned
- worker-owned
- leased-resource-owned
- still serial

Do not split by line number or narrative order. Split by state ownership, resource ownership, and acceptance authority.

## Generate persistent agent instructions

Write durable monitor and worker instruction files for any workflow expected to run longer than one interactive turn or to survive interruption.

At minimum, produce:
- `monitor_prompt.md`
- `single_process_agent_prompt.md`
- `task_contract.md`
- `resource_leases.md`
- `state_schema.md`
- `resume_protocol.md`
- `verification_plan.md`

Read [agent-instructions.md](agent-instructions.md) for the required contents.

The monitor and worker prompts must be usable by fresh agents that did not see the original conversation.

## Implement state-machine enforcement

For runnable workflows, implement the contract in scripts. Do not leave the monitor to enforce critical transitions from prose alone.

Read [state-machine-scripts.md](state-machine-scripts.md).

Use the KISS rule:
- Markdown explains the contract.
- Scripts enforce the contract.
- Tests prove the script rejects bad transitions.

## Design the monitor loop

Use a simple, durable monitor control loop.

Prefer:
- a fixed review interval
- one idempotent reconciliation tick
- canonical state files as the source of truth
- optional progress events as hints, not required control flow

The monitor should usually have three layers:
- timer layer: wake up every N seconds or minutes
- deterministic reconciliation layer: inspect canonical state, health, leases, and pending handoffs
- agent escalation layer: handle ambiguous recovery or complex re-planning only when deterministic rules are insufficient

Do not make the workflow depend on perfect progress-event signaling. If a worker dies silently or a progress event is missed, the next tick must still recover the workflow.

## Lease scarce resources

Model scarce resources as leases, not informal ownership.

Examples:
- browser or CDP lanes
- API submission slots
- review capacity
- ports, profiles, temp storage, or GPU lanes

Each lease should have:
- an owner
- a timeout
- a heartbeat or freshness signal
- reclaim rules

## Centralize acceptance

Keep one canonical acceptance authority, usually the monitor.

Workers may:
- propose outputs
- attach validation evidence
- request scarce-resource use

The monitor should:
- approve promotion
- update canonical state
- merge shared remediation changes
- requeue or block work

## Add recovery rules

Make the redesign replay-safe.

Require:
- durable task handoffs
- idempotent monitor reconciliation
- bounded retries
- explicit failure classes
- backpressure when resources saturate

Use the same semantic acceptance bar as the serial workflow unless the user explicitly asks to change it.
