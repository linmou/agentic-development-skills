#!/usr/bin/env python3
# Purpose: Validate one source-derived Speckit orchestration state transition without persisting workflow state.

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import cast


class StateValidationError(ValueError):
    """Raised when a requested orchestration transition is not legal."""


@dataclass(frozen=True)
class Transition:
    name: str
    from_state: str
    to_state: str
    actor: str
    evidence_keys: tuple[str, ...]
    requires_component_id: bool


TRANSITIONS = {
    transition.name: transition
    for transition in (
        Transition("begin_preflight", "initial", "preflight", "main_agent", ("baseline_record",), False),
        Transition("preflight_passed", "preflight", "decomposing", "main_agent", ("preflight_record",), False),
        Transition("preflight_blocked", "preflight", "blocked", "main_agent", ("blocker_record",), False),
        Transition("decomposition_complete", "decomposing", "allocation_review", "main_agent", ("component_decomposition", "allocation_review_packet"), False),
        Transition("allocation_review_approved", "allocation_review", "allocating", "main_agent", ("allocation_review_decision",), False),
        Transition("allocation_review_blocked", "allocation_review", "decomposing", "main_agent", ("allocation_review_feedback",), False),
        Transition("allocation_passed", "allocating", "planning", "main_agent", ("allocation_record",), False),
        Transition("allocation_blocked", "allocating", "blocked", "main_agent", ("blocker_record",), False),
        Transition("start_component_planning", "planning", "planning", "component_owner", ("planning_start",), True),
        Transition("ask_batched_questions", "planning", "clarification_wait", "main_agent", ("question_batch",), False),
        Transition("apply_canonical_answers", "clarification_wait", "planning", "main_agent", ("canonical_decisions",), False),
        Transition("planning_artifacts_ready", "planning", "artifact_gate", "main_agent", ("planning_package",), False),
        Transition("artifact_gate_failed", "artifact_gate", "planning", "main_agent", ("remediation_record",), False),
        Transition("artifact_gate_passed", "artifact_gate", "cross_component_review", "main_agent", ("artifact_gate_report",), False),
        Transition("cross_component_review_failed", "cross_component_review", "planning", "main_agent", ("remediation_record",), False),
        Transition("cross_component_review_questions", "cross_component_review", "clarification_wait", "main_agent", ("question_batch",), False),
        Transition("cross_component_review_passed", "cross_component_review", "dag_building", "main_agent", ("reconciliation_report",), False),
        Transition("dag_cycle_or_contract_change", "dag_building", "planning", "main_agent", ("dag_issue",), False),
        Transition("dag_passed", "dag_building", "integration_design", "main_agent", ("dependency_graph",), False),
        Transition("integration_design_rework", "integration_design", "dag_building", "main_agent", ("design_issue",), False),
        Transition("integration_design_contract_change", "integration_design", "planning", "main_agent", ("contract_change",), False),
        Transition("integration_design_passed", "integration_design", "implementation_ready", "main_agent", ("edge_work_packets", "integration_test_plan"), False),
        Transition("start_implementation_wave", "implementation_ready", "implementing", "main_agent", ("activation_record",), False),
        Transition("local_component_passed", "implementing", "integration_queue", "component_owner", ("component_commit", "local_verification"), True),
        Transition("begin_integration", "integration_queue", "integrating", "main_agent", ("integration_start",), True),
        Transition("integration_failed", "integrating", "integration_red", "main_agent", ("integration_failure",), True),
        Transition("route_integration_fix", "integration_red", "integrating", "main_agent", ("corrective_commit",), True),
        Transition("integration_coverage_passed", "integrating", "integration_coverage_ready", "main_agent", ("coverage_manifest", "tested_integration_sha"), True),
        Transition("integration_passed", "integration_coverage_ready", "promotion_ready", "main_agent", ("integration_verification", "tested_integration_sha"), True),
        Transition("promote_green_state", "promotion_ready", "propagating", "main_agent", ("promotion_sha", "promotion_smoke"), True),
        Transition("propagation_complete", "propagating", "final_verification", "main_agent", ("propagation_record",), False),
        Transition("final_gates_passed", "final_verification", "completed", "main_agent", ("final_verification", "final_audit_smoke"), False),
    )
}
STATES = frozenset({
    "initial",
    "preflight",
    "decomposing",
    "allocation_review",
    "allocating",
    "planning",
    "clarification_wait",
    "artifact_gate",
    "cross_component_review",
    "dag_building",
    "integration_design",
    "implementation_ready",
    "implementing",
    "integration_queue",
    "integrating",
    "integration_red",
    "integration_coverage_ready",
    "promotion_ready",
    "propagating",
    "final_verification",
    "completed",
    "blocked",
})
TERMINAL_STATES = frozenset({"completed", "blocked"})


def parse_evidence(items: list[str]) -> dict[str, str]:
    evidence: dict[str, str] = {}
    for item in items:
        key, separator, value = item.partition("=")
        if not separator or not key or not value:
            raise StateValidationError("evidence must use non-empty key=value form")
        evidence[key] = value
    return evidence


def _read_coverage_manifest(path_value: str) -> dict[str, object]:
    path = Path(path_value)
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StateValidationError(f"coverage manifest is not valid JSON: {path}") from exc

    if not isinstance(manifest, dict):
        raise StateValidationError("coverage manifest must be a JSON object")
    return manifest


def _validate_coverage_section(
    manifest: dict[str, object], category: str, directory: str
) -> None:
    section = manifest.get(category)
    if not isinstance(section, dict):
        raise StateValidationError(f"coverage manifest requires {category} section")
    tests = section.get("tests")
    if not isinstance(tests, list):
        raise StateValidationError(f"coverage manifest {category}.tests must be a list")
    if not any(
        isinstance(test, dict)
        and isinstance(test.get("path"), str)
        and test["path"].startswith(directory)
        and test.get("added") is True
        and test.get("passed") is True
        for test in tests
    ):
        raise StateValidationError(f"coverage manifest requires a new passed {category} test")
    if not isinstance(section.get("command"), str) or not section["command"].strip():
        raise StateValidationError(f"coverage manifest requires {category}.command")
    if section.get("exit_code") != 0:
        raise StateValidationError(f"coverage manifest {category}.exit_code must be 0")


def _validate_edge_handoff(
    handoff: object, index: int, passed_test_paths: set[str]
) -> None:
    if not isinstance(handoff, dict):
        raise StateValidationError(f"coverage manifest edge_handoffs[{index}] must be an object")
    for field in ("edge_id", "producer", "consumer"):
        value = handoff.get(field)
        if not isinstance(value, str) or not value.strip():
            raise StateValidationError(
                f"coverage manifest edge_handoffs[{index}].{field} must be a non-empty string"
            )

    test_path = handoff.get("test_path")
    if not isinstance(test_path, str) or not test_path.startswith("tests/integration/"):
        raise StateValidationError(
            f"coverage manifest edge_handoffs[{index}].test_path must be an integration test path"
        )
    if handoff.get("passed") is not True:
        raise StateValidationError(
            f"coverage manifest edge_handoffs[{index}].passed must be true"
        )
    if handoff.get("upstream_output_consumed") is not True:
        raise StateValidationError(
            f"coverage manifest edge_handoffs[{index}] must consume upstream output"
        )
    if handoff.get("synthetic_boundary_replacement") is not False:
        raise StateValidationError(
            f"coverage manifest edge_handoffs[{index}] must not use a synthetic boundary replacement"
        )
    if test_path not in passed_test_paths:
        raise StateValidationError(
            f"coverage manifest edge_handoffs[{index}].test_path must name a declared new passed integration test"
        )


def _validate_edge_handoffs(manifest: dict[str, object]) -> None:
    handoffs = manifest.get("edge_handoffs")
    if not isinstance(handoffs, list) or not handoffs:
        raise StateValidationError("coverage manifest requires a non-empty edge_handoffs list")

    integration = cast(dict[str, object], manifest["integration"])
    integration_tests = cast(list[object], integration["tests"])
    passed_test_paths = {
        test["path"]
        for test in integration_tests
        if isinstance(test, dict)
        and isinstance(test.get("path"), str)
        and test.get("added") is True
        and test.get("passed") is True
    }

    for index, handoff in enumerate(handoffs):
        _validate_edge_handoff(handoff, index, passed_test_paths)


def validate_coverage_manifest(path_value: str, tested_sha: str) -> dict[str, object]:
    manifest = _read_coverage_manifest(path_value)
    if manifest.get("schema_version") != 2:
        raise StateValidationError("coverage manifest requires schema_version=2")
    if manifest.get("status") != "passed":
        raise StateValidationError("coverage manifest status must be passed")
    if manifest.get("tested_integration_sha") != tested_sha:
        raise StateValidationError("coverage manifest tested_integration_sha must match transition evidence")

    _validate_coverage_section(manifest, "integration", "tests/integration/")
    _validate_coverage_section(manifest, "e2e", "tests/e2e/")
    _validate_edge_handoffs(manifest)

    return manifest


def validate_transition(
    state: str,
    transition_name: str,
    actor: str,
    component_id: str | None,
    evidence: dict[str, str],
) -> dict[str, object]:
    if state not in STATES:
        raise StateValidationError(f"unknown state: {state}")
    if state in TERMINAL_STATES:
        raise StateValidationError(f"terminal state cannot transition: {state}")

    transition = TRANSITIONS.get(transition_name)
    if transition is None:
        raise StateValidationError(f"unknown transition: {transition_name}")
    if state != transition.from_state:
        raise StateValidationError(
            f"transition {transition.name} requires source state {transition.from_state}"
        )
    if actor != transition.actor:
        raise StateValidationError(
            f"transition {transition.name} requires actor {transition.actor}"
        )
    if transition.requires_component_id and not component_id:
        raise StateValidationError(f"transition {transition.name} requires component_id")

    missing_keys = [key for key in transition.evidence_keys if not evidence.get(key)]
    if missing_keys:
        raise StateValidationError(
            f"transition {transition.name} requires evidence: {', '.join(missing_keys)}"
        )

    coverage_manifest: dict[str, object] | None = None
    if transition.name == "integration_coverage_passed":
        coverage_manifest = validate_coverage_manifest(
            evidence["coverage_manifest"], evidence["tested_integration_sha"]
        )

    result: dict[str, object] = {
        "accepted": True,
        "transition": transition.name,
        "from_state": transition.from_state,
        "to_state": transition.to_state,
        "component_id": component_id,
    }
    if coverage_manifest is not None:
        result["coverage_manifest"] = {
            "status": coverage_manifest["status"],
            "schema_version": coverage_manifest["schema_version"],
        }
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", required=True)
    parser.add_argument("--transition", required=True)
    parser.add_argument("--actor", required=True)
    parser.add_argument("--component-id")
    parser.add_argument("--evidence", action="append", default=[])
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = validate_transition(
            state=args.state,
            transition_name=args.transition,
            actor=args.actor,
            component_id=args.component_id,
            evidence=parse_evidence(args.evidence),
        )
    except StateValidationError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
