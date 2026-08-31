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


def write_audit(audit_dir: Path, reviewer_id: str) -> None:
    payload = {
        "feature_name": "login_flow",
        "phase": "green",
        "iteration": 1,
        "reviewer_id": reviewer_id,
        "claim": "The artifact satisfies the login-flow claim.",
        "overall_verdict": "pass",
        "overall_confidence": 0.9,
        "criteria": [{"id": "c1", "text": "The artifact includes login validation.", "blocking": True, "verdict": "pass", "confidence": 0.9, "evidence": [{"kind": "quote", "location": "artifact:12", "text": "validation"}], "reasoning": "Evidence-bound reasoning.", "counterevidence": []}],
        "open_questions": [],
        "disputed_points_if_any": [],
    }
    (audit_dir / f"login_flow_green_{reviewer_id}_iteration1.json").write_text(json.dumps(payload))


def test_record_round_rejects_a_missing_required_reviewer_file(tmp_path: Path) -> None:
    write_audit(tmp_path, "audit1")
    write_audit(tmp_path, "audit2")
    result = subprocess.run([sys.executable, str(VALIDATOR), "record_round", "--feature-name", "login_flow", "--phase", "green", "--iteration", "1", "--audit-dir", str(tmp_path)], capture_output=True, text=True, check=False)

    assert result.returncode == 1
    assert "audit3" in result.stdout
