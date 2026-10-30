#!/usr/bin/env python3
# Responsible for rejecting a missing persisted reviewer result at the audit handoff boundary.
"""Exercise the first coarse validator transition through its CLI."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_audit_transition.py"


def write_audit(
    audit_dir: Path, reviewer_id: str, verdict: str = "pass", phase: str = "green"
) -> None:
    payload = {
        "feature_name": "login_flow",
        "phase": "green",
        "iteration": 1,
        "reviewer_id": reviewer_id,
        "claim": "The artifact satisfies the login-flow claim.",
        "overall_verdict": verdict,
        "overall_confidence": 0.9,
        "criteria": [
            {
                "id": "c1",
                "text": "The artifact includes login validation.",
                "blocking": True,
                "verdict": verdict,
                "confidence": 0.9,
                "evidence": [{"kind": "quote", "location": "artifact:12", "text": "validation"}],
                "reasoning": "Evidence-bound reasoning.",
                "counterevidence": [],
            }
        ],
        "open_questions": [],
        "disputed_points_if_any": [],
    }
    payload["phase"] = phase
    (audit_dir / f"login_flow_{phase}_{reviewer_id}_iteration1.json").write_text(
        json.dumps(payload)
    )


def test_record_round_rejects_a_missing_required_reviewer_file(tmp_path: Path) -> None:
    write_audit(tmp_path, "audit1")
    write_audit(tmp_path, "audit2")
    result = subprocess.run(
        [
            sys.executable,
            str(VALIDATOR),
            "record_round",
            "--feature-name",
            "login_flow",
            "--phase",
            "green",
            "--iteration",
            "1",
            "--audit-dir",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "audit3" in result.stdout


def write_summary(audit_dir: Path, status: str = "converged", final_verdict: str = "pass") -> None:
    payload = {
        "feature_name": "login_flow",
        "phase": "red",
        "iteration": 1,
        "reviewer_count": 3,
        "status": status,
        "disputed_criteria": [] if status == "converged" else ["c1"],
        "criteria": {
            "c1": {
                "criterion_text": "The artifact includes login validation.",
                "reviewer_count": 3,
                "verdicts": [final_verdict] * 3,
                "confidences": [0.9] * 3,
                "final_verdict": final_verdict,
                "converged": status == "converged",
            }
        },
    }
    (audit_dir / "login_flow_red_iteration1_summary.json").write_text(json.dumps(payload))


def run_transition(audit_dir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(VALIDATOR),
            "advance_phase",
            "--feature-name",
            "login_flow",
            "--from-phase",
            "red",
            "--to-phase",
            "green",
            "--iteration",
            "1",
            "--audit-dir",
            str(audit_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_advance_phase_rejects_missing_summary(tmp_path: Path) -> None:
    for reviewer_id in ("audit1", "audit2", "audit3"):
        write_audit(tmp_path, reviewer_id, phase="red")

    result = run_transition(tmp_path)

    assert result.returncode == 1
    assert "missing_summary" in result.stdout


def test_advance_phase_rejects_non_converged_summary(tmp_path: Path) -> None:
    for reviewer_id in ("audit1", "audit2", "audit3"):
        write_audit(tmp_path, reviewer_id, phase="red")
    write_summary(tmp_path, status="not_converged")

    result = run_transition(tmp_path)

    assert result.returncode == 1
    assert "not_converged" in result.stdout


def test_advance_phase_rejects_non_passing_blocking_criterion(tmp_path: Path) -> None:
    for reviewer_id in ("audit1", "audit2", "audit3"):
        write_audit(tmp_path, reviewer_id, verdict="fail", phase="red")
    write_summary(tmp_path, final_verdict="fail")

    result = run_transition(tmp_path)

    assert result.returncode == 1
    assert "blocking_criteria_not_pass" in result.stdout


def test_advance_phase_accepts_converged_blocking_pass(tmp_path: Path) -> None:
    for reviewer_id in ("audit1", "audit2", "audit3"):
        write_audit(tmp_path, reviewer_id, phase="red")
    write_summary(tmp_path)

    result = run_transition(tmp_path)

    assert result.returncode == 0
    assert '"state": "phase_advanced"' in result.stdout


def test_advance_phase_rejects_reviewer_specific_criteria(tmp_path: Path) -> None:
    for reviewer_id in ("audit1", "audit2", "audit3"):
        write_audit(tmp_path, reviewer_id, phase="red")
    audit3 = tmp_path / "login_flow_red_audit3_iteration1.json"
    payload = json.loads(audit3.read_text())
    payload["criteria"][0]["id"] = "scope"
    audit3.write_text(json.dumps(payload))
    write_summary(tmp_path)

    result = run_transition(tmp_path)

    assert result.returncode == 1
    assert "review_contract_mismatch" in result.stdout


def add_provenance(audit_dir: Path, identities: dict[str, str]) -> None:
    for reviewer_id, identity in identities.items():
        path = audit_dir / f"login_flow_red_{reviewer_id}_iteration1.json"
        payload = json.loads(path.read_text())
        payload["reviewer_agent_id"] = identity
        payload["reviewer_source"] = "subagent"
        path.write_text(json.dumps(payload))


def run_with_provenance(audit_dir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(VALIDATOR),
            "advance_phase",
            "--feature-name",
            "login_flow",
            "--from-phase",
            "red",
            "--to-phase",
            "green",
            "--iteration",
            "1",
            "--audit-dir",
            str(audit_dir),
            "--require-reviewer-provenance",
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_required_provenance_rejects_missing_fields(tmp_path: Path) -> None:
    for reviewer_id in ("audit1", "audit2", "audit3"):
        write_audit(tmp_path, reviewer_id, phase="red")
    write_summary(tmp_path)
    add_provenance(tmp_path, {"audit1": "agent:r1", "audit2": "agent:r2"})

    result = run_with_provenance(tmp_path)

    assert result.returncode == 1
    assert "missing_reviewer_provenance" in result.stdout
    assert "audit3" in result.stdout


def test_required_provenance_rejects_shared_identity(tmp_path: Path) -> None:
    for reviewer_id in ("audit1", "audit2", "audit3"):
        write_audit(tmp_path, reviewer_id, phase="red")
    write_summary(tmp_path)
    add_provenance(tmp_path, {"audit1": "agent:r1", "audit2": "agent:r1", "audit3": "agent:r3"})

    result = run_with_provenance(tmp_path)

    assert result.returncode == 1
    assert "duplicate_reviewer_agent_id" in result.stdout


def test_required_provenance_accepts_distinct_identities(tmp_path: Path) -> None:
    for reviewer_id in ("audit1", "audit2", "audit3"):
        write_audit(tmp_path, reviewer_id, phase="red")
    write_summary(tmp_path)
    add_provenance(tmp_path, {"audit1": "agent:r1", "audit2": "agent:r2", "audit3": "agent:r3"})

    result = run_with_provenance(tmp_path)

    assert result.returncode == 0, result.stdout
    assert '"phase_advanced"' in result.stdout


def test_provenance_is_optional_by_default(tmp_path: Path) -> None:
    for reviewer_id in ("audit1", "audit2", "audit3"):
        write_audit(tmp_path, reviewer_id, phase="red")
    write_summary(tmp_path)

    assert run_transition(tmp_path).returncode == 0


def write_round(audit_dir: Path, iteration: int, verdicts: dict[str, list[str]]) -> None:
    """Write three reviewer files and a summary; verdicts maps criterion id to per-reviewer verdicts."""
    for index, reviewer_id in enumerate(("audit1", "audit2", "audit3")):
        criteria = [
            {
                "id": criterion_id,
                "text": f"Criterion {criterion_id}.",
                "blocking": True,
                "verdict": per_reviewer[index],
                "confidence": 0.9,
                "evidence": [{"kind": "quote", "location": "artifact:1", "text": "x"}],
                "reasoning": "Evidence-bound reasoning.",
                "counterevidence": [],
            }
            for criterion_id, per_reviewer in verdicts.items()
        ]
        payload = {
            "feature_name": "login_flow",
            "phase": "red",
            "iteration": iteration,
            "reviewer_id": reviewer_id,
            "claim": "claim",
            "overall_verdict": "pass",
            "overall_confidence": 0.9,
            "criteria": criteria,
            "open_questions": [],
            "disputed_points_if_any": [],
        }
        (audit_dir / f"login_flow_red_{reviewer_id}_iteration{iteration}.json").write_text(
            json.dumps(payload)
        )
    summary_criteria = {}
    disputed = []
    for criterion_id, per_reviewer in verdicts.items():
        converged = len(set(per_reviewer)) == 1
        if not converged:
            disputed.append(criterion_id)
        summary_criteria[criterion_id] = {
            "criterion_text": f"Criterion {criterion_id}.",
            "reviewer_count": 3,
            "verdicts": per_reviewer,
            "confidences": [0.9] * 3,
            "final_verdict": per_reviewer[0] if converged else None,
            "converged": converged,
        }
    (audit_dir / f"login_flow_red_iteration{iteration}_summary.json").write_text(
        json.dumps(
            {
                "feature_name": "login_flow",
                "phase": "red",
                "iteration": iteration,
                "reviewer_count": 3,
                "status": "converged" if not disputed else "not_converged",
                "disputed_criteria": disputed,
                "criteria": summary_criteria,
            }
        )
    )


def run_iteration(audit_dir: Path, iteration: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(VALIDATOR),
            "advance_phase",
            "--feature-name",
            "login_flow",
            "--from-phase",
            "red",
            "--to-phase",
            "green",
            "--iteration",
            str(iteration),
            "--audit-dir",
            str(audit_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_follow_up_round_keeps_earlier_blocking_failure(tmp_path: Path) -> None:
    write_round(tmp_path, 1, {"c1": ["fail"] * 3, "c2": ["pass", "fail", "pass"]})
    write_round(tmp_path, 2, {"c2": ["pass"] * 3})

    result = run_iteration(tmp_path, 2)

    assert result.returncode == 1, result.stdout
    assert "blocking_criteria_not_pass" in result.stdout
    assert '"c1"' in result.stdout


def test_follow_up_round_accepts_when_every_blocking_criterion_passes(tmp_path: Path) -> None:
    write_round(tmp_path, 1, {"c1": ["pass"] * 3, "c2": ["pass", "fail", "pass"]})
    write_round(tmp_path, 2, {"c2": ["pass"] * 3})

    result = run_iteration(tmp_path, 2)

    assert result.returncode == 0, result.stdout


def test_follow_up_round_rejects_missing_earlier_round(tmp_path: Path) -> None:
    write_round(tmp_path, 2, {"c2": ["pass"] * 3})

    result = run_iteration(tmp_path, 2)

    assert result.returncode == 1
    assert "missing_prior_round" in result.stdout
