# Persistent Agent Instructions

## Contents

- Create a workflow package
- Write monitor instructions
- Write single-process agent instructions
- Generate enforcement scripts
- Persist contracts
- Keep imports explicit
- Make resume possible

## Create a workflow package

When transforming a single-process skill or workflow into a parallel workflow, write durable artifacts instead of relying on conversation context.

Use this package shape unless the target repo already has a clearer convention:

```text
parallel_workflow/
  instructions/
    monitor_prompt.md
    single_process_agent_prompt.md
    task_contract.md
    resource_leases.md
    state_schema.md
    resume_protocol.md
    verification_plan.md
  state/
    tasks.jsonl
    leases.json
    canonical_state.json
  handoffs/
  logs/
  scripts/
    state_machine.py
    monitor.py
    worker_launcher.py
  tests/
    test_state_machine.py
```

Include `scripts/` and `tests/` when the user wants a runnable workflow. Omit `worker_launcher.py` only when worker startup is owned by an existing runner or the user asks for manual worker launch.

Name the directory for the workflow when multiple parallel workflows may coexist.

## Write monitor instructions

`monitor_prompt.md` must be sufficient for a fresh monitor agent to resume from disk.

Include:
- the original workflow or skill used as the semantic reference
- the monitor's exclusive ownership of scheduling, canonical state, leases, retries, acceptance, and final reporting
- the canonical files the monitor must read before each action
- the legal task states and state transitions
- the worker spawning or assignment policy
- the scarce-resource lease rules
- the backpressure and retry policy
- the acceptance gates and evidence requirements
- the resume procedure after interruption
- the stop conditions and escalation conditions

State explicitly that the monitor must not rely on conversation memory as workflow state.

## Write single-process agent instructions

`single_process_agent_prompt.md` must be sufficient for a fresh worker or single-process agent to execute one assigned task.

Include:
- the task-local portion of the original workflow to run
- the allowed input fields and output paths
- the old scripts, functions, or skill procedures that may be reused
- the resources that require an explicit lease before use
- the evidence and metadata the worker must emit
- the heartbeat or progress format
- the blocker and failure-reporting format
- the rule that workers must not mutate canonical truth directly
- the rule that workers execute one leased task at a time unless the workflow explicitly defines finer-grained pipelining

Keep workers isolated. They may propose outputs and attach evidence; the monitor promotes or rejects them.

## Generate enforcement scripts

Markdown instruction files are not enough for a long-running runnable workflow. Implement the state machine in scripts so the monitor can reject illegal worker actions deterministically.

Read [state-machine-scripts.md](state-machine-scripts.md) before writing scripts.

Generate:
- `scripts/state_machine.py` for legal states, transitions, actor permissions, and evidence requirements
- `scripts/monitor.py` for reconciliation, transition validation, lease handling, atomic canonical writes, and durable logs
- `scripts/worker_launcher.py` only if the workflow needs a local worker starter
- `tests/test_state_machine.py` for legal and illegal transitions

Keep the implementation boring. The script should enforce the contract, not reinterpret it.

## Persist contracts

Write the contracts as Markdown files even when also implementing scripts.

`task_contract.md` should define:
- task identity
- task payload
- task-local inputs
- task-local outputs
- legal task statuses
- required evidence
- terminal statuses

`resource_leases.md` should define:
- scarce resources
- lease owners
- lease acquisition and release rules
- timeouts
- heartbeat or freshness checks
- reclaim rules

`state_schema.md` should define:
- canonical state files
- durable handoff files
- atomic write expectations
- duplicate-action suppression keys
- which actor may write each file

`resume_protocol.md` should define:
- how the monitor reconstructs active work
- how stale leases are found and reclaimed
- how incomplete handoffs are handled
- how workers restart or receive reassigned tasks
- how rerunning a monitor tick stays idempotent

`verification_plan.md` should define:
- serial-reference comparison
- invariants
- scenario tests
- replay or shadow mode when useful
- metamorphic checks for worker count, ordering, pause, and resume

## Keep imports explicit

Do not describe the old single-process skill as something workers import wholesale.

Classify reuse boundaries:
- reference only: read the old skill to preserve semantics
- worker operation: call an old script or function on one isolated task
- forbidden import: avoid old procedures that mutate global state, own acceptance, write shared outputs, or assume singleton resources

If the old workflow has no safe worker-level boundary, keep that part serial or make it a leased resource lane.

## Make resume possible

A long-running workflow is valid only if a fresh monitor can reconstruct the next legal action from durable state and instruction files.

Before finishing, check:
- monitor instructions name every canonical state file
- worker instructions do not require hidden conversation context
- every task handoff has a durable file or state transition
- every scarce resource has a lease rule
- every final acceptance decision is made by the monitor
