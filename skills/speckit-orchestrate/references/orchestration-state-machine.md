# Orchestration State Machine

**Intent**: Make the initiative lifecycle in the orchestration protocol inspectable and validate declared transition metadata without introducing workflow persistence.

## Source And Boundary

This contract is derived from [the orchestrator workflow](../SKILL.md) and [the orchestration protocol](orchestration-protocol.md): preflight, decomposition, human allocation review, allocation, Spec Kit planning, the artifact gate, cross-component reconciliation, DAG construction, integration design, implementation waves, serial integration, green promotion, downstream propagation, and final verification.

Use `scripts/validate_orchestration_state.py` to validate one claimed transition:

```bash
python3 scripts/validate_orchestration_state.py \
  --state implementing \
  --transition local_component_passed \
  --actor component_owner \
  --component-id canonical-cohort \
  --evidence component_commit=<commit-reference> \
  --evidence local_verification=<verification-reference>
```

The validator is pure and does not persist state. The caller retains the initiative record and submits its current declared state on each invocation.

For ordinary transitions it validates transition name, declared source state, declared actor, required evidence-reference presence, required non-empty `component_id`, and terminal-state immutability. For `integration_coverage_passed`, it also reads the referenced JSON coverage manifest and validates `schema_version == 2`, `status == "passed"`, a matching `tested_integration_sha`, at least one manifest-declared new passed test under both `tests/integration/` and `tests/e2e/`, non-empty commands, zero exit codes, and a non-empty list of producer-to-consumer handoffs. Each handoff must identify its edge and endpoints, point to a declared new passed integration test, consume upstream output, and reject synthetic boundary replacement. The validator does not inspect test code or prove these declarations independently.

## States

Initial state: `initial`.

Terminal states: `completed`, `blocked`.

Non-terminal states: `preflight`, `decomposing`, `allocation_review`, `allocating`, `planning`, `clarification_wait`, `artifact_gate`, `cross_component_review`, `dag_building`, `integration_design`, `implementation_ready`, `implementing`, `integration_queue`, `integrating`, `integration_red`, `integration_coverage_ready`, `promotion_ready`, `propagating`, and `final_verification`.

## Legal Transitions

`component_id` is required only where the table says `yes`.

| Transition | From | To | Actor | Component ID | Required evidence references |
|---|---|---|---|---|---|
| `begin_preflight` | `initial` | `preflight` | `main_agent` | no | `baseline_record` |
| `preflight_passed` | `preflight` | `decomposing` | `main_agent` | no | `preflight_record` |
| `preflight_blocked` | `preflight` | `blocked` | `main_agent` | no | `blocker_record` |
| `decomposition_complete` | `decomposing` | `allocation_review` | `main_agent` | no | `component_decomposition`, `allocation_review_packet` |
| `allocation_review_approved` | `allocation_review` | `allocating` | `main_agent` | no | `allocation_review_decision` |
| `allocation_review_blocked` | `allocation_review` | `decomposing` | `main_agent` | no | `allocation_review_feedback` |
| `allocation_passed` | `allocating` | `planning` | `main_agent` | no | `allocation_record` |
| `allocation_blocked` | `allocating` | `blocked` | `main_agent` | no | `blocker_record` |
| `start_component_planning` | `planning` | `planning` | `component_owner` | yes | `planning_start` |
| `ask_batched_questions` | `planning` | `clarification_wait` | `main_agent` | no | `question_batch` |
| `apply_canonical_answers` | `clarification_wait` | `planning` | `main_agent` | no | `canonical_decisions` |
| `planning_artifacts_ready` | `planning` | `artifact_gate` | `main_agent` | no | `planning_package` |
| `artifact_gate_failed` | `artifact_gate` | `planning` | `main_agent` | no | `remediation_record` |
| `artifact_gate_passed` | `artifact_gate` | `cross_component_review` | `main_agent` | no | `artifact_gate_report` |
| `cross_component_review_failed` | `cross_component_review` | `planning` | `main_agent` | no | `remediation_record` |
| `cross_component_review_questions` | `cross_component_review` | `clarification_wait` | `main_agent` | no | `question_batch` |
| `cross_component_review_passed` | `cross_component_review` | `dag_building` | `main_agent` | no | `reconciliation_report` |
| `dag_cycle_or_contract_change` | `dag_building` | `planning` | `main_agent` | no | `dag_issue` |
| `dag_passed` | `dag_building` | `integration_design` | `main_agent` | no | `dependency_graph` |
| `integration_design_rework` | `integration_design` | `dag_building` | `main_agent` | no | `design_issue` |
| `integration_design_contract_change` | `integration_design` | `planning` | `main_agent` | no | `contract_change` |
| `integration_design_passed` | `integration_design` | `implementation_ready` | `main_agent` | no | `edge_work_packets`, `integration_test_plan` |
| `start_implementation_wave` | `implementation_ready` | `implementing` | `main_agent` | no | `activation_record` |
| `local_component_passed` | `implementing` | `integration_queue` | `component_owner` | yes | `component_commit`, `local_verification` |
| `begin_integration` | `integration_queue` | `integrating` | `main_agent` | yes | `integration_start` |
| `integration_failed` | `integrating` | `integration_red` | `main_agent` | yes | `integration_failure` |
| `route_integration_fix` | `integration_red` | `integrating` | `main_agent` | yes | `corrective_commit` |
| `integration_coverage_passed` | `integrating` | `integration_coverage_ready` | `main_agent` | yes | `coverage_manifest`, `tested_integration_sha` |
| `integration_passed` | `integration_coverage_ready` | `promotion_ready` | `main_agent` | yes | `integration_verification`, `tested_integration_sha` |
| `promote_green_state` | `promotion_ready` | `propagating` | `main_agent` | yes | `promotion_sha`, `promotion_smoke` |
| `propagation_complete` | `propagating` | `final_verification` | `main_agent` | no | `propagation_record` |
| `final_gates_passed` | `final_verification` | `completed` | `main_agent` | no | `final_verification`, `final_audit_smoke` |

## Invariants And Rejections

- A caller cannot transition from `completed` or `blocked`.
- Worktree allocation cannot be declared ready until the initiative has passed through `allocation_review` and `allocation_review_approved`.
- Implementation cannot become ready until cross-component reconciliation and integration design both pass.
- Reconciliation returns component defects to planning, material questions to clarification, and only a clean report to DAG construction.
- Integration design returns graph-only defects to DAG construction and component-contract changes to planning.
- A transition is accepted only from its declared source state and declared actor.
- Component-scoped integration and implementation events require a non-empty `component_id`; it names the component but is not persisted or independently tracked by this validator.
- Every listed evidence key requires a non-empty reference value. Extra evidence keys are permitted and not interpreted.
- `integration_passed` is rejected unless the current declared state is `integration_coverage_ready`; that state can be reached only through `integration_coverage_passed`.
- The coverage manifest must be valid schema-version-2 JSON with declared results for both test categories and at least one valid edge handoff. Every handoff test path must also appear as a new passed integration test.
- `upstream_output_consumed: true` and `synthetic_boundary_replacement: false` are manifest assertions. The validator does not inspect test dataflow or compare paths with a Git baseline.
- An unknown state, unknown transition, malformed `key=value` evidence, incorrect actor, wrong source state, missing component ID, or missing required evidence is rejected with exit code `2`.

## Initiative-Level Limitation

This is deliberately an initiative-level machine, not a per-component runtime. A real initiative can have multiple owners planning or implementing concurrently while the integration worktree processes one component at a time. The validator cannot establish those facts from a single transition request. Human decisions, reconciliation, and edge work packets are represented by opaque evidence references; the validator cannot judge their semantic quality. The coverage gate validates manifest structure and declarations, but does not execute commands, inspect test dataflow, or prove that `added: true` reflects Git history. The control artifacts required by the protocol, especially `dependency-graph.md` and `integration-review.md`, remain authoritative for ownership, reconciled contracts, edge designs, promotion SHAs, test results, and integration history.

Do not treat a successful validation as proof that the protocol's external gates passed. It proves only that the supplied metadata has the shape required for the named lifecycle move.
