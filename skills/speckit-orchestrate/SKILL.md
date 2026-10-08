---
name: speckit-orchestrate
description: Start or resume broad, interdependent Spec Kit initiatives with dedicated worktrees, component owners, dependency-gated implementation, and audited integration promotion. Use for coordinated components, not a single isolated feature.
metadata:
  short-description: Orchestrate complex Spec Kit initiatives
---

# Spec Kit Orchestrator

Turn a broad initiative into independently owned components without losing cross-component contracts, verification evidence, or Git provenance.

Before taking action, read [references/orchestration-protocol.md](references/orchestration-protocol.md) completely. It defines the required artifacts, branch and worktree topology, agent reports, quality gates, and promotion rules.

For an existing initiative, complete the protocol's **Resume Audit** before implementation, merge, promotion, recommending a file for external use, or task dispatch. Its output is an evidence-backed resume point and an owner-routed work queue; the current directory, task checkboxes, and a prior completion claim do not establish either.

For an inspectable initiative lifecycle, read [references/orchestration-state-machine.md](references/orchestration-state-machine.md). Use `scripts/validate_orchestration_state.py` to validate one declared state transition's metadata. The integration coverage transition validates a versioned JSON manifest of runnable coverage, deferred edges, matching commands, zero exit codes, and the tested integration SHA. The validator does not persist state, execute commands, or independently verify Git history, SHAs, agents, dependency satisfaction, or concurrency.

## New Initiative Start Gate

1. Read the repository instructions that apply to the base repository and every proposed worktree.
2. Confirm the repository contains `.specify/` and local Spec Kit instructions for `specify`, `clarify`, `plan`, `tasks`, `analyze`, and `implement`.
3. Confirm Git worktrees and subagents are available. Do not silently replace requested subagents with an untracked sequential workflow.
4. Inspect the current branch, status, worktrees, existing feature prefixes, and available agent capacity.
5. Record the user-selected target branch and immutable baseline commit. If uncommitted work may belong to the initiative, stop and ask the user to commit or choose another baseline. Never stash, reset, clean, or overwrite it.

## Required Workflow

1. **Decompose**: Split the initiative into cohesive, independently specifiable components. State each component's responsibility, public contracts, expected tests, shared files, and exclusions. Prepare a provisional dependency graph and proposed worktree scopes, but do not create branches or worktrees yet.
2. **Human allocation review**: Present the human with the provisional dependency graph and, for every component, its responsibility, public contracts, expected tests, shared-file ownership, exclusions, proposed prefix, branch, worktree path, stable owner, and capacity wave. Ask only the material scope, contract, ownership, and dependency questions. Wait for explicit approval before creating any branch or worktree. If the human blocks the packet, revise decomposition and present the changed packet again; do not allocate partially.
3. **Allocate**: After approval, centrally assign every component its approved unique Spec Kit prefix, branch, worktree, and stable subagent owner. The main agent owns the dedicated integration worktree. Use capacity-bounded planning waves; never assign two agents to one worktree concurrently.
4. **Specify**: In every component worktree, complete `specify -> clarify -> plan -> tasks -> analyze`. Component agents report human decisions to the main agent; only the main agent asks the user, in deduplicated phase batches. No component may begin implementation during this stage.
5. **Gate planning**: Require complete artifacts, no unresolved clarification markers, and remediation of all CRITICAL and HIGH `speckit-analyze` findings across every component.
6. **Reconcile components**: The integration agent compares all completed component artifacts, detects cross-component ambiguity and conflicts, and records one reconciliation report. Fix deterministic integration issues, return component-local defects to their owners, and ask the human only for material semantic decisions. Reopen planning until the report passes.
7. **Build the DAG**: Derive and record the authoritative cross-component dependency graph only after reconciliation passes. Compare it with the reviewed provisional graph, resolve cycles and shared-file ownership before implementation, and reopen human review if the comparison changes scope, contracts, ownership, or implementation waves. Check that every prerequisite can pass its promotion gate using only components available before its consumers start.
8. **Design integration**: For every DAG edge, the integration agent defines an edge work packet containing both sides of the contract, invariants, minimal glue, handoff tests, end-to-end coverage, and the promotion condition. Assign each test to the earliest promotion where its inputs exist; defer the actual producer-to-consumer handoff until the consumer is integrated. Return graph issues to DAG construction and contract changes to planning. Do not activate implementation until every promotion condition is runnable in DAG order.
9. **Implement by wave**: Activate only dependency-ready components. Each owner follows `speckit-implement` plus repository-required implementation or testing skills, commits locally verified work, and remains assigned until integration promotion succeeds.
10. **Integrate serially**: Merge one component into integration at a time. Implement integration-owned glue, then re-run local checks plus currently runnable handoff, integration, end-to-end, and smoke tests. Record completed handoffs and still-blocked edges in the coverage manifest. Validate `integration_coverage_passed` before declaring `integration_passed`.
    If a runtime dependency cycle blocks a gate, follow the protocol's **Runtime Dependency Recovery** before another component merge or promotion.
11. **Promote downstream**: After a green gate, record the evidence and immutable promotion SHA, then merge that exact integration state into every newly unblocked downstream component branch and resume its owner. Never merge sibling component branches directly.
12. **Finish on integration**: Run the final full gates and write the review result. Leave the completed initiative on the integration branch; do not merge it into `main` or the original target branch, and do not wait for human review before continuing downstream work.

## Integration Agent Responsibility

- Keep one integration owner; do not add producer or consumer agent roles.
- Detect and reconcile naming, identity, schema, path, cardinality, provenance, logic, ordering, state, failure-semantics, assumption, configuration, runtime, scale, and scientific-meaning conflicts across component artifacts.
- Fix unambiguous cross-component conflicts and integration glue directly. Route component-local defects to the existing owner and rerun affected planning or verification gates.
- Ask the human only when resolution changes product or scientific meaning, scope, architecture, ownership, or another material semantic choice.
- Own edge work packets and tests that pass the producer's actual output to the consumer in the same test or run.

## Non-Negotiable Invariants

- Component feature prefixes are globally unique within the repository. Concurrent agents never auto-allocate their own prefix.
- The integration branch is the only source from which prerequisites flow downstream.
- A downstream branch receives a recorded green promotion SHA, never an unverified integration `HEAD`.
- A component merge requires completed component tasks, local verification, and a clean source worktree; a corrective merge requires the same for its scoped tasks and commits.
- An external check is pending until it runs and passes. Its effect on promotion must follow the approved gate or milestone recorded before the wave.
- The main agent alone edits orchestration and integration-review records.
- Failures are recorded with the command, output or log path, owning component, and corrective commit. Never change declared behavior or experiment configuration as a silent fallback.
- Integration promotion requires the machine-validated coverage gate. A deferred edge becomes a tested handoff when its consumer is integrated; final verification requires all declared edges to have real handoff evidence.
- Component-local regressions return to the component owner. Cross-component contracts, merge resolution, and integration glue belong to the main integration agent.
- Do not remove worktrees or branches at completion. Do not delete files except where the user's active repository instructions explicitly permit it.
- Do not rerun an unchanged failing command repeatedly. Diagnose before retrying; if the same external or product-decision blocker remains after two informed attempts, report the blocker to the user.
