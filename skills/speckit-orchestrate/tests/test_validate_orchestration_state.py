#!/usr/bin/env python3
# Tests scripts/validate_orchestration_state.py for component-scoped initiative transition validation.

import json
import subprocess
import sys
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "validate_orchestration_state.py"


def _write_valid_coverage_manifest(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "status": "passed",
                "tested_integration_sha": "def456",
                "edge_handoffs": [
                    {
                        "edge_id": "cohort->prompt-arms",
                        "producer": "cohort",
                        "consumer": "prompt-arms",
                        "test_path": "tests/integration/test_handoff.py",
                        "passed": True,
                        "upstream_output_consumed": True,
                        "synthetic_boundary_replacement": False,
                    }
                ],
                "integration": {
                    "tests": [{"path": "tests/integration/test_handoff.py", "added": True, "passed": True}],
                    "command": "pytest tests/integration/test_handoff.py",
                    "exit_code": 0,
                },
                "e2e": {
                    "tests": [{"path": "tests/e2e/test_pipeline.py", "added": True, "passed": True}],
                    "command": "pytest tests/e2e/test_pipeline.py",
                    "exit_code": 0,
                },
            }
        ),
        encoding="utf-8",
    )


def test_cli_accepts_a_locally_verified_component_for_integration():
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--state",
            "implementing",
            "--transition",
            "local_component_passed",
            "--actor",
            "component_owner",
            "--component-id",
            "canonical-cohort",
            "--evidence",
            "component_commit=abc123",
            "--evidence",
            "local_verification=audits/canonical-cohort-local.json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["accepted"] is True
    assert payload["from_state"] == "implementing"
    assert payload["to_state"] == "integration_queue"
    assert payload["component_id"] == "canonical-cohort"


def test_cli_accepts_every_legal_initiative_transition(tmp_path: Path):
    coverage_manifest = tmp_path / "coverage.json"
    _write_valid_coverage_manifest(coverage_manifest)
    transitions = [
        ("initial", "begin_preflight", "main_agent", None, ["baseline_record=abc123"]),
        ("preflight", "preflight_passed", "main_agent", None, ["preflight_record=audits/preflight.json"]),
        ("preflight", "preflight_blocked", "main_agent", None, ["blocker_record=audits/blocker.json"]),
        ("decomposing", "decomposition_complete", "main_agent", None, ["component_decomposition=specs/orchestration/components.md", "allocation_review_packet=audits/allocation-review.md"]),
        ("allocation_review", "allocation_review_approved", "main_agent", None, ["allocation_review_decision=audits/allocation-approval.json"]),
        ("allocation_review", "allocation_review_blocked", "main_agent", None, ["allocation_review_feedback=audits/allocation-feedback.json"]),
        ("allocating", "allocation_passed", "main_agent", None, ["allocation_record=audits/allocation.json"]),
        ("allocating", "allocation_blocked", "main_agent", None, ["blocker_record=audits/blocker.json"]),
        ("planning", "start_component_planning", "component_owner", "cohort", ["planning_start=specs/001-cohort/spec.md"]),
        ("planning", "ask_batched_questions", "main_agent", None, ["question_batch=audits/questions.json"]),
        ("clarification_wait", "apply_canonical_answers", "main_agent", None, ["canonical_decisions=audits/answers.json"]),
        ("planning", "planning_artifacts_ready", "main_agent", None, ["planning_package=audits/planning.json"]),
        ("artifact_gate", "artifact_gate_failed", "main_agent", None, ["remediation_record=audits/remediation.json"]),
        ("artifact_gate", "artifact_gate_passed", "main_agent", None, ["artifact_gate_report=audits/artifact-gate.json"]),
        ("cross_component_review", "cross_component_review_failed", "main_agent", None, ["remediation_record=audits/cross-component-remediation.json"]),
        ("cross_component_review", "cross_component_review_questions", "main_agent", None, ["question_batch=audits/cross-component-questions.json"]),
        ("cross_component_review", "cross_component_review_passed", "main_agent", None, ["reconciliation_report=audits/cross-component-review.json"]),
        ("dag_building", "dag_cycle_or_contract_change", "main_agent", None, ["dag_issue=audits/dag-issue.json"]),
        ("dag_building", "dag_passed", "main_agent", None, ["dependency_graph=specs/orchestration/graph.md"]),
        ("integration_design", "integration_design_rework", "main_agent", None, ["design_issue=audits/integration-design-issue.json"]),
        ("integration_design", "integration_design_contract_change", "main_agent", None, ["contract_change=audits/integration-contract-change.json"]),
        ("integration_design", "integration_design_passed", "main_agent", None, ["edge_work_packets=specs/orchestration/graph.md", "integration_test_plan=audits/integration-test-plan.json"]),
        ("implementation_ready", "start_implementation_wave", "main_agent", None, ["activation_record=audits/wave.json"]),
        ("implementing", "local_component_passed", "component_owner", "cohort", ["component_commit=abc123", "local_verification=audits/local.json"]),
        ("integration_queue", "begin_integration", "main_agent", "cohort", ["integration_start=audits/integration-start.json"]),
        ("integrating", "integration_failed", "main_agent", "cohort", ["integration_failure=audits/failure.json"]),
        ("integration_red", "route_integration_fix", "main_agent", "cohort", ["corrective_commit=def456"]),
        ("integrating", "integration_coverage_passed", "main_agent", "cohort", [f"coverage_manifest={coverage_manifest}", "tested_integration_sha=def456"]),
        ("integration_coverage_ready", "integration_passed", "main_agent", "cohort", ["integration_verification=audits/integration.json", "tested_integration_sha=def456"]),
        ("promotion_ready", "promote_green_state", "main_agent", "cohort", ["promotion_sha=def456", "promotion_smoke=audits/smoke.json"]),
        ("propagating", "propagation_complete", "main_agent", None, ["propagation_record=audits/propagation.json"]),
        ("final_verification", "final_gates_passed", "main_agent", None, ["final_verification=audits/final.json", "final_audit_smoke=audits/final-smoke.json"]),
    ]

    for state, transition, actor, component_id, evidence in transitions:
        command = [
            sys.executable,
            str(SCRIPT),
            "--state",
            state,
            "--transition",
            transition,
            "--actor",
            actor,
        ]
        if component_id:
            command.extend(["--component-id", component_id])
        for evidence_reference in evidence:
            command.extend(["--evidence", evidence_reference])

        result = subprocess.run(command, check=True, capture_output=True, text=True)
        assert json.loads(result.stdout)["accepted"] is True


def test_cli_rejects_invalid_transition_metadata_and_terminal_mutation():
    cases = [
        (["--state", "unknown", "--transition", "begin_preflight", "--actor", "main_agent", "--evidence", "baseline_record=abc123"], "unknown state: unknown"),
        (["--state", "initial", "--transition", "unknown", "--actor", "main_agent"], "unknown transition: unknown"),
        (["--state", "planning", "--transition", "begin_preflight", "--actor", "main_agent", "--evidence", "baseline_record=abc123"], "requires source state initial"),
        (["--state", "initial", "--transition", "begin_preflight", "--actor", "component_owner", "--evidence", "baseline_record=abc123"], "requires actor main_agent"),
        (["--state", "initial", "--transition", "begin_preflight", "--actor", "main_agent"], "requires evidence: baseline_record"),
        (["--state", "implementing", "--transition", "local_component_passed", "--actor", "component_owner", "--evidence", "component_commit=abc123", "--evidence", "local_verification=audits/local.json"], "requires component_id"),
        (["--state", "completed", "--transition", "begin_preflight", "--actor", "main_agent", "--evidence", "baseline_record=abc123"], "terminal state cannot transition: completed"),
        (["--state", "blocked", "--transition", "begin_preflight", "--actor", "main_agent", "--evidence", "baseline_record=abc123"], "terminal state cannot transition: blocked"),
        (["--state", "integrating", "--transition", "integration_passed", "--actor", "main_agent", "--component-id", "cohort", "--evidence", "integration_verification=audits/integration.json", "--evidence", "tested_integration_sha=def456"], "requires source state integration_coverage_ready"),
    ]

    for arguments, expected_error in cases:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *arguments],
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 2
        assert expected_error in result.stderr


def test_cli_accepts_a_machine_validated_integration_e2e_coverage_manifest(tmp_path: Path):
    manifest = tmp_path / "coverage.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "status": "passed",
                "tested_integration_sha": "def456",
                "edge_handoffs": [
                    {
                        "edge_id": "cohort->prompt-arms",
                        "producer": "cohort",
                        "consumer": "prompt-arms",
                        "test_path": "tests/integration/test_handoff.py",
                        "passed": True,
                        "upstream_output_consumed": True,
                        "synthetic_boundary_replacement": False,
                    }
                ],
                "integration": {
                    "tests": [{"path": "tests/integration/test_handoff.py", "added": True, "passed": True}],
                    "command": "pytest tests/integration/test_handoff.py",
                    "exit_code": 0,
                },
                "e2e": {
                    "tests": [{"path": "tests/e2e/test_pipeline.py", "added": True, "passed": True}],
                    "command": "pytest tests/e2e/test_pipeline.py",
                    "exit_code": 0,
                },
            }
        ),
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--state",
            "integrating",
            "--transition",
            "integration_coverage_passed",
            "--actor",
            "main_agent",
            "--component-id",
            "cohort",
            "--evidence",
            f"coverage_manifest={manifest}",
            "--evidence",
            "tested_integration_sha=def456",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["to_state"] == "integration_coverage_ready"
    assert payload["coverage_manifest"]["status"] == "passed"


def test_cli_rejects_coverage_without_new_passed_e2e_test(tmp_path: Path):
    manifest = tmp_path / "coverage.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "status": "passed",
                "tested_integration_sha": "def456",
                "edge_handoffs": [
                    {
                        "edge_id": "cohort->prompt-arms",
                        "producer": "cohort",
                        "consumer": "prompt-arms",
                        "test_path": "tests/integration/test_handoff.py",
                        "passed": True,
                        "upstream_output_consumed": True,
                        "synthetic_boundary_replacement": False,
                    }
                ],
                "integration": {
                    "tests": [{"path": "tests/integration/test_handoff.py", "added": True, "passed": True}],
                    "command": "pytest tests/integration/test_handoff.py",
                    "exit_code": 0,
                },
                "e2e": {
                    "tests": [{"path": "tests/e2e/test_pipeline.py", "added": False, "passed": True}],
                    "command": "pytest tests/e2e/test_pipeline.py",
                    "exit_code": 0,
                },
            }
        ),
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--state",
            "integrating",
            "--transition",
            "integration_coverage_passed",
            "--actor",
            "main_agent",
            "--component-id",
            "cohort",
            "--evidence",
            f"coverage_manifest={manifest}",
            "--evidence",
            "tested_integration_sha=def456",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "e2e" in result.stderr


def test_cli_rejects_invalid_or_disconnected_edge_handoffs(tmp_path: Path):
    base_manifest = {
        "schema_version": 2,
        "status": "passed",
        "tested_integration_sha": "def456",
        "edge_handoffs": [
            {
                "edge_id": "cohort->prompt-arms",
                "producer": "cohort",
                "consumer": "prompt-arms",
                "test_path": "tests/integration/test_handoff.py",
                "passed": True,
                "upstream_output_consumed": True,
                "synthetic_boundary_replacement": False,
            }
        ],
        "integration": {
            "tests": [
                {
                    "path": "tests/integration/test_handoff.py",
                    "added": True,
                    "passed": True,
                }
            ],
            "command": "pytest tests/integration/test_handoff.py",
            "exit_code": 0,
        },
        "e2e": {
            "tests": [
                {
                    "path": "tests/e2e/test_pipeline.py",
                    "added": True,
                    "passed": True,
                }
            ],
            "command": "pytest tests/e2e/test_pipeline.py",
            "exit_code": 0,
        },
    }
    cases = [
        (None, "non-empty edge_handoffs list"),
        ({"schema_version": 1}, "schema_version=2"),
        ({"edge_handoffs": []}, "non-empty edge_handoffs list"),
        ({"edge_handoffs": None}, "non-empty edge_handoffs list"),
        ({"edge_handoffs": [{**base_manifest["edge_handoffs"][0], "edge_id": ""}]}, "edge_handoffs[0].edge_id"),
        ({"edge_handoffs": [{**base_manifest["edge_handoffs"][0], "producer": ""}]}, "edge_handoffs[0].producer"),
        ({"edge_handoffs": [{**base_manifest["edge_handoffs"][0], "consumer": ""}]}, "edge_handoffs[0].consumer"),
        ({"edge_handoffs": [{**base_manifest["edge_handoffs"][0], "test_path": "tests/unit/test_handoff.py"}]}, "integration test path"),
        ({"edge_handoffs": [{**base_manifest["edge_handoffs"][0], "passed": False}]}, "edge_handoffs[0].passed"),
        ({"edge_handoffs": [{**base_manifest["edge_handoffs"][0], "upstream_output_consumed": False}]}, "consume upstream output"),
        ({"edge_handoffs": [{**base_manifest["edge_handoffs"][0], "synthetic_boundary_replacement": True}]}, "synthetic boundary replacement"),
        (
            {
                "integration": {
                    **base_manifest["integration"],
                    "tests": [
                        {
                            "path": "tests/integration/test_other.py",
                            "added": True,
                            "passed": True,
                        }
                    ],
                }
            },
            "declared new passed integration test",
        ),
    ]

    for index, (replacement, expected_error) in enumerate(cases):
        manifest_data = dict(base_manifest)
        if replacement is None:
            del manifest_data["edge_handoffs"]
        else:
            manifest_data.update(replacement)
        manifest = tmp_path / f"coverage-{index}.json"
        manifest.write_text(json.dumps(manifest_data), encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--state",
                "integrating",
                "--transition",
                "integration_coverage_passed",
                "--actor",
                "main_agent",
                "--component-id",
                "cohort",
                "--evidence",
                f"coverage_manifest={manifest}",
                "--evidence",
                "tested_integration_sha=def456",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 2
        assert expected_error in result.stderr


def test_cross_component_review_and_integration_design_route_by_issue_type():
    cases = [
        (
            "cross_component_review",
            "cross_component_review_failed",
            {"remediation_record": "audits/cross-component-remediation.json"},
            "planning",
        ),
        (
            "cross_component_review",
            "cross_component_review_questions",
            {"question_batch": "audits/cross-component-questions.json"},
            "clarification_wait",
        ),
        (
            "cross_component_review",
            "cross_component_review_passed",
            {"reconciliation_report": "audits/cross-component-review.json"},
            "dag_building",
        ),
        (
            "integration_design",
            "integration_design_rework",
            {"design_issue": "audits/integration-design-issue.json"},
            "dag_building",
        ),
        (
            "integration_design",
            "integration_design_contract_change",
            {"contract_change": "audits/integration-contract-change.json"},
            "planning",
        ),
        (
            "integration_design",
            "integration_design_passed",
            {
                "edge_work_packets": "specs/orchestration/graph.md",
                "integration_test_plan": "audits/integration-test-plan.json",
            },
            "implementation_ready",
        ),
    ]

    for state, transition, evidence, expected_state in cases:
        payload = validate_cli(state, transition, "main_agent", None, evidence)
        assert payload["to_state"] == expected_state


def test_cli_has_a_path_to_each_terminal_state(tmp_path: Path):
    coverage_manifest = tmp_path / "coverage.json"
    _write_valid_coverage_manifest(coverage_manifest)
    completed_path = [
        ("initial", "begin_preflight", "main_agent", None, ["baseline_record=abc123"]),
        ("preflight", "preflight_passed", "main_agent", None, ["preflight_record=audits/preflight.json"]),
        ("decomposing", "decomposition_complete", "main_agent", None, ["component_decomposition=specs/orchestration/components.md", "allocation_review_packet=audits/allocation-review.md"]),
        ("allocation_review", "allocation_review_approved", "main_agent", None, ["allocation_review_decision=audits/allocation-approval.json"]),
        ("allocating", "allocation_passed", "main_agent", None, ["allocation_record=audits/allocation.json"]),
        ("planning", "planning_artifacts_ready", "main_agent", None, ["planning_package=audits/planning.json"]),
        ("artifact_gate", "artifact_gate_passed", "main_agent", None, ["artifact_gate_report=audits/artifact-gate.json"]),
        ("cross_component_review", "cross_component_review_passed", "main_agent", None, ["reconciliation_report=audits/cross-component-review.json"]),
        ("dag_building", "dag_passed", "main_agent", None, ["dependency_graph=specs/orchestration/graph.md"]),
        ("integration_design", "integration_design_passed", "main_agent", None, ["edge_work_packets=specs/orchestration/graph.md", "integration_test_plan=audits/integration-test-plan.json"]),
        ("implementation_ready", "start_implementation_wave", "main_agent", None, ["activation_record=audits/wave.json"]),
        ("implementing", "local_component_passed", "component_owner", "cohort", ["component_commit=abc123", "local_verification=audits/local.json"]),
        ("integration_queue", "begin_integration", "main_agent", "cohort", ["integration_start=audits/integration-start.json"]),
        ("integrating", "integration_coverage_passed", "main_agent", "cohort", [f"coverage_manifest={coverage_manifest}", "tested_integration_sha=def456"]),
        ("integration_coverage_ready", "integration_passed", "main_agent", "cohort", ["integration_verification=audits/integration.json", "tested_integration_sha=def456"]),
        ("promotion_ready", "promote_green_state", "main_agent", "cohort", ["promotion_sha=def456", "promotion_smoke=audits/smoke.json"]),
        ("propagating", "propagation_complete", "main_agent", None, ["propagation_record=audits/propagation.json"]),
        ("final_verification", "final_gates_passed", "main_agent", None, ["final_verification=audits/final.json", "final_audit_smoke=audits/final-smoke.json"]),
    ]
    blocked_path = [
        ("initial", "begin_preflight", "main_agent", None, ["baseline_record=abc123"]),
        ("preflight", "preflight_blocked", "main_agent", None, ["blocker_record=audits/blocker.json"]),
    ]

    for path, terminal_state in ((completed_path, "completed"), (blocked_path, "blocked")):
        current_state = path[0][0]
        for state, transition, actor, component_id, evidence in path:
            assert state == current_state
            evidence_map = dict(item.split("=", maxsplit=1) for item in evidence)
            payload = validate_cli(state, transition, actor, component_id, evidence_map)
            current_state = payload["to_state"]
        assert current_state == terminal_state


def validate_cli(
    state: str,
    transition: str,
    actor: str,
    component_id: str | None,
    evidence: dict[str, str],
) -> dict[str, object]:
    command = [
        sys.executable,
        str(SCRIPT),
        "--state",
        state,
        "--transition",
        transition,
        "--actor",
        actor,
    ]
    if component_id:
        command.extend(["--component-id", component_id])
    for key, value in evidence.items():
        command.extend(["--evidence", f"{key}={value}"])
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)
