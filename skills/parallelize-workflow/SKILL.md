---
name: parallelize-workflow
description: Transform a serial skill or operational workflow into a new bounded parallel workflow while preserving semantics. Use when Codex needs to analyze a single-process skill, generate a monitor-worker or monitor-single-process-agent workflow, persist monitor and worker instruction Markdown, implement executable state-machine enforcement scripts, define task/resource/state contracts, or verify that a parallel redesign has not drifted from the original workflow.
---

# Parallelize Workflow

## Overview

Transform a serial or batch-heavy workflow into a new bounded parallel workflow without changing its semantic contract. Optimize for throughput, isolation, and recovery rather than maximizing agent count. When the user gives a single-process skill or workflow and asks to accelerate or parallelize it, build the parallel workflow package unless the user asks only for analysis.

## Run The Workflow

1. Model the current workflow.
   Capture task units, state transitions, inputs, outputs, shared resources, acceptance gates, and failure classes. Identify the true bottleneck and the canonical source of truth.

2. Decide whether parallelism is appropriate.
   Read [references/suitability.md](references/suitability.md) when decomposition, bottlenecks, or merge cost are unclear. Do not parallelize workflows that are mostly serial, heavily shared-state, or dominated by an uncontrolled singleton resource.

3. Design the target execution model.
   Define:
   - the monitor responsibilities
   - the single-process agent or worker responsibilities
   - the task granularity
   - the scarce-resource lease model
   - the canonical state files or commit points
   - the backpressure and retry rules
   Read [references/transformation.md](references/transformation.md) for the transformation pattern.
   Read [references/monitor-design.md](references/monitor-design.md) when the monitor must handle long-running progress, resource repair, and worker reassignment without becoming fragile.

4. Generate the new parallel workflow package.
   Create or update a durable workflow package that can be resumed without relying on conversation memory. At minimum, include persistent Markdown instructions for:
   - the monitor agent
   - the single-process agent or worker agent
   - the task, resource, state, and resume contracts
   Also include executable scripts that enforce the state machine when the user wants a runnable workflow.
   Read [references/agent-instructions.md](references/agent-instructions.md) before writing these files.
   Read [references/state-machine-scripts.md](references/state-machine-scripts.md) before implementing monitor enforcement scripts.

5. Implement the new boundaries.
   Change the workflow so workers execute isolated tasks and the monitor owns scheduling, canonical truth, and acceptance. Keep shared-resource access bounded and explicit. Reuse the old skill, scripts, or functions only at safe task-local boundaries.

6. Verify semantic equivalence.
   Read [references/verification.md](references/verification.md). Compare invariants and final outcomes against the serial reference. Prefer differential, replay, and scenario-based checks over line-by-line execution matching.

## Produce These Outputs

Produce:
- a suitability judgment
- a generated or updated parallel workflow package
- a proposed parallel architecture
- the task, resource, state, and resume contract
- persistent monitor instruction Markdown
- persistent single-process agent or worker instruction Markdown
- executable state-machine enforcement scripts for runnable workflows
- tests proving legal transitions pass and illegal transitions fail
- a migration or implementation plan
- a drift-verification plan

If the user asks for code or skill updates, implement the redesign directly rather than stopping at theory.

## Keep These Rules

- Prefer dynamic task allocation over coarse static partitioning when task duration varies.
- Prefer one task lease per worker at a time unless the workflow already has stable finer-grained pipelining.
- Treat scarce resources as leased lanes, not free-for-all shared access.
- Prefer an interval-triggered monitor backbone with idempotent ticks over a progress-trigger-only monitor.
- Keep canonical acceptance centralized.
- Bound concurrency at the real bottleneck.
- Reduce concurrency when disk, memory, review capacity, or external lanes saturate.
- Make task handoffs, promotions, retries, and failures durable and replay-safe.
- Do not rely on conversation memory for long-running monitor or worker behavior.
- Keep the original single-process workflow as the semantic reference, not as an opaque unit to run in every worker.
- Treat Markdown as the contract explanation and scripts as the contract enforcement.
