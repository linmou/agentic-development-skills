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
