# Orchestration Protocol

**Intent**: Preserve decision, dependency, ownership, test, and Git evidence while a broad initiative moves through parallel Spec Kit worktrees and serial integration promotion.

## Control Artifacts

Create these main-agent-owned files on the integration branch:

- `specs/orchestration/<initiative>/dependency-graph.md`
- `specs/orchestration/<initiative>/integration-review.md`

Begin each document with a one-line intent. Keep their responsibilities separate:

`dependency-graph.md` is the implementation control plane. Record:

- baseline branch and commit;
- every component's unique prefix, branch, worktree, owner, responsibility, and artifact paths;
- public contracts and shared-file ownership;
- the cross-component reconciliation result and unresolved material decisions;
- dependency edges in `prerequisite -> consumer` form with a reason for every edge;
- one integration-owned work packet for every dependency edge;
- topological waves and the conditions that unblock each component;
- cycles or boundary changes made before implementation.

`integration-review.md` is the chronological audit. Record:

- human clarification questions, answers, affected components, and updated artifacts;
- Spec Kit artifact and analysis status per component;
- local commit SHAs and exact local verification commands;
- integration merge, fix, tested, audit, and promotion SHAs;
- exact integration, end-to-end, smoke, and final commands with exit status and log or artifact paths;
- failures, ownership decisions, corrective commits, and retest results;
- downstream branches and the promotion SHA each received;
- final state and residual risks without requiring a human approval gate.

Update the review record after every material transition, not only at the end. Commit audit updates on the integration branch. Component agents must report status through messages and must not edit either control artifact.

## Human Allocation Review

Complete this interaction after decomposition and before creating the integration branch, component branches, or any worktrees. The purpose is to let the human correct component boundaries and dependency assumptions while the topology is still cheap to change.

Present one deduplicated review packet containing:

- the provisional dependency graph, with each proposed `prerequisite -> consumer` edge and its reason;
- every component's responsibility, public contracts, expected tests, shared-file ownership, and explicit exclusions;
- the proposed Spec Kit prefix, branch name, worktree path, stable owner identity, and capacity wave for every component;
- the proposed integration branch and worktree, baseline branch and commit, and any known allocation collisions or unresolved decisions.

Ask the human to approve the packet, block it with corrections, or answer the listed material questions. Approval must be explicit. A vague acknowledgement, silence, or approval of only one component does not authorize allocation. While the packet is blocked, revise the decomposition and present the complete changed packet again; do not create a subset of the proposed worktrees.

Record the packet version, human decision, answers, affected components, and resulting changes in `integration-review.md` immediately after the integration worktree exists. The first `dependency-graph.md` must identify the graph as provisional until the post-planning DAG gate replaces or confirms it. If completed plans change a scope, public contract, shared-file owner, dependency edge, or implementation wave from the approved packet, stop before implementation, obtain a new human decision, and update the affected planning artifacts.

## Branch and Worktree Allocation

### Baseline

Resolve the repository root and record:

- target branch chosen by the user;
- baseline commit SHA;
- current worktree status;
- existing `git worktree list --porcelain` output;
- branch-numbering mode from `.specify/init-options.json`.

The baseline must be committed and reproducible. Existing user changes, branches, and worktrees are preserved.

### Unique Spec Kit prefixes

Allocate all component names centrally before any planning agent writes artifacts. Scan both `specs/` directories and local or remote feature branches.

- For sequential numbering, reserve consecutive unused numeric prefixes at least three digits wide.
- For timestamp numbering, reserve a different full timestamp prefix for every component; never reuse one timestamp with multiple slugs.
- Name each component branch exactly `<unique-prefix>-<component-slug>`.

Never let concurrent component agents invoke automatic numbering. Spec Kit resolves a feature directory by numeric or timestamp prefix; duplicate prefixes make the merged integration branch ambiguous even when slugs differ.

### Topology

Use these defaults unless repository instructions require another location:

- integration branch: `integration/<initiative-slug>`;
- worktree root: a sibling directory named `<repo>-worktrees/<initiative-slug>/`;
- integration worktree: `<worktree-root>/integration`;
- component worktree: `<worktree-root>/<component-slug>`.

Create the integration branch and every component branch from the recorded baseline commit. The main agent owns the integration worktree. Each component worktree has exactly one distinct, stable subagent identity. Create and activate component worktrees in waves bounded by available active-agent capacity. An idle owner may be reactivated later, but an owner must not be reused for another worktree and a second agent must not enter the same worktree concurrently. If the collaboration platform cannot retain one distinct identity per component across waves, stop before allocation instead of weakening ownership.

If a requested branch or path already exists with different provenance, stop that allocation and resolve the collision. Do not overwrite it.

## Component Planning

### Agent assignment

Every component-agent task must include:

- its exact worktree path and branch;
- its component responsibility and exclusions;
- declared upstream and downstream contracts known so far;
- files or interfaces likely to be shared;
- the required Spec Kit sequence and report format;
- an explicit prohibition on editing the integration worktree or orchestration control artifacts.

The component owner reads the instructions applicable inside its worktree before writing anything.

### Spec Kit branch adaptation

The orchestrator creates branches and worktrees before component planning. Therefore the component agent must not run the branch-creation portion of `speckit-specify`.

Inside the already checked-out component branch, the owner:

1. creates `specs/<component-branch>/spec.md` from `.specify/templates/spec-template.md`;
2. follows the local `speckit-specify` instructions beginning with specification generation and quality validation;
3. runs the local `speckit-clarify`, `speckit-plan`, `speckit-tasks`, and `speckit-analyze` workflows normally against the current unique-prefix branch;
4. commits the complete planning package after its gates pass.

Do not call `create-new-feature.sh` from the component worktree. It would attempt to create or switch branches that are already bound to worktrees.

### Human-question protocol

Component agents never ask the user directly. They send the main agent one structured report per unresolved material decision:

```text
Component: <name>
Phase: specification | planning
Artifact: <path and section>
Decision: <one precise question>
Why blocking: <scope, contract, architecture, test, security, or compliance impact>
Options: <2-4 mutually exclusive choices with implications>
Recommended default: <choice and rationale, or none>
Affected components: <names>
```

The main agent deduplicates questions that express the same domain decision and asks the user in two possible batches:

1. after component specification and clarification scans;
2. after planning exposes architectural or contract decisions, before task generation is finalized.

After an answer, the main agent sends the canonical decision to every affected owner. Each owner updates its artifacts and reports the resulting commit. Persist the decision and affected artifact paths in `integration-review.md`.

Do not ask for implementation preferences that repository context, the constitution, or a safe documented default already resolves.

### Global artifact gate

Implementation remains closed until every component has:

- a complete `spec.md`, `plan.md`, and `tasks.md`;
- completed requirement checklists;
- no `NEEDS CLARIFICATION`, unresolved placeholder, or unjustified constitution violation;
- traceable requirements and acceptance scenarios in tasks;
- a `speckit-analyze` pass whose CRITICAL and HIGH findings were remediated and rechecked;
- a committed planning package and clean worktree.

`speckit-analyze` is read-only. The component owner applies justified remediation through the appropriate Spec Kit artifact, then reruns the analysis. Escalate only findings that require a product decision.

## Cross-Component Reconciliation

The main integration agent performs this gate after every component passes the global artifact gate. No separate producer or consumer agent is created. Compare each component's `spec.md`, `plan.md`, `tasks.md`, data model, contracts, and quickstart against every component it exchanges data, control, configuration, or state with.

Inspect these conflict classes:

- naming and identity: one name for different concepts, multiple names for one concept, unstable IDs, namespaces, or ownership;
- data contract: schema, type, units, path, encoding, cardinality, ordering, nullability, version, provenance, or lifecycle mismatch;
- behavior: logic, preconditions, postconditions, state transitions, idempotency, retries, timeout, or failure-semantics mismatch;
- assumptions: configuration source, runtime, scale, resource availability, security boundary, or deployment topology mismatch;
- scientific meaning: cohort, filtering, leakage, randomization, metric, statistical unit, baseline, or interpretation mismatch.

Write a reconciliation entry for each conflict with its affected components, evidence locations, canonical interpretation, owner, required artifact updates, and disposition. Use these resolution rules:

1. Resolve an unambiguous issue from approved requirements, the constitution, repository instructions, or an already canonical contract.
2. The integration agent fixes integration-owned contracts, adapters, naming maps, orchestration artifacts, and integration tests.
3. Route component-local specification, implementation, or test defects to that component's existing owner. The integration agent defines the expected boundary result and verifies the correction.
4. Update and reanalyze every affected planning package before declaring reconciliation passed.
5. Ask the human only when alternatives change product or scientific meaning, scope, architecture, ownership, security posture, or another material semantic choice. Batch equivalent questions and record the canonical answer.

The gate passes only when every identified conflict is resolved or has a recorded human decision reflected in all affected artifacts. A component-local correction returns to `planning`; a material question enters `clarification_wait`; a clean reconciliation proceeds to DAG construction.

## Dependency DAG

Build the cross-component DAG from the completed specs, contracts, plans, and task lists. Add an edge `A -> B` when B cannot implement or verify its contract without an integrated A. Typical evidence includes a public interface, schema, migration, data producer, shared foundation, or test fixture supplied by A.

Also serialize components that claim incompatible ownership of the same files or public contract. File overlap alone is not automatically a dependency when clean independent ownership is possible; revise boundaries first.

For every edge, record:

- the supplying contract or artifact;
- the consuming requirement or task;
- the invariant that must hold across the boundary;
- the promotion condition.

The graph must be acyclic before implementation. Resolve a cycle by changing component boundaries, combining inseparable components, or extracting a stable interface component. Ask the user only when the resolution changes product scope or a material architectural choice. Any boundary or contract change reopens the global artifact gate: update and reanalyze every affected `spec.md`, `plan.md`, and `tasks.md` before implementation can begin.

## Integration Design

Component `tasks.md` files design component-local implementation and tests. After those files exist and the DAG passes, the integration agent adds integration-owned edge work packets to `dependency-graph.md`; do not create another Spec Kit component or new producer and consumer agents.

Each edge work packet contains:

- stable `edge_id`, producer, consumer, and dependency reason;
- producer output and consumer input, with schemas, locations, identity rules, and lifecycle;
- boundary invariants and a compatibility verdict;
- minimal integration glue or adapter, its owner, and implementation timing;
- a handoff test that creates the upstream output and passes that same artifact to the consumer;
- affected end-to-end and smoke tests;
- exact promotion condition and evidence locations.

If design exposes a graph-only issue, return to DAG construction. If it changes a component contract or assumption, return to planning and rerun reconciliation. Otherwise, record `edge_work_packets` and `integration_test_plan` evidence before opening implementation.

The integration agent implements integration-only glue in the integration worktree when the supplying interface is available. Component-local changes remain with the existing component owner. A handoff test must consume the artifact produced earlier in the same test or run; manually constructing a replacement consumer fixture does not test the edge.

## Implementation Waves

Activate all and only components whose incoming edges are satisfied by recorded green promotion SHAs, subject to agent capacity. An implementation owner:

1. if it has prerequisites, merges the exact prerequisite promotion SHA from integration into its branch before coding;
2. follows local `speckit-implement` and all repository-mandated development workflows;
3. implements only its declared component and approved shared-contract changes;
4. runs the tests and static checks required by its tasks, plan, and repository instructions;
5. records commands and artifact or log paths, updates completed task markers, and commits the result;
6. reports its local commit, clean status, verification evidence, changed public contracts, and known integration risks;
7. remains assigned and available until the integration promotion gate succeeds.

Do not treat a local pass as component completion. Completion means the component is green and audited in integration.

## Integration and Promotion

### Serial merge gate

Before merging a component, require a clean integration worktree and a green prior integration state. Merge one component at a time with an explicit merge commit so component provenance remains visible.

After the merge, run:

- the component's local verification commands again in integration;
- tests for every affected shared contract and prerequisite handoff;
- the initiative's current integration and end-to-end scenarios;
- a smoke command that exercises the newly available runnable path;
- repository-required type, lint, documentation, or scientific-validity checks.

The integration design gate must add missing handoff, integration, end-to-end, or smoke coverage needed for component acceptance scenarios. Do not silently mark a required gate inapplicable.

### Machine-validated integration coverage gate

Before `integration_passed`, the main agent must submit the `integration_coverage_passed` transition with a `coverage_manifest` and the `tested_integration_sha`. The validator accepts only a JSON manifest with this shape:

```json
{
  "schema_version": 2,
  "status": "passed",
  "tested_integration_sha": "<same SHA as transition evidence>",
  "edge_handoffs": [
    {
      "edge_id": "<producer>-><consumer>",
      "producer": "<component-id>",
      "consumer": "<component-id>",
      "test_path": "tests/integration/<handoff-test>",
      "passed": true,
      "upstream_output_consumed": true,
      "synthetic_boundary_replacement": false
    }
  ],
  "integration": {
    "tests": [{"path": "tests/integration/<test>", "added": true, "passed": true}],
    "command": "<exact integration test command>",
    "exit_code": 0
  },
  "e2e": {
    "tests": [{"path": "tests/e2e/<test>", "added": true, "passed": true}],
    "command": "<exact end-to-end test command>",
    "exit_code": 0
  }
}
```

The validator requires a non-empty `edge_handoffs` list. Every entry must identify both components, point to a declared new passed integration test, declare that the test consumed the upstream output, and reject synthetic boundary replacement. It also checks test-path categories, declared `added` and `passed` values, commands, exit codes, and SHA match. The main agent must execute the commands and preserve logs or result artifacts in `integration-review.md`; the validator does not execute commands, inspect test code, or independently compare paths with Git history.

### Failure routing

While integration is red:

- do not merge another component;
- do not send the current integration `HEAD` downstream;
- record the failing command, exit status, relevant output or log, suspected ownership, and affected components;
- return component-local behavior to the component owner for a fix commit, repeated local verification, and an updated evidence report;
- handle merge resolutions, shared contracts, and cross-component glue in the integration worktree under main-agent ownership;
- merge corrective commits and rerun the failed gate plus affected regression gates.

If a merge cannot be completed coherently, abort only that in-progress merge, preserve the component branch, and record the conflict. Never reset away committed user or integration work.

### Green promotion

When all gates pass:

1. record the tested integration SHA and evidence in `integration-review.md`;
2. commit the audit update and capture that audit commit as the candidate promotion SHA;
3. rerun the smoke command against the candidate SHA;
4. when smoke passes, use that unchanged candidate as the immutable promotion SHA;
5. immediately merge that exact SHA into every downstream branch for which all prerequisites are now promoted;
6. append the promotion SHA and downstream receipts to the review record in a later audit commit, avoiding an impossible commit that claims its own SHA;
7. smoke-test that receipt-audit commit before another component merge; carry its SHA and result into the next audit entry or, for the last component, the final report;
8. resume downstream owners and release the promoted component owner after propagation completes.

Never merge a component branch directly into a sibling. Never substitute a newer, unverified integration `HEAD` for the recorded promotion SHA.

## Final Gate

After every component is promoted, run the complete repository-required test suite plus the initiative's full integration, end-to-end, and smoke commands from the integration worktree. Record that fully tested code SHA, final commands, results, promotion history, and remaining risks in `integration-review.md`, then commit the final audit update and smoke-test that audit commit. Report both the fully tested code SHA and the smoke-verified final audit SHA; do not make the audit commit claim its own hash.

Completion leaves all branches and worktrees in place. Report the integration branch and audit paths, but do not merge integration into the baseline target and do not pause for human review approval.
