#!/usr/bin/env python3
# Responsible file: scripts/red_review_gate.py; purpose: verify risk-scaled Red follow-up gates.

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "scripts" / "red_review_gate.py"
AUDIT_REQUIRED_TOP_LEVEL_FIELDS = (
    "feature_name",
    "phase",
    "iteration",
    "reviewer_id",
    "reviewer_agent_id",
    "reviewer_source",
    "claim",
    "overall_verdict",
    "overall_confidence",
    "criteria",
    "open_questions",
    "disputed_points_if_any",
)
CRITERION_REQUIRED_FIELDS = (
    "id",
    "text",
    "blocking",
    "verdict",
    "confidence",
    "evidence",
    "reasoning",
    "counterevidence",
)


def criterion(
    criterion_id: str,
    verdict: str,
    *,
    blocking: bool = True,
    text: str | None = None,
    evidence: list[dict[str, str]] | None = None,
    counterevidence: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return {
        "id": criterion_id,
        "text": text or f"Criterion {criterion_id}",
        "blocking": blocking,
        "verdict": verdict,
        "confidence": 0.9,
        "evidence": evidence if evidence is not None else [{"kind": "test", "location": "red.log"}],
        "reasoning": "Evidence-bound result.",
        "counterevidence": counterevidence or [],
    }


def audit(slot: str, criteria: list[dict[str, Any]]) -> dict[str, Any]:
    overall = "fail" if any(item["verdict"] == "fail" for item in criteria) else "pass"
    if any(item["verdict"] == "insufficient_evidence" for item in criteria):
        overall = "insufficient_evidence"
    reviewer_agent_id = (
        f"agent:initial-{slot}"
        if slot in {"audit1", "audit2", "audit3"}
        else "agent:focused-reviewer"
    )
    return {
        "feature_name": "selector",
        "phase": "red",
        "iteration": 1,
        "reviewer_id": slot,
        "reviewer_agent_id": reviewer_agent_id,
        "reviewer_source": "test.delegate",
        "claim": "The Red behavior is complete.",
        "overall_verdict": overall,
        "overall_confidence": 0.9,
        "criteria": criteria,
        "open_questions": [],
        "disputed_points_if_any": [],
    }


def write_initial_set(tmp_path: Path) -> tuple[Path, list[Path]]:
    receipt = tmp_path / "roles.json"
    receipt.write_text(
        json.dumps(
            {
                "schema": 2,
                "feature": "selector",
                "route": "compact",
                "monitor_agent_id": "agent:monitor",
                "monitor_source": "test.delegate",
                "red_reviewer_agent_ids": [
                    "agent:initial-audit1",
                    "agent:initial-audit2",
                    "agent:initial-audit3",
                ],
                "reviewer_source": "test.delegate",
            }
        )
    )
    paths: list[Path] = []
    for slot in ("audit1", "audit2", "audit3"):
        path = tmp_path / f"selector_red_{slot}_iteration1.json"
        path.write_text(
            json.dumps(
                audit(
                    slot,
                    [criterion("repair", "fail"), criterion("stable", "pass", blocking=False)],
                )
            )
        )
        paths.append(path)
    return receipt, paths


def run_initial(
    tmp_path: Path,
    receipt: Path,
    audits: list[Path],
    *,
    route: str = "compact",
    risk_tier: str = "low",
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(GATE),
            "initial",
            "--route",
            route,
            "--risk-tier",
            risk_tier,
            "--role-receipt",
            str(receipt),
            "--output",
            str(tmp_path / "eligibility.json"),
            *[str(path) for path in audits],
        ],
        text=True,
        capture_output=True,
        check=False,
    )


def run_provenance(
    tmp_path: Path,
    receipt: Path,
    audits: list[Path],
    *,
    iteration: int = 1,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(GATE),
            "provenance",
            "--role-receipt",
            str(receipt),
            "--iteration",
            str(iteration),
            "--output",
            str(tmp_path / "provenance.json"),
            *[str(path) for path in audits],
        ],
        text=True,
        capture_output=True,
        check=False,
    )


def write_focused(tmp_path: Path, focused_criterion: dict[str, Any]) -> Path:
    payload = audit("focused", [focused_criterion])
    payload["iteration"] = 2
    payload["overall_verdict"] = focused_criterion["verdict"]
    path = tmp_path / "selector_red_focused_iteration2.json"
    path.write_text(json.dumps(payload))
    return path


def run_focused(
    tmp_path: Path,
    focused: Path,
    *,
    agent_id: str = "agent:focused-reviewer",
    reviewer_source: str = "test.delegate",
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(GATE),
            "focused",
            "--eligibility",
            str(tmp_path / "eligibility.json"),
            "--role-receipt",
            str(tmp_path / "roles.json"),
            "--focused-audit",
            str(focused),
            "--focused-reviewer-agent-id",
            agent_id,
            "--reviewer-source",
            reviewer_source,
            "--output",
            str(tmp_path / "focused_gate.json"),
        ],
        text=True,
        capture_output=True,
        check=False,
    )


def replace_audit(path: Path, mutate: Any) -> None:
    payload = json.loads(path.read_text())
    mutate(payload)
    path.write_text(json.dumps(payload))


def test_unanimous_single_blocker_allows_one_independent_focused_pass(tmp_path: Path) -> None:
    receipt, audits = write_initial_set(tmp_path)

    initial = run_initial(tmp_path, receipt, audits)

    assert initial.returncode == 0, initial.stdout + initial.stderr
    eligibility = json.loads((tmp_path / "eligibility.json").read_text())
    assert eligibility == {
        "schema": 1,
        "decision": "focused_re_review",
        "feature": "selector",
        "route": "compact",
        "risk_tier": "low",
        "monitor_agent_id": "agent:monitor",
        "monitor_source": "test.delegate",
        "initial_reviewer_agent_ids": [
            "agent:initial-audit1",
            "agent:initial-audit2",
            "agent:initial-audit3",
        ],
        "reviewer_source": "test.delegate",
        "role_receipt_path": str(receipt.resolve()),
        "role_receipt_sha256": hashlib.sha256(receipt.read_bytes()).hexdigest(),
        "repaired_criterion": {
            "id": "repair",
            "text": "Criterion repair",
            "blocking": True,
        },
    }
    focused = write_focused(tmp_path, criterion("repair", "pass"))

    advanced = run_focused(tmp_path, focused)

    assert advanced.returncode == 0, advanced.stdout + advanced.stderr
    focused_gate = json.loads((tmp_path / "focused_gate.json").read_text())
    assert focused_gate["decision"] == "advance_green"
    assert focused_gate["feature"] == "selector"
    assert focused_gate["phase"] == "red"
    assert focused_gate["iteration"] == 2
    assert focused_gate["focused_reviewer_agent_id"] == "agent:focused-reviewer"
    assert focused_gate["reviewer_source"] == "test.delegate"
    assert focused_gate["focused_audit_path"] == str(focused.resolve())
    assert focused_gate["focused_audit_sha256"] == hashlib.sha256(focused.read_bytes()).hexdigest()
    assert focused_gate["role_receipt_path"] == str(receipt.resolve())
    assert focused_gate["role_receipt_sha256"] == hashlib.sha256(receipt.read_bytes()).hexdigest()
    eligibility = tmp_path / "eligibility.json"
    assert focused_gate["eligibility_path"] == str(eligibility.resolve())
    assert focused_gate["eligibility_sha256"] == hashlib.sha256(eligibility.read_bytes()).hexdigest()


def test_gate_accepts_backend_neutral_delegation_provenance(tmp_path: Path) -> None:
    receipt, audits = write_initial_set(tmp_path)
    receipt_payload = json.loads(receipt.read_text())
    receipt_payload.update(
        {
            "schema": 2,
            "monitor_agent_id": "workflow:monitor-17",
            "monitor_source": "workflow.delegate",
            "red_reviewer_agent_ids": [
                "mcp:reviewer-a",
                "mcp:reviewer-b",
                "mcp:reviewer-c",
            ],
            "reviewer_source": "multi_agent_v1.delegate",
        }
    )
    receipt.write_text(json.dumps(receipt_payload))
    for path, reviewer_agent_id in zip(
        audits,
        receipt_payload["red_reviewer_agent_ids"],
        strict=True,
    ):
        replace_audit(
            path,
            lambda payload, agent_id=reviewer_agent_id: payload.update(
                {
                    "reviewer_agent_id": agent_id,
                    "reviewer_source": "multi_agent_v1.delegate",
                }
            ),
        )

    initial = run_initial(tmp_path, receipt, audits)

    assert initial.returncode == 0, initial.stdout + initial.stderr
    focused = write_focused(tmp_path, criterion("repair", "pass"))
    replace_audit(
        focused,
        lambda payload: payload.update(
            {
                "reviewer_agent_id": "api:focused-reviewer",
                "reviewer_source": "agent_api.create_worker",
            }
        ),
    )
    advanced = run_focused(
        tmp_path,
        focused,
        agent_id="api:focused-reviewer",
        reviewer_source="agent_api.create_worker",
    )

    assert advanced.returncode == 0, advanced.stdout + advanced.stderr
    assert json.loads((tmp_path / "focused_gate.json").read_text())["decision"] == "advance_green"


def test_normal_red_provenance_gate_binds_receipt_to_owned_audit_bytes(tmp_path: Path) -> None:
    receipt, audits = write_initial_set(tmp_path)

    result = run_provenance(tmp_path, receipt, audits)

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads((tmp_path / "provenance.json").read_text())
    assert payload["decision"] == "provenance_valid"
    assert payload["feature"] == "selector"
    assert payload["phase"] == "red"
    assert payload["iteration"] == 1
    assert payload["role_receipt_sha256"] == hashlib.sha256(receipt.read_bytes()).hexdigest()
    assert payload["reviewers"] == [
        {
            "reviewer_id": f"audit{index}",
            "reviewer_agent_id": f"agent:initial-audit{index}",
            "reviewer_source": "test.delegate",
            "audit_path": str(path.resolve()),
            "audit_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        for index, path in enumerate(audits, start=1)
    ]


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("reviewer_agent_id", "agent:unassigned"),
        ("reviewer_source", "other.delegate"),
    ],
)
def test_normal_red_provenance_gate_rejects_unbound_audit_owner(
    tmp_path: Path,
    field: str,
    replacement: str,
) -> None:
    receipt, audits = write_initial_set(tmp_path)
    replace_audit(audits[1], lambda payload: payload.update({field: replacement}))

    result = run_provenance(tmp_path, receipt, audits)

    assert result.returncode != 0
    assert json.loads(result.stdout)["decision"] == "normal_three_reviewer_follow_up"
    assert not (tmp_path / "provenance.json").exists()


@pytest.mark.parametrize(
    ("route", "risk_tier"),
    [("full", "low"), ("compact", "medium"), ("compact", "high")],
)
def test_non_compact_or_non_low_risk_requires_normal_follow_up(
    tmp_path: Path, route: str, risk_tier: str
) -> None:
    receipt, audits = write_initial_set(tmp_path)

    result = run_initial(tmp_path, receipt, audits, route=route, risk_tier=risk_tier)

    assert result.returncode != 0
    assert json.loads(result.stdout)["decision"] == "normal_three_reviewer_follow_up"
    assert not (tmp_path / "eligibility.json").exists()


@pytest.mark.parametrize("audit_index", [0, 1, 2], ids=["audit1", "audit2", "audit3"])
@pytest.mark.parametrize(
    "mutation",
    [
        lambda payload: payload["criteria"].__setitem__(0, criterion("repair", "insufficient_evidence", evidence=[])),
        lambda payload: payload["criteria"][0].update(
            {"counterevidence": [{"kind": "test", "location": "counter.log"}]}
        ),
        lambda payload: payload.update({"open_questions": ["Is the failure real?"]}),
        lambda payload: payload.update({"disputed_points_if_any": ["repair: conflicting evidence"]}),
    ],
    ids=["insufficient", "counterevidence", "question", "dispute"],
)
def test_unresolved_or_broader_initial_review_requires_normal_follow_up(
    tmp_path: Path, mutation: Any, audit_index: int
) -> None:
    receipt, audits = write_initial_set(tmp_path)
    replace_audit(audits[audit_index], mutation)

    result = run_initial(tmp_path, receipt, audits)

    assert result.returncode != 0
    assert json.loads(result.stdout)["decision"] == "normal_three_reviewer_follow_up"
    assert not (tmp_path / "eligibility.json").exists()


@pytest.mark.parametrize("dissent_index", [0, 1, 2], ids=["audit1", "audit2", "audit3"])
def test_initial_review_rejects_coherent_dissent_in_every_position(
    tmp_path: Path, dissent_index: int
) -> None:
    receipt, audits = write_initial_set(tmp_path)
    replace_audit(
        audits[dissent_index],
        lambda payload: (
            payload["criteria"].__setitem__(0, criterion("repair", "pass")),
            payload.update({"overall_verdict": "pass"}),
        ),
    )

    result = run_initial(tmp_path, receipt, audits)

    assert result.returncode != 0
    assert json.loads(result.stdout)["decision"] == "normal_three_reviewer_follow_up"
    assert not (tmp_path / "eligibility.json").exists()


def test_initial_review_rejects_two_unanimous_blocking_failures(tmp_path: Path) -> None:
    receipt, audits = write_initial_set(tmp_path)
    for path in audits:
        replace_audit(
            path,
            lambda payload: payload["criteria"].append(criterion("second", "fail")),
        )

    result = run_initial(tmp_path, receipt, audits)

    assert result.returncode != 0
    assert json.loads(result.stdout)["decision"] == "normal_three_reviewer_follow_up"
    assert not (tmp_path / "eligibility.json").exists()


def test_initial_review_rejects_unanimous_nonblocking_failure(tmp_path: Path) -> None:
    receipt, audits = write_initial_set(tmp_path)
    for path in audits:
        replace_audit(
            path,
            lambda payload: payload["criteria"].append(
                criterion("nonblocking", "fail", blocking=False)
            ),
        )

    result = run_initial(tmp_path, receipt, audits)

    assert result.returncode != 0
    assert json.loads(result.stdout)["decision"] == "normal_three_reviewer_follow_up"
    assert not (tmp_path / "eligibility.json").exists()


@pytest.mark.parametrize("dissent_index", [0, 1, 2], ids=["audit1", "audit2", "audit3"])
def test_initial_review_rejects_swapped_failures_in_every_position(
    tmp_path: Path, dissent_index: int
) -> None:
    receipt, audits = write_initial_set(tmp_path)
    replace_audit(
        audits[dissent_index],
        lambda payload: payload.update(
            {
                "criteria": [
                    criterion("repair", "pass"),
                    criterion("stable", "fail", blocking=False),
                ],
                "overall_verdict": "fail",
            }
        ),
    )

    result = run_initial(tmp_path, receipt, audits)

    assert result.returncode != 0
    assert json.loads(result.stdout)["decision"] == "normal_three_reviewer_follow_up"
    assert not (tmp_path / "eligibility.json").exists()


@pytest.mark.parametrize("audit_index", [0, 1, 2], ids=["audit1", "audit2", "audit3"])
@pytest.mark.parametrize("uncertainty", ["insufficient_evidence", "counterevidence"])
def test_initial_review_rejects_uncertainty_on_stable_criterion(
    tmp_path: Path, uncertainty: str, audit_index: int
) -> None:
    receipt, audits = write_initial_set(tmp_path)
    if uncertainty == "insufficient_evidence":
        replace_audit(
            audits[audit_index],
            lambda payload: (
                payload["criteria"][1].update(
                    {"verdict": "insufficient_evidence", "evidence": []}
                ),
                payload.update({"overall_verdict": "insufficient_evidence"}),
            ),
        )
    else:
        replace_audit(
            audits[audit_index],
            lambda payload: payload["criteria"][1].update(
                {"counterevidence": [{"kind": "test", "location": "counter.log"}]}
            ),
        )

    result = run_initial(tmp_path, receipt, audits)

    assert result.returncode != 0
    assert json.loads(result.stdout)["decision"] == "normal_three_reviewer_follow_up"
    assert not (tmp_path / "eligibility.json").exists()


def test_initial_review_must_be_iteration_one(tmp_path: Path) -> None:
    receipt, audits = write_initial_set(tmp_path)
    replace_audit(audits[1], lambda payload: payload.update({"iteration": 2}))

    result = run_initial(tmp_path, receipt, audits)

    assert result.returncode != 0
    assert json.loads(result.stdout)["decision"] == "normal_three_reviewer_follow_up"
    assert not (tmp_path / "eligibility.json").exists()


@pytest.mark.parametrize("audit_count", [2, 4])
def test_initial_review_requires_exactly_three_audit_files(tmp_path: Path, audit_count: int) -> None:
    receipt, audits = write_initial_set(tmp_path)
    supplied = audits[:2] if audit_count == 2 else [*audits, audits[0]]

    result = run_initial(tmp_path, receipt, supplied)

    assert result.returncode != 0
    assert json.loads(result.stdout)["decision"] == "normal_three_reviewer_follow_up"


@pytest.mark.parametrize("reviewer_id", ["audit1", "unknown"])
def test_initial_review_rejects_duplicate_or_unknown_reviewer_slot(
    tmp_path: Path, reviewer_id: str
) -> None:
    receipt, audits = write_initial_set(tmp_path)
    replace_audit(audits[1], lambda payload: payload.update({"reviewer_id": reviewer_id}))

    result = run_initial(tmp_path, receipt, audits)

    assert result.returncode != 0
    assert json.loads(result.stdout)["decision"] == "normal_three_reviewer_follow_up"


def test_initial_review_rejects_wrong_audit_filename(tmp_path: Path) -> None:
    receipt, audits = write_initial_set(tmp_path)
    wrong_name = tmp_path / "wrong_name.json"
    audits[1].rename(wrong_name)
    audits[1] = wrong_name

    result = run_initial(tmp_path, receipt, audits)

    assert result.returncode != 0
    assert json.loads(result.stdout)["decision"] == "normal_three_reviewer_follow_up"


@pytest.mark.parametrize(
    "metadata",
    [{"feature_name": "different"}, {"phase": "green"}],
    ids=["feature", "phase"],
)
def test_initial_review_rejects_wrong_feature_or_phase(
    tmp_path: Path, metadata: dict[str, str]
) -> None:
    receipt, audits = write_initial_set(tmp_path)
    replace_audit(audits[1], lambda payload: payload.update(metadata))

    result = run_initial(tmp_path, receipt, audits)

    assert result.returncode != 0
    assert json.loads(result.stdout)["decision"] == "normal_three_reviewer_follow_up"


@pytest.mark.parametrize(
    "metadata",
    [
        {"feature_name": "uniformly-wrong"},
        {"phase": "green"},
        {"iteration": 2},
    ],
    ids=["feature", "phase", "iteration"],
)
def test_initial_review_rejects_uniformly_wrong_metadata(
    tmp_path: Path, metadata: dict[str, Any]
) -> None:
    receipt, audits = write_initial_set(tmp_path)
    for path in audits:
        replace_audit(path, lambda payload: payload.update(metadata))

    result = run_initial(tmp_path, receipt, audits)

    assert result.returncode != 0
    assert json.loads(result.stdout)["decision"] == "normal_three_reviewer_follow_up"
    assert not (tmp_path / "eligibility.json").exists()


@pytest.mark.parametrize(
    "mutation",
    [
        lambda payload: payload["criteria"][0].update({"id": "different"}),
        lambda payload: payload["criteria"][0].update({"text": "Different criterion"}),
        lambda payload: payload["criteria"][0].update({"blocking": False}),
        lambda payload: payload.update({"overall_verdict": "pass"}),
        lambda payload: payload["criteria"].append(criterion("nonblocking", "fail", blocking=False)),
    ],
    ids=["criterion-id", "criterion-text", "blocking-flag", "overall-verdict", "nonblocking-failure"],
)
def test_initial_review_rejects_criterion_drift_or_inconsistent_verdict(
    tmp_path: Path, mutation: Any
) -> None:
    receipt, audits = write_initial_set(tmp_path)
    replace_audit(audits[1], mutation)

    result = run_initial(tmp_path, receipt, audits)

    assert result.returncode != 0
    assert json.loads(result.stdout)["decision"] == "normal_three_reviewer_follow_up"


@pytest.mark.parametrize(
    "mutation",
    [
        lambda payload: payload["criteria"][1].update({"id": "different-stable"}),
        lambda payload: payload["criteria"][1].update({"text": "Different stable criterion"}),
        lambda payload: payload["criteria"][1].update({"blocking": True}),
        lambda payload: payload["criteria"].pop(1),
        lambda payload: payload["criteria"].append(criterion("new-pass", "pass", blocking=False)),
    ],
    ids=["id", "text", "blocking", "removed", "added"],
)
def test_initial_review_rejects_changed_or_new_passing_criterion(
    tmp_path: Path, mutation: Any
) -> None:
    receipt, audits = write_initial_set(tmp_path)
    replace_audit(audits[1], mutation)

    result = run_initial(tmp_path, receipt, audits)

    assert result.returncode != 0
    assert json.loads(result.stdout)["decision"] == "normal_three_reviewer_follow_up"


@pytest.mark.parametrize(
    "receipt_case",
    [
        "invalid-json",
        "missing-schema",
        "wrong-schema",
        "invalid-schema-type",
        "missing-feature",
        "wrong-feature",
        "invalid-feature-type",
        "missing-route",
        "route-mismatch",
        "invalid-route-type",
        "missing-monitor-id",
        "invalid-monitor-id",
        "invalid-monitor-id-type",
        "monitor-owner-collision",
        "missing-monitor-source",
        "wrong-monitor-source",
        "invalid-monitor-source-type",
        "missing-owner",
        "duplicate-owner",
        "invalid-owners-type",
        "invalid-owner-item-type",
        "swapped-slot-owners",
        "missing-reviewer-source",
        "wrong-reviewer-source",
        "invalid-reviewer-source-type",
    ],
)
def test_invalid_initial_reviewer_ownership_requires_normal_follow_up(
    tmp_path: Path, receipt_case: str
) -> None:
    receipt, audits = write_initial_set(tmp_path)
    if receipt_case == "invalid-json":
        receipt.write_text("{")
    else:
        payload = json.loads(receipt.read_text())
        if receipt_case == "missing-schema":
            payload.pop("schema")
        elif receipt_case == "wrong-schema":
            payload["schema"] = 1
        elif receipt_case == "invalid-schema-type":
            payload["schema"] = "1"
        elif receipt_case == "missing-feature":
            payload.pop("feature")
        elif receipt_case == "wrong-feature":
            payload["feature"] = "other"
        elif receipt_case == "invalid-feature-type":
            payload["feature"] = 1
        elif receipt_case == "missing-route":
            payload.pop("route")
        elif receipt_case == "route-mismatch":
            payload["route"] = "full"
        elif receipt_case == "invalid-route-type":
            payload["route"] = 1
        elif receipt_case == "missing-monitor-id":
            payload.pop("monitor_agent_id")
        elif receipt_case == "invalid-monitor-id":
            payload["monitor_agent_id"] = ""
        elif receipt_case == "invalid-monitor-id-type":
            payload["monitor_agent_id"] = 1
        elif receipt_case == "monitor-owner-collision":
            payload["monitor_agent_id"] = "agent:initial-audit1"
        elif receipt_case == "missing-monitor-source":
            payload.pop("monitor_source")
        elif receipt_case == "wrong-monitor-source":
            payload["monitor_source"] = ""
        elif receipt_case == "invalid-monitor-source-type":
            payload["monitor_source"] = 1
        elif receipt_case == "missing-owner":
            payload["red_reviewer_agent_ids"] = [
                "agent:initial-audit1",
                "agent:initial-audit2",
            ]
        elif receipt_case == "duplicate-owner":
            payload["red_reviewer_agent_ids"] = [
                "agent:reviewer",
                "agent:reviewer",
                "agent:reviewer",
            ]
        elif receipt_case == "invalid-owners-type":
            payload["red_reviewer_agent_ids"] = "agent:reviewer"
        elif receipt_case == "invalid-owner-item-type":
            payload["red_reviewer_agent_ids"] = [
                "agent:initial-audit1",
                2,
                "agent:initial-audit3",
            ]
        elif receipt_case == "swapped-slot-owners":
            payload["red_reviewer_agent_ids"] = [
                "agent:initial-audit2",
                "agent:initial-audit1",
                "agent:initial-audit3",
            ]
        elif receipt_case == "missing-reviewer-source":
            payload.pop("reviewer_source")
        elif receipt_case == "invalid-reviewer-source-type":
            payload["reviewer_source"] = 1
        else:
            payload["reviewer_source"] = "other.delegate"
        receipt.write_text(json.dumps(payload))

    result = run_initial(tmp_path, receipt, audits)

    assert result.returncode != 0
    assert json.loads(result.stdout)["decision"] == "normal_three_reviewer_follow_up"
    assert not (tmp_path / "eligibility.json").exists()


@pytest.mark.parametrize("audit_index", [0, 1, 2], ids=["audit1", "audit2", "audit3"])
@pytest.mark.parametrize(
    "malformation",
    [
        "invalid-json",
        "missing-top-level-field",
        "missing-reviewer-agent-id",
        "wrong-reviewer-agent-id",
        "missing-reviewer-source",
        "wrong-reviewer-source",
        "missing-criterion-field",
    ],
)
def test_initial_review_requires_valid_reviewer_owned_json_in_every_position(
    tmp_path: Path, audit_index: int, malformation: str
) -> None:
    receipt, audits = write_initial_set(tmp_path)
    path = audits[audit_index]
    if malformation == "invalid-json":
        path.write_text("{")
    else:
        payload = json.loads(path.read_text())
        if malformation == "missing-top-level-field":
            payload.pop("claim")
        elif malformation == "missing-reviewer-agent-id":
            payload.pop("reviewer_agent_id")
        elif malformation == "wrong-reviewer-agent-id":
            payload["reviewer_agent_id"] = "agent:unassigned-reviewer"
        elif malformation == "missing-reviewer-source":
            payload.pop("reviewer_source")
        elif malformation == "wrong-reviewer-source":
            payload["reviewer_source"] = "other.delegate"
        else:
            payload["criteria"][0].pop("reasoning")
        path.write_text(json.dumps(payload))

    result = run_initial(tmp_path, receipt, audits)

    assert result.returncode != 0
    assert json.loads(result.stdout)["decision"] == "normal_three_reviewer_follow_up"
    assert not (tmp_path / "eligibility.json").exists()


@pytest.mark.parametrize("audit_index", [0, 1, 2], ids=["audit1", "audit2", "audit3"])
@pytest.mark.parametrize("criterion_index", [0, 1], ids=["repair", "stable"])
@pytest.mark.parametrize(
    "invalid_evidence",
    [[], [{}], [{"kind": "test"}]],
    ids=["empty-list", "empty-item", "missing-location"],
)
def test_initial_review_rejects_known_malformed_evidence_on_both_criteria(
    tmp_path: Path,
    audit_index: int,
    criterion_index: int,
    invalid_evidence: list[dict[str, str]],
) -> None:
    receipt, audits = write_initial_set(tmp_path)
    replace_audit(
        audits[audit_index],
        lambda payload: payload["criteria"][criterion_index].update(
            {"evidence": invalid_evidence}
        ),
    )

    result = run_initial(tmp_path, receipt, audits)

    assert result.returncode != 0
    assert json.loads(result.stdout)["decision"] == "normal_three_reviewer_follow_up"
    assert not (tmp_path / "eligibility.json").exists()


@pytest.mark.parametrize("audit_index", [0, 1, 2], ids=["audit1", "audit2", "audit3"])
@pytest.mark.parametrize("field", AUDIT_REQUIRED_TOP_LEVEL_FIELDS)
def test_initial_review_rejects_every_missing_top_level_field(
    tmp_path: Path, audit_index: int, field: str
) -> None:
    receipt, audits = write_initial_set(tmp_path)
    replace_audit(audits[audit_index], lambda payload: payload.pop(field))

    result = run_initial(tmp_path, receipt, audits)

    assert result.returncode != 0
    assert json.loads(result.stdout)["decision"] == "normal_three_reviewer_follow_up"
    assert not (tmp_path / "eligibility.json").exists()


@pytest.mark.parametrize("audit_index", [0, 1, 2], ids=["audit1", "audit2", "audit3"])
@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("feature_name", 1),
        ("phase", 1),
        ("iteration", "1"),
        ("reviewer_id", 1),
        ("reviewer_agent_id", 1),
        ("reviewer_source", 1),
        ("claim", 1),
        ("overall_verdict", "unknown"),
        ("overall_confidence", "high"),
        ("overall_confidence", 1.1),
        ("criteria", {}),
        ("open_questions", "none"),
        ("disputed_points_if_any", "none"),
    ],
)
def test_initial_review_rejects_invalid_top_level_field_types_or_values(
    tmp_path: Path, audit_index: int, field: str, invalid_value: Any
) -> None:
    receipt, audits = write_initial_set(tmp_path)
    replace_audit(
        audits[audit_index],
        lambda payload: payload.update({field: invalid_value}),
    )

    result = run_initial(tmp_path, receipt, audits)

    assert result.returncode != 0
    assert json.loads(result.stdout)["decision"] == "normal_three_reviewer_follow_up"
    assert not (tmp_path / "eligibility.json").exists()


@pytest.mark.parametrize("audit_index", [0, 1, 2], ids=["audit1", "audit2", "audit3"])
@pytest.mark.parametrize("criterion_index", [0, 1], ids=["repair", "stable"])
@pytest.mark.parametrize("field", CRITERION_REQUIRED_FIELDS)
def test_initial_review_rejects_every_missing_criterion_field(
    tmp_path: Path, audit_index: int, criterion_index: int, field: str
) -> None:
    receipt, audits = write_initial_set(tmp_path)
    replace_audit(
        audits[audit_index],
        lambda payload: payload["criteria"][criterion_index].pop(field),
    )

    result = run_initial(tmp_path, receipt, audits)

    assert result.returncode != 0
    assert json.loads(result.stdout)["decision"] == "normal_three_reviewer_follow_up"
    assert not (tmp_path / "eligibility.json").exists()


@pytest.mark.parametrize("audit_index", [0, 1, 2], ids=["audit1", "audit2", "audit3"])
@pytest.mark.parametrize("criterion_index", [0, 1], ids=["repair", "stable"])
@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("id", 1),
        ("text", 1),
        ("blocking", "true"),
        ("verdict", "unknown"),
        ("confidence", "high"),
        ("confidence", 1.1),
        ("evidence", {}),
        ("reasoning", ""),
        ("counterevidence", {}),
    ],
)
def test_initial_review_rejects_invalid_criterion_field_types_or_values(
    tmp_path: Path,
    audit_index: int,
    criterion_index: int,
    field: str,
    invalid_value: Any,
) -> None:
    receipt, audits = write_initial_set(tmp_path)
    replace_audit(
        audits[audit_index],
        lambda payload: payload["criteria"][criterion_index].update({field: invalid_value}),
    )

    result = run_initial(tmp_path, receipt, audits)

    assert result.returncode != 0
    assert json.loads(result.stdout)["decision"] == "normal_three_reviewer_follow_up"
    assert not (tmp_path / "eligibility.json").exists()


@pytest.mark.parametrize("audit_index", [0, 1, 2], ids=["audit1", "audit2", "audit3"])
@pytest.mark.parametrize("criterion_index", [0, 1], ids=["repair", "stable"])
@pytest.mark.parametrize(
    "invalid_evidence",
    [
        [{"location": "red.log"}],
        [{"kind": "", "location": "red.log"}],
        [{"kind": "test", "location": ""}],
        [{"kind": 1, "location": "red.log"}],
        [{"kind": "test", "location": 1}],
    ],
)
def test_initial_review_rejects_invalid_evidence_citations_in_every_position(
    tmp_path: Path,
    audit_index: int,
    criterion_index: int,
    invalid_evidence: list[dict[str, Any]],
) -> None:
    receipt, audits = write_initial_set(tmp_path)
    replace_audit(
        audits[audit_index],
        lambda payload: payload["criteria"][criterion_index].update({"evidence": invalid_evidence}),
    )

    result = run_initial(tmp_path, receipt, audits)

    assert result.returncode != 0
    assert json.loads(result.stdout)["decision"] == "normal_three_reviewer_follow_up"
    assert not (tmp_path / "eligibility.json").exists()


@pytest.mark.parametrize(
    "eligibility_case",
    [
        "absent",
        "invalid-json",
        "wrong-schema",
        "wrong-decision",
        "wrong-feature",
        "wrong-route",
        "wrong-risk-tier",
        "invalid-monitor-id",
        "replacement-monitor-id",
        "monitor-owner-collision",
        "wrong-monitor-source",
        "missing-initial-owner",
        "duplicate-initial-owner",
        "replacement-initial-owner",
        "wrong-reviewer-source",
        "invalid-repaired-criterion",
        "wrong-receipt-path",
        "wrong-receipt-hash",
        "mutated-source-receipt",
    ],
)
def test_focused_review_rejects_invalid_eligibility_state(
    tmp_path: Path, eligibility_case: str
) -> None:
    receipt, audits = write_initial_set(tmp_path)
    assert run_initial(tmp_path, receipt, audits).returncode == 0
    eligibility_path = tmp_path / "eligibility.json"
    if eligibility_case == "absent":
        eligibility_path.unlink()
    elif eligibility_case == "invalid-json":
        eligibility_path.write_text("{")
    else:
        payload = json.loads(eligibility_path.read_text())
        if eligibility_case == "wrong-schema":
            payload["schema"] = 2
        elif eligibility_case == "wrong-decision":
            payload["decision"] = "normal_three_reviewer_follow_up"
        elif eligibility_case == "wrong-feature":
            payload["feature"] = "other"
        elif eligibility_case == "wrong-route":
            payload["route"] = "full"
        elif eligibility_case == "wrong-risk-tier":
            payload["risk_tier"] = "high"
        elif eligibility_case == "invalid-monitor-id":
            payload["monitor_agent_id"] = "monitor"
        elif eligibility_case == "replacement-monitor-id":
            payload["monitor_agent_id"] = "agent:replacement-monitor"
        elif eligibility_case == "monitor-owner-collision":
            payload["monitor_agent_id"] = "agent:initial-audit1"
        elif eligibility_case == "wrong-monitor-source":
            payload["monitor_source"] = "main_agent"
        elif eligibility_case == "missing-initial-owner":
            payload["initial_reviewer_agent_ids"] = payload["initial_reviewer_agent_ids"][:2]
        elif eligibility_case == "duplicate-initial-owner":
            payload["initial_reviewer_agent_ids"] = ["agent:reviewer"] * 3
        elif eligibility_case == "replacement-initial-owner":
            payload["initial_reviewer_agent_ids"][1] = "agent:replacement-reviewer"
        elif eligibility_case == "wrong-reviewer-source":
            payload["reviewer_source"] = "main_agent"
        elif eligibility_case == "invalid-repaired-criterion":
            payload["repaired_criterion"] = {"id": "repair"}
        elif eligibility_case == "wrong-receipt-path":
            payload["role_receipt_path"] = str((tmp_path / "other-roles.json").resolve())
        elif eligibility_case == "wrong-receipt-hash":
            payload["role_receipt_sha256"] = "0" * 64
        else:
            receipt.write_text(json.dumps({"schema": 1}))
        eligibility_path.write_text(json.dumps(payload))
    focused = write_focused(tmp_path, criterion("repair", "pass"))

    result = run_focused(tmp_path, focused)

    assert result.returncode != 0
    assert json.loads(result.stdout)["decision"] == "normal_three_reviewer_follow_up"
    assert not (tmp_path / "focused_gate.json").exists()


@pytest.mark.parametrize(
    "field",
    [
        "schema",
        "decision",
        "feature",
        "route",
        "risk_tier",
        "monitor_agent_id",
        "monitor_source",
        "initial_reviewer_agent_ids",
        "reviewer_source",
        "role_receipt_path",
        "role_receipt_sha256",
        "repaired_criterion",
    ],
)
def test_focused_review_rejects_incomplete_eligibility_state(
    tmp_path: Path, field: str
) -> None:
    receipt, audits = write_initial_set(tmp_path)
    assert run_initial(tmp_path, receipt, audits).returncode == 0
    eligibility_path = tmp_path / "eligibility.json"
    payload = json.loads(eligibility_path.read_text())
    payload.pop(field)
    eligibility_path.write_text(json.dumps(payload))
    focused = write_focused(tmp_path, criterion("repair", "pass"))

    result = run_focused(tmp_path, focused)

    assert result.returncode != 0
    assert json.loads(result.stdout)["decision"] == "normal_three_reviewer_follow_up"
    assert not (tmp_path / "focused_gate.json").exists()


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("schema", "1"),
        ("decision", 1),
        ("feature", 1),
        ("route", 1),
        ("risk_tier", 1),
        ("monitor_agent_id", 1),
        ("monitor_source", 1),
        ("initial_reviewer_agent_ids", "agent:reviewer"),
        ("initial_reviewer_agent_ids", ["agent:initial-audit1", 2, "agent:initial-audit3"]),
        ("reviewer_source", 1),
        ("role_receipt_path", 1),
        ("role_receipt_sha256", 1),
        ("repaired_criterion", []),
    ],
)
def test_focused_review_rejects_invalid_eligibility_field_types(
    tmp_path: Path, field: str, invalid_value: Any
) -> None:
    receipt, audits = write_initial_set(tmp_path)
    assert run_initial(tmp_path, receipt, audits).returncode == 0
    eligibility_path = tmp_path / "eligibility.json"
    payload = json.loads(eligibility_path.read_text())
    payload[field] = invalid_value
    eligibility_path.write_text(json.dumps(payload))
    focused = write_focused(tmp_path, criterion("repair", "pass"))

    result = run_focused(tmp_path, focused)

    assert result.returncode != 0
    assert json.loads(result.stdout)["decision"] == "normal_three_reviewer_follow_up"
    assert not (tmp_path / "focused_gate.json").exists()


@pytest.mark.parametrize("field", AUDIT_REQUIRED_TOP_LEVEL_FIELDS)
def test_focused_review_rejects_every_missing_top_level_field(
    tmp_path: Path, field: str
) -> None:
    receipt, audits = write_initial_set(tmp_path)
    assert run_initial(tmp_path, receipt, audits).returncode == 0
    focused = write_focused(tmp_path, criterion("repair", "pass"))
    replace_audit(focused, lambda payload: payload.pop(field))

    result = run_focused(tmp_path, focused)

    assert result.returncode != 0
    assert json.loads(result.stdout)["decision"] == "normal_three_reviewer_follow_up"
    assert not (tmp_path / "focused_gate.json").exists()


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("feature_name", 1),
        ("phase", 1),
        ("iteration", "2"),
        ("reviewer_id", 1),
        ("reviewer_agent_id", 1),
        ("reviewer_source", 1),
        ("claim", 1),
        ("overall_verdict", "unknown"),
        ("overall_confidence", "high"),
        ("overall_confidence", 1.1),
        ("criteria", {}),
        ("open_questions", "none"),
        ("disputed_points_if_any", "none"),
    ],
)
def test_focused_review_rejects_invalid_top_level_field_types_or_values(
    tmp_path: Path, field: str, invalid_value: Any
) -> None:
    receipt, audits = write_initial_set(tmp_path)
    assert run_initial(tmp_path, receipt, audits).returncode == 0
    focused = write_focused(tmp_path, criterion("repair", "pass"))
    replace_audit(focused, lambda payload: payload.update({field: invalid_value}))

    result = run_focused(tmp_path, focused)

    assert result.returncode != 0
    assert json.loads(result.stdout)["decision"] == "normal_three_reviewer_follow_up"
    assert not (tmp_path / "focused_gate.json").exists()


@pytest.mark.parametrize("field", CRITERION_REQUIRED_FIELDS)
def test_focused_review_rejects_every_missing_criterion_field(
    tmp_path: Path, field: str
) -> None:
    receipt, audits = write_initial_set(tmp_path)
    assert run_initial(tmp_path, receipt, audits).returncode == 0
    focused = write_focused(tmp_path, criterion("repair", "pass"))
    replace_audit(
        focused,
        lambda payload: payload["criteria"][0].pop(field),
    )

    result = run_focused(tmp_path, focused)

    assert result.returncode != 0
    assert json.loads(result.stdout)["decision"] == "normal_three_reviewer_follow_up"
    assert not (tmp_path / "focused_gate.json").exists()


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("id", 1),
        ("text", 1),
        ("blocking", "true"),
        ("verdict", "unknown"),
        ("confidence", "high"),
        ("confidence", 1.1),
        ("evidence", {}),
        ("reasoning", ""),
        ("counterevidence", {}),
    ],
)
def test_focused_review_rejects_invalid_criterion_field_types_or_values(
    tmp_path: Path, field: str, invalid_value: Any
) -> None:
    receipt, audits = write_initial_set(tmp_path)
    assert run_initial(tmp_path, receipt, audits).returncode == 0
    focused = write_focused(tmp_path, criterion("repair", "pass"))
    replace_audit(
        focused,
        lambda payload: payload["criteria"][0].update({field: invalid_value}),
    )

    result = run_focused(tmp_path, focused)

    assert result.returncode != 0
    assert json.loads(result.stdout)["decision"] == "normal_three_reviewer_follow_up"
    assert not (tmp_path / "focused_gate.json").exists()


def test_focused_review_rejects_invalid_json(tmp_path: Path) -> None:
    receipt, audits = write_initial_set(tmp_path)
    assert run_initial(tmp_path, receipt, audits).returncode == 0
    focused = write_focused(tmp_path, criterion("repair", "pass"))
    focused.write_text("{")

    result = run_focused(tmp_path, focused)

    assert result.returncode != 0
    assert json.loads(result.stdout)["decision"] == "normal_three_reviewer_follow_up"
    assert not (tmp_path / "focused_gate.json").exists()


def test_focused_review_rejects_feature_mismatch_with_eligibility(tmp_path: Path) -> None:
    receipt, audits = write_initial_set(tmp_path)
    assert run_initial(tmp_path, receipt, audits).returncode == 0
    focused = write_focused(tmp_path, criterion("repair", "pass"))
    replace_audit(focused, lambda payload: payload.update({"feature_name": "other"}))

    result = run_focused(tmp_path, focused)

    assert result.returncode != 0
    assert json.loads(result.stdout)["decision"] == "normal_three_reviewer_follow_up"
    assert not (tmp_path / "focused_gate.json").exists()


@pytest.mark.parametrize(
    "criterion_mutation",
    [
        lambda item: item.update({"id": "new"}),
        lambda item: item.update({"text": "Changed criterion"}),
        lambda item: item.update({"blocking": False}),
        lambda item: item.update({"verdict": "fail"}),
        lambda item: item.update({"verdict": "insufficient_evidence", "evidence": []}),
        lambda item: item.update({"evidence": []}),
        lambda item: item.update({"evidence": [{}]}),
        lambda item: item.update({"evidence": [{"kind": "test"}]}),
        lambda item: item.update({"evidence": [{"location": "red.log"}]}),
        lambda item: item.update({"evidence": ["red.log"]}),
        lambda item: item.update({"evidence": [{"kind": "", "location": "red.log"}]}),
        lambda item: item.update({"evidence": [{"kind": "test", "location": ""}]}),
        lambda item: item.update({"evidence": [{"kind": 1, "location": "red.log"}]}),
        lambda item: item.update({"evidence": [{"kind": "test", "location": 1}]}),
        lambda item: item.update({"counterevidence": [{"kind": "test", "location": "counter.log"}]}),
    ],
    ids=[
        "new-id",
        "changed-text",
        "changed-blocking",
        "fail",
        "insufficient",
        "no-evidence",
        "empty-evidence-item",
        "citation-without-location",
        "citation-without-kind",
        "non-object-evidence-item",
        "empty-kind",
        "empty-location",
        "non-string-kind",
        "non-string-location",
        "counterevidence",
    ],
)
def test_focused_review_must_pass_only_the_frozen_repaired_criterion(
    tmp_path: Path, criterion_mutation: Any
) -> None:
    receipt, audits = write_initial_set(tmp_path)
    assert run_initial(tmp_path, receipt, audits).returncode == 0
    repaired = criterion("repair", "pass")
    criterion_mutation(repaired)
    focused = write_focused(tmp_path, repaired)

    result = run_focused(tmp_path, focused)

    assert result.returncode != 0
    assert json.loads(result.stdout)["decision"] == "normal_three_reviewer_follow_up"


def test_focused_review_rejects_extra_criterion_unresolved_fields_and_reused_identity(
    tmp_path: Path,
) -> None:
    receipt, audits = write_initial_set(tmp_path)
    assert run_initial(tmp_path, receipt, audits).returncode == 0
    focused = write_focused(tmp_path, criterion("repair", "pass"))
    replace_audit(focused, lambda payload: payload["criteria"].append(criterion("new", "pass")))
    result = run_focused(tmp_path, focused)
    assert result.returncode != 0
    assert json.loads(result.stdout)["decision"] == "normal_three_reviewer_follow_up"
    assert not (tmp_path / "focused_gate.json").exists()

    focused = write_focused(tmp_path, criterion("repair", "pass"))
    replace_audit(focused, lambda payload: payload.update({"open_questions": ["Still open"]}))
    result = run_focused(tmp_path, focused)
    assert result.returncode != 0
    assert json.loads(result.stdout)["decision"] == "normal_three_reviewer_follow_up"
    assert not (tmp_path / "focused_gate.json").exists()

    focused = write_focused(tmp_path, criterion("repair", "pass"))
    replace_audit(focused, lambda payload: payload.update({"disputed_points_if_any": ["Still disputed"]}))
    result = run_focused(tmp_path, focused)
    assert result.returncode != 0
    assert json.loads(result.stdout)["decision"] == "normal_three_reviewer_follow_up"
    assert not (tmp_path / "focused_gate.json").exists()



@pytest.mark.parametrize(
    "initial_reviewer_id",
    ["agent:initial-audit1", "agent:initial-audit2", "agent:initial-audit3"],
    ids=["audit1", "audit2", "audit3"],
)
def test_focused_review_rejects_reuse_of_every_initial_reviewer(
    tmp_path: Path, initial_reviewer_id: str
) -> None:
    receipt, audits = write_initial_set(tmp_path)
    assert run_initial(tmp_path, receipt, audits).returncode == 0
    focused = write_focused(tmp_path, criterion("repair", "pass"))

    reused = run_focused(tmp_path, focused, agent_id=initial_reviewer_id)

    assert reused.returncode != 0
    assert json.loads(reused.stdout)["decision"] == "normal_three_reviewer_follow_up"


@pytest.mark.parametrize(
    ("payload_update", "agent_id", "reviewer_source"),
    [
        ({"iteration": 1}, "agent:focused-reviewer", "test.delegate"),
        ({"phase": "green"}, "agent:focused-reviewer", "test.delegate"),
        ({"reviewer_id": "audit1"}, "agent:focused-reviewer", "test.delegate"),
        ({"reviewer_agent_id": "agent:other"}, "agent:focused-reviewer", "test.delegate"),
        ({"reviewer_source": "other.delegate"}, "agent:focused-reviewer", "test.delegate"),
        ({}, "agent:focused-reviewer", "other.delegate"),
        ({}, "agent:monitor", "test.delegate"),
    ],
    ids=[
        "iteration",
        "phase",
        "reviewer-id",
        "audit-agent-id",
        "audit-source",
        "cli-source",
        "monitor-reuse",
    ],
)
def test_focused_review_rejects_invalid_metadata_or_provenance(
    tmp_path: Path,
    payload_update: dict[str, Any],
    agent_id: str,
    reviewer_source: str,
) -> None:
    receipt, audits = write_initial_set(tmp_path)
    assert run_initial(tmp_path, receipt, audits).returncode == 0
    focused = write_focused(tmp_path, criterion("repair", "pass"))
    replace_audit(focused, lambda payload: payload.update(payload_update))

    result = run_focused(
        tmp_path,
        focused,
        agent_id=agent_id,
        reviewer_source=reviewer_source,
    )

    assert result.returncode != 0
    assert json.loads(result.stdout)["decision"] == "normal_three_reviewer_follow_up"


@pytest.mark.parametrize("overall_verdict", ["fail", "insufficient_evidence"])
def test_focused_review_rejects_overall_verdict_that_contradicts_pass(
    tmp_path: Path, overall_verdict: str
) -> None:
    receipt, audits = write_initial_set(tmp_path)
    assert run_initial(tmp_path, receipt, audits).returncode == 0
    focused = write_focused(tmp_path, criterion("repair", "pass"))
    replace_audit(
        focused,
        lambda payload: payload.update({"overall_verdict": overall_verdict}),
    )

    result = run_focused(tmp_path, focused)

    assert result.returncode != 0
    assert json.loads(result.stdout)["decision"] == "normal_three_reviewer_follow_up"


def test_focused_review_does_not_mutate_eligibility_input(tmp_path: Path) -> None:
    receipt, audits = write_initial_set(tmp_path)
    assert run_initial(tmp_path, receipt, audits).returncode == 0
    before = deepcopy(json.loads((tmp_path / "eligibility.json").read_text()))
    focused = write_focused(tmp_path, criterion("repair", "pass"))

    assert run_focused(tmp_path, focused).returncode == 0

    assert json.loads((tmp_path / "eligibility.json").read_text()) == before
