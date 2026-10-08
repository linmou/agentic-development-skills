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
- topological waves, runnable promotion checks, and the conditions that unblock each component;
- cycles or boundary changes, including those discovered during implementation.

`integration-review.md` is the chronological audit. Record:

- human clarification questions, answers, affected components, and updated artifacts;
- Spec Kit artifact and analysis status per component;
- local commit SHAs and exact local verification commands;
- integration merge, fix, tested, audit, and promotion SHAs;
- exact integration, end-to-end, smoke, and final commands with exit status and log or artifact paths;
- failures, ownership decisions, corrective commits, and retest results;
- open runtime dependency incidents with their blocked gate, owner, and next action, followed by resolution evidence;
- downstream branches and the promotion SHA each received;
- final state and residual risks without requiring a human approval gate.

Update the review record after every material transition, not only at the end. Commit audit updates on the integration branch. Component agents must report status through messages and must not edit either control artifact.

## Resume Audit

For an existing initiative, first reconstruct its state without editing files, merging, dispatching implementation, or recommending a repository artifact for use elsewhere. Work from the initiative's control artifacts and all recorded worktrees, regardless of the current directory. A previous `completed` label describes its recorded point in time, not the current branch heads.

1. **Inventory provenance.** Read applicable repository instructions, the dependency graph, integration review, component plans and tasks, coverage manifests, and relevant test definitions. Run `git worktree list --porcelain`; for every recorded worktree, capture its path, branch, `HEAD`, status, and any uncommitted changes. Compare each component head with integration using ancestry and commits present on only one side. Match merge, tested, audit, and promotion SHAs in the review to actual commits. Treat unmerged component commits and dirty worktrees as pending work, not as evidence already integrated. Before recommending a file, resolve its branch and commit and check for a newer authoritative version on its owning branch.
2. **Audit gates against current code.** Rebuild the edge list and topological order from the graph; compare every edge with the latest manifest's completed and deferred lists. For each claimed green gate, verify that its commands, logs, and tested SHA refer to the integrated code at that point. Inspect the relevant tests and contract behavior where an assertion depends on semantics or real producer-to-consumer data flow. A validator pass, checkbox, or recorded exit code alone does not establish graph completeness or correctness. Check whether later commits invalidate earlier evidence.
3. **Find the resume point.** Identify the last integration SHA whose required gates are supported by evidence and the first missing, stale, or failed gate. Read open runtime dependency incidents before using unchecked tasks as a work queue. Record branch heads, unmerged commits, discrepancies, affected edges, ownership, and the next allowed actions in a resume audit entry in `integration-review.md` after the read-only inspection. Preserve earlier audit entries, including a historical final result. If no green point can be justified, establish a new baseline by running the required gates on a known commit before promotion.
4. **Resume by ownership.** Reconcile the pending work with the graph and component scopes. Send component-local defects to their recorded owners; queue locally verified unmerged commits for serial integration. The integration owner handles contracts, glue, coverage accounting, and merges. If an earlier owner is unavailable, establish a new sole owner for that same worktree and record the handoff before dispatch. Reopen the earliest affected gate, rerun its downstream checks, and promote only a newly verified integration SHA. A historical `completed` state starts a documented correction cycle; it is not a validator transition out of that terminal state.

The audit is complete only when every component head and graph edge is accounted for, the last green SHA is justified or declared unknown, and each pending action has an owner and prerequisite gate. Preserve existing worktree changes throughout inspection.

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

Create the integration branch and every component branch from the recorded baseline commit. The main agent owns the integration worktree. Each component worktree has exactly one distinct, stable subagent identity. Create and activate component worktrees in waves bounded by available active-agent capacity. An idle owner may be reactivated later, but an owner must not be reused for another worktree and a second agent must not enter the same worktree concurrently. If the collaboration platform cannot retain one distinct identity per component across waves, stop before allocation instead of weakening ownership. A later session may reassign an unavailable owner only through the recorded resume handoff above.

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

Before implementation, simulate each wave in topological order. For every prerequisite promotion, list the code, fixtures, glue, and tests its gate needs and confirm each exists by that wave. A producer's promotion can verify its output contract and runnable flow; a handoff requiring the consumer belongs to the consumer's later integration gate. Record both gates on the edge. A condition needing code from a still-blocked component is a dependency error even when the component graph is acyclic. Resolve it by moving the test to the first runnable gate or revising component boundaries and edges. The gate passes only when every promotion condition is runnable before it unblocks its consumers.

Classify externally hosted or otherwise unavailable checks before the wave starts. A required check holds promotion while pending. A separately approved contract-ready milestone may unblock only the downstream work explicitly assigned to that milestone in the graph; record its runnable checks, pending hosted acceptance, and distinct promotion condition. The machine coverage gate still needs its required runnable integration and end-to-end tests to pass. A blocked check cannot become optional during recovery.

Resolve component cycles by changing boundaries, combining inseparable components, or extracting a stable interface component. Ask the user only when the resolution changes product scope or a material architectural choice. Any boundary or contract change reopens the global artifact gate: update and reanalyze every affected `spec.md`, `plan.md`, and `tasks.md` before implementation can begin.

## Integration Design

Component `tasks.md` files design component-local implementation and tests. After those files exist and the DAG passes, the integration agent adds integration-owned edge work packets to `dependency-graph.md`; do not create another Spec Kit component or new producer and consumer agents.

Each edge work packet contains:

- stable `edge_id`, producer, consumer, and dependency reason;
- producer output and consumer input, with schemas, locations, identity rules, and lifecycle;
- boundary invariants and a compatibility verdict;
- minimal integration glue or adapter, its owner, and implementation timing;
- a handoff test that creates the upstream output and passes that same artifact to the consumer;
- affected end-to-end and smoke tests;
- the producer's runnable promotion condition, the later consumer handoff gate, and evidence locations.

Check every planned test's earliest runnable wave against the graph. If design exposes a graph-only issue, return to DAG construction. If it changes a component contract or assumption, return to planning and rerun reconciliation. Otherwise, record `edge_work_packets` and `integration_test_plan` evidence before opening implementation.

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

Before merging a component, confirm its tasks are complete, its recorded local checks passed on its current commit, and its source worktree and integration worktree are clean. Require a green prior integration state. Review the source commits since the last integration point against the approved component scope. Merge one component at a time with an explicit merge commit so component provenance remains visible.

After the merge, run:

- the component's local verification commands again in integration;
- tests for every affected shared contract and handoff whose producer and consumer are integrated;
- the initiative's currently runnable integration and end-to-end scenarios;
- a smoke command that exercises the newly available runnable path;
- repository-required type, lint, documentation, or scientific-validity checks.

The integration design gate must add missing handoff, integration, end-to-end, or smoke coverage needed for component acceptance scenarios. Do not silently mark a required gate inapplicable.

### Machine-validated integration coverage gate

Before `integration_passed`, the main agent must submit the `integration_coverage_passed` transition with a `coverage_manifest` and the `tested_integration_sha`. Use schema version 3 for staged promotion. For example, a producer promotion before its consumer exists has this shape:

```json
{
  "schema_version": 3,
  "status": "passed",
  "tested_integration_sha": "<same SHA as transition evidence>",
  "integrated_components": ["<producer-id>"],
  "edge_handoffs": [],
  "deferred_edges": [{"edge_id": "<edge-id>", "producer": "<producer-id>", "consumer": "<pending-consumer-id>"}],
  "integration": {
    "tests": [{"path": "tests/integration/<producer-contract-test>", "added": true, "passed": true}],
    "command": "<exact integration test command>",
    "exit_code": 0
  },
  "e2e": {
    "tests": [{"path": "tests/e2e/<runnable-producer-flow>", "added": true, "passed": true}],
    "command": "<exact end-to-end test command>",
    "exit_code": 0
  }
}
```

In version 3, `integrated_components` includes the component being promoted. Each `deferred_edges` producer must be integrated and its consumer still pending; each `edge_handoffs` endpoint must be integrated. Move an edge from `deferred_edges` to `edge_handoffs` at the consumer's integration gate. A handoff entry must identify both components, point to a declared new passed integration test, set `passed` and `upstream_output_consumed` to true, and set `synthetic_boundary_replacement` to false. The validator checks these declarations, unique edge IDs, test categories, commands, exit codes, and SHA match. Version 2 remains valid for a fully runnable handoff and requires a non-empty `edge_handoffs` list.

At every promotion, compare both edge lists with the authoritative dependency graph: every declared edge whose producer is integrated is either tested or deferred, and no edge with an integrated consumer remains deferred. The validator cannot read the graph or prove list completeness. Execute the commands and preserve logs or result artifacts in `integration-review.md`; the validator does not execute commands, inspect test code, or independently compare paths with Git history.

### Failure routing

While integration is red:

- do not merge another component;
- do not send the current integration `HEAD` downstream;
- record the failing command, exit status, relevant output or log, suspected ownership, and affected components;
- return component-local behavior to the component owner for a fix commit, repeated local verification, and an updated evidence report;
- handle merge resolutions, shared contracts, and cross-component glue in the integration worktree under main-agent ownership;
- merge corrective commits and rerun the failed gate plus affected regression gates.

If a merge cannot be completed coherently, abort only that in-progress merge, preserve the component branch, and record the conflict. Never reset away committed user or integration work.

### Runtime Dependency Recovery

When a failed gate reveals a dependency missing from the approved DAG or a promotion condition that cannot run in its assigned wave, freeze the affected wave. Mark the candidate integration state red and retain the last recorded green SHA. Pause new full component merges and downstream propagation while diagnosing the failure; do not use an informal prerequisite sync to move integration `HEAD` to a component branch. Open a dated incident in `integration-review.md` with the failing command and log, candidate and last green SHAs, affected edges and branches, blocked gate, assigned owner, and next runnable action. Keep that entry current as diagnosis and ownership change.

Trace the failing command to its inputs and owners. Distinguish a consumer-dependent handoff test assigned to the producer's gate, a shared fixture or build prerequisite owned elsewhere, and a genuine mutual dependency between production contracts. Record the failing evidence, affected graph edges, and whether any already promoted branch relied on the invalid condition.

- For an early handoff test, move it to the consumer's first runnable integration gate. Keep a producer-side check that verifies the producer's own contract, and update the edge packet, coverage manifest, and promotion conditions.
- For a shared fixture or build prerequisite, route a narrowly scoped correction to its owner. After the relevant tasks and local checks pass, require a clean source worktree and inspect the commits that would enter integration. Bring only the verified correction into integration with traceable source and integration commits; keep other component work on its branch.
- For a genuine production cycle, revise component boundaries or combine inseparable work. Update affected Spec Kit artifacts, reconcile contracts, rebuild the DAG and integration design, and obtain human review when scope, ownership, contracts, or waves change. Recheck branches that already received a promotion against the revised graph before further propagation.

Record the corrected edges, owner, waves, and promotion conditions in `dependency-graph.md`, linking the incident; preserve the original failure and decision history in `integration-review.md`. Re-run DAG feasibility and the affected planning gates after the correction. Test the failed check and affected regressions against one recorded integration code SHA; rerun checks whose evidence became stale. Record each unavailable external check as pending. Apply the gate or separately approved contract-ready milestone defined before the wave; if neither permits progress, wait for the check. Once the applicable gate is green, follow the normal audit-commit and smoke-tested promotion sequence, then send only that recorded SHA to newly unblocked branches. Close the incident with the corrective commit, test results, promotion SHA, and downstream receipts only when the graph, gate evidence, branch receipts, and integration review agree on the same promotion state.

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

Before step 5, verify that the tested code SHA is an ancestor of the candidate promotion SHA and that the intervening commit contains only the audit update. After each downstream merge, verify the recorded promotion SHA is an ancestor of that branch's new `HEAD`; record the branch head and merge result. If either check fails, keep propagation closed and diagnose the mismatch.

Never merge a component branch directly into a sibling. Never substitute a newer, unverified integration `HEAD` for the recorded promotion SHA.

## Final Gate

After every component is promoted, require a real passed handoff for every declared edge and no deferred edges. Run the complete repository-required test suite plus the initiative's full integration, end-to-end, and smoke commands from the integration worktree. Record that fully tested code SHA, final commands, results, promotion history, and remaining risks in `integration-review.md`, then commit the final audit update and smoke-test that audit commit. Report both the fully tested code SHA and the smoke-verified final audit SHA; do not make the audit commit claim its own hash.

Completion leaves all branches and worktrees in place. Report the integration branch and audit paths, but do not merge integration into the baseline target and do not pause for human review approval.
