"""Responsible for review-with-multi-debate/scripts/aggregate_audits.py convergence decisions."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "aggregate_audits.py"


def load_module():
    spec = importlib.util.spec_from_file_location("aggregate_audits", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def write_audit(path: Path, reviewer_id: str, criterion_verdict: str, confidence: float) -> None:
    path.write_text(
        json.dumps(
            {
                "feature_name": "login-flow",
                "phase": "green",
                "iteration": 1,
                "reviewer_id": reviewer_id,
                "claim": "The artifact satisfies the login-flow claim.",
                "overall_verdict": criterion_verdict,
                "overall_confidence": confidence,
                "criteria": [
                    {
                        "id": "c1",
                        "text": "Artifact includes login validation.",
                        "verdict": criterion_verdict,
                        "confidence": confidence,
                        "evidence": [
                            {
                                "kind": "quote",
                                "location": "artifact:12",
                                "text": "login validation exists",
                            }
                        ],
                        "reasoning": "Matched directly.",
                        "counterevidence": [],
                    }
                ],
                "open_questions": [],
            },
            indent=2,
        )
    )


def test_reviewer_specific_criteria_are_rejected(tmp_path: Path) -> None:
    write_audit(tmp_path / "audit1.json", "audit1", "pass", 0.92)
    write_audit(tmp_path / "audit2.json", "audit2", "pass", 0.88)
    write_audit(tmp_path / "audit3.json", "audit3", "pass", 0.90)
    payload = json.loads((tmp_path / "audit3.json").read_text())
    payload["criteria"][0]["id"] = "scope"
    (tmp_path / "audit3.json").write_text(json.dumps(payload))

    module = load_module()
    summary = module.aggregate_audits(
        [tmp_path / "audit1.json", tmp_path / "audit2.json", tmp_path / "audit3.json"]
    )

    assert summary["status"] == "invalid_contract"
    assert "criterion_ids_mismatch:audit3" in summary["contract_errors"]


def test_manifest_definition_is_authoritative(tmp_path: Path) -> None:
    for reviewer_id in ("audit1", "audit2", "audit3"):
        write_audit(tmp_path / f"{reviewer_id}.json", reviewer_id, "pass", 0.9)
    manifest = tmp_path / "criteria.json"
    manifest.write_text(
        json.dumps(
            {"criteria": [{"id": "c1", "text": "Different text", "blocking": False}]}
        )
    )

    module = load_module()
    summary = module.aggregate_audits(
        [tmp_path / f"{reviewer_id}.json" for reviewer_id in ("audit1", "audit2", "audit3")],
        criteria_manifest=manifest,
    )

    assert summary["status"] == "invalid_contract"
    assert "criteria_manifest_definition_mismatch:audit1:c1" in summary["contract_errors"]


def test_identical_reviews_converge(tmp_path: Path) -> None:
    write_audit(tmp_path / "audit1.json", "audit1", "pass", 0.92)
    write_audit(tmp_path / "audit2.json", "audit2", "pass", 0.88)
    write_audit(tmp_path / "audit3.json", "audit3", "pass", 0.90)

    module = load_module()
    summary = module.aggregate_audits(
        [
            tmp_path / "audit1.json",
            tmp_path / "audit2.json",
            tmp_path / "audit3.json",
        ]
    )

    assert summary["status"] == "converged"
    assert summary["disputed_criteria"] == []
    assert summary["criteria"]["c1"]["converged"] is True


def test_mixed_verdicts_are_marked_disputed(tmp_path: Path) -> None:
    write_audit(tmp_path / "audit1.json", "audit1", "pass", 0.92)
    write_audit(tmp_path / "audit2.json", "audit2", "fail", 0.88)
    write_audit(tmp_path / "audit3.json", "audit3", "pass", 0.90)

    module = load_module()
    summary = module.aggregate_audits(
        [
            tmp_path / "audit1.json",
            tmp_path / "audit2.json",
            tmp_path / "audit3.json",
        ]
    )

    assert summary["status"] == "not_converged"
    assert summary["disputed_criteria"] == ["c1"]
    assert summary["criteria"]["c1"]["final_verdict"] == "disputed"
