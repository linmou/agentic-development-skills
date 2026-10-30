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
    # Reviewers genuinely disagree, so the not_converged summary is consistent with them.
    write_round(tmp_path, 1, {"c1": ["pass", "pass", "fail"]})

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


def rewrite_round_criterion(audit_dir: Path, iteration: int, criterion_id: str, **changes: object) -> None:
    for reviewer_id in ("audit1", "audit2", "audit3"):
        path = audit_dir / f"login_flow_red_{reviewer_id}_iteration{iteration}.json"
        payload = json.loads(path.read_text())
        for criterion in payload["criteria"]:
            if criterion["id"] == criterion_id:
                criterion.update(changes)
        path.write_text(json.dumps(payload))


def test_follow_up_round_rejects_weakened_criterion_text(tmp_path: Path) -> None:
    write_round(tmp_path, 1, {"c1": ["pass"] * 3, "c2": ["pass", "fail", "pass"]})
    write_round(tmp_path, 2, {"c2": ["pass"] * 3})
    rewrite_round_criterion(tmp_path, 2, "c2", text="A weaker version of c2.")

    result = run_iteration(tmp_path, 2)

    assert result.returncode == 1
    assert "criterion_redefined:c2" in result.stdout


def test_follow_up_round_rejects_dropping_blocking_flag(tmp_path: Path) -> None:
    write_round(tmp_path, 1, {"c1": ["pass"] * 3, "c2": ["fail", "fail", "pass"]})
    write_round(tmp_path, 2, {"c2": ["fail"] * 3})
    rewrite_round_criterion(tmp_path, 2, "c2", blocking=False)

    result = run_iteration(tmp_path, 2)

    assert result.returncode == 1
    assert "criterion_redefined:c2" in result.stdout


def test_follow_up_round_rejects_new_criterion(tmp_path: Path) -> None:
    write_round(tmp_path, 1, {"c1": ["pass"] * 3, "c2": ["pass", "fail", "pass"]})
    write_round(tmp_path, 2, {"c3": ["pass"] * 3})

    result = run_iteration(tmp_path, 2)

    assert result.returncode == 1
    assert "criterion_added_in_follow_up:c3" in result.stdout


def write_manifest(audit_dir: Path, criterion_ids: list[str]) -> Path:
    path = audit_dir / "criteria.json"
    path.write_text(
        json.dumps(
            {
                "criteria": [
                    {"id": criterion_id, "text": f"Criterion {criterion_id}.", "blocking": True}
                    for criterion_id in criterion_ids
                ]
            }
        )
    )
    return path


def run_frozen(audit_dir: Path, iteration: int, manifest: Path) -> subprocess.CompletedProcess[str]:
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
            "--criteria-manifest",
            str(manifest),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_frozen_follow_up_with_disputed_subset_converges(tmp_path: Path) -> None:
    manifest = write_manifest(tmp_path, ["c1", "c2"])
    write_round(tmp_path, 1, {"c1": ["pass"] * 3, "c2": ["pass", "fail", "pass"]})
    write_round(tmp_path, 2, {"c2": ["pass"] * 3})

    result = run_frozen(tmp_path, 2, manifest)

    assert result.returncode == 0, result.stdout


def test_frozen_first_round_still_requires_full_manifest(tmp_path: Path) -> None:
    manifest = write_manifest(tmp_path, ["c1", "c2"])
    write_round(tmp_path, 1, {"c1": ["pass"] * 3})

    result = run_frozen(tmp_path, 1, manifest)

    assert result.returncode == 1
    assert "criteria_manifest_ids_mismatch" in result.stdout


def test_follow_up_round_cannot_rereview_settled_criterion(tmp_path: Path) -> None:
    write_round(tmp_path, 1, {"c1": ["fail"] * 3, "c2": ["pass", "fail", "pass"]})
    write_round(tmp_path, 2, {"c1": ["pass"] * 3, "c2": ["pass"] * 3})

    result = run_iteration(tmp_path, 2)

    assert result.returncode == 1
    assert "follow_up_scope_violation" in result.stdout
    assert "criterion_not_disputed:c1" in result.stdout


def test_follow_up_gate_revalidates_earlier_reviewer_files(tmp_path: Path) -> None:
    write_round(tmp_path, 1, {"c1": ["pass"] * 3, "c2": ["pass", "fail", "pass"]})
    write_round(tmp_path, 2, {"c2": ["pass"] * 3})
    path = tmp_path / "login_flow_red_audit1_iteration1.json"
    payload = json.loads(path.read_text())
    payload["criteria"][0]["evidence"] = []
    path.write_text(json.dumps(payload))

    result = run_iteration(tmp_path, 2)

    assert result.returncode == 1
    assert "invalid_prior_round" in result.stdout
    assert "missing_evidence" in result.stdout


def test_follow_up_gate_checks_earlier_round_provenance(tmp_path: Path) -> None:
    write_round(tmp_path, 1, {"c1": ["pass"] * 3, "c2": ["pass", "fail", "pass"]})
    write_round(tmp_path, 2, {"c2": ["pass"] * 3})
    for iteration in (1, 2):
        for index, reviewer_id in enumerate(("audit1", "audit2", "audit3")):
            path = tmp_path / f"login_flow_red_{reviewer_id}_iteration{iteration}.json"
            payload = json.loads(path.read_text())
            if iteration == 2 or reviewer_id != "audit3":
                payload["reviewer_agent_id"] = f"agent:r{index}"
                payload["reviewer_source"] = "subagent"
            path.write_text(json.dumps(payload))

    result = subprocess.run(
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
            "2",
            "--audit-dir",
            str(tmp_path),
            "--require-reviewer-provenance",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "invalid_prior_round" in result.stdout
    assert "missing_reviewer_provenance" in result.stdout


def _digest_of(manifest: dict) -> str:
    sys.path.insert(0, str(ROOT / "scripts"))
    from review_bundle import criteria_manifest_digest

    return criteria_manifest_digest(manifest)


def stamp_digest(audit_dir: Path, iteration: int, digest: str) -> None:
    for reviewer_id in ("audit1", "audit2", "audit3"):
        path = audit_dir / f"login_flow_red_{reviewer_id}_iteration{iteration}.json"
        payload = json.loads(path.read_text())
        payload["criteria_manifest_digest"] = digest
        path.write_text(json.dumps(payload))


def test_frozen_follow_up_uses_each_rounds_own_manifest_digest(tmp_path: Path) -> None:
    manifests = {}
    for iteration, ids in ((1, ["c1", "c2"]), (2, ["c2"])):
        manifests[iteration] = {
            "feature_name": "login_flow",
            "phase": "red",
            "iteration": iteration,
            "criteria": [{"id": i, "text": f"Criterion {i}.", "blocking": True} for i in ids],
        }
    write_round(tmp_path, 1, {"c1": ["pass"] * 3, "c2": ["pass", "fail", "pass"]})
    write_round(tmp_path, 2, {"c2": ["pass"] * 3})
    stamp_digest(tmp_path, 1, _digest_of(manifests[1]))
    stamp_digest(tmp_path, 2, _digest_of(manifests[2]))
    assert _digest_of(manifests[1]) != _digest_of(manifests[2])
    manifest_path = tmp_path / "criteria_iteration2.json"
    manifest_path.write_text(json.dumps(manifests[2]))

    result = subprocess.run(
        [
            sys.executable, str(VALIDATOR), "advance_phase",
            "--feature-name", "login_flow", "--from-phase", "red", "--to-phase", "green",
            "--iteration", "2", "--audit-dir", str(tmp_path),
            "--criteria-manifest", str(manifest_path),
            "--criteria-manifest-digest", _digest_of(manifests[2]),
        ],
        capture_output=True, text=True, check=False,
    )

    assert result.returncode == 0, result.stdout


def test_stale_prior_summary_cannot_hide_a_blocking_failure(tmp_path: Path) -> None:
    write_round(tmp_path, 1, {"c1": ["pass"] * 3, "c2": ["pass", "fail", "pass"]})
    write_round(tmp_path, 2, {"c2": ["pass"] * 3})
    # Round-1 reviewer files regenerated after aggregation: c1 now fails unanimously.
    for reviewer_id in ("audit1", "audit2", "audit3"):
        path = tmp_path / f"login_flow_red_{reviewer_id}_iteration1.json"
        payload = json.loads(path.read_text())
        payload["criteria"][0]["verdict"] = "fail"
        path.write_text(json.dumps(payload))

    result = run_iteration(tmp_path, 2)

    assert result.returncode == 1
    assert "stale_summary" in result.stdout
    assert "summary_verdicts:c1" in result.stdout


def test_stale_current_summary_is_rejected(tmp_path: Path) -> None:
    write_round(tmp_path, 1, {"c1": ["pass"] * 3})
    for reviewer_id in ("audit1", "audit2", "audit3"):
        path = tmp_path / f"login_flow_red_{reviewer_id}_iteration1.json"
        payload = json.loads(path.read_text())
        payload["criteria"][0]["verdict"] = "fail"
        path.write_text(json.dumps(payload))

    result = run_iteration(tmp_path, 1)

    assert result.returncode == 1
    assert "stale_summary" in result.stdout


def set_confidences(audit_dir: Path, iteration: int, criterion_id: str, confidences: list[float]) -> None:
    for reviewer_id, confidence in zip(("audit1", "audit2", "audit3"), confidences):
        path = audit_dir / f"login_flow_red_{reviewer_id}_iteration{iteration}.json"
        payload = json.loads(path.read_text())
        for criterion in payload["criteria"]:
            if criterion["id"] == criterion_id:
                criterion["confidence"] = confidence
        path.write_text(json.dumps(payload))
    summary_path = audit_dir / f"login_flow_red_iteration{iteration}_summary.json"
    summary = json.loads(summary_path.read_text())
    summary["criteria"][criterion_id]["confidences"] = confidences
    summary_path.write_text(json.dumps(summary))


def test_gate_recomputes_confidence_spread(tmp_path: Path) -> None:
    write_round(tmp_path, 1, {"c1": ["pass"] * 3})
    set_confidences(tmp_path, 1, "c1", [0.1, 0.5, 0.9])

    result = run_iteration(tmp_path, 1)

    assert result.returncode == 1
    assert "summary_convergence:c1" in result.stdout


def test_gate_accepts_wide_spread_with_matching_custom_gap(tmp_path: Path) -> None:
    write_round(tmp_path, 1, {"c1": ["pass"] * 3})
    set_confidences(tmp_path, 1, "c1", [0.65, 0.7, 0.9])

    result = subprocess.run(
        [
            sys.executable, str(VALIDATOR), "advance_phase",
            "--feature-name", "login_flow", "--from-phase", "red", "--to-phase", "green",
            "--iteration", "1", "--audit-dir", str(tmp_path), "--confidence-gap", "0.3",
        ],
        capture_output=True, text=True, check=False,
    )

    assert result.returncode == 0, result.stdout


def test_omitted_dispute_carries_forward_to_later_rounds(tmp_path: Path) -> None:
    write_round(tmp_path, 1, {"c1": ["pass", "fail", "pass"], "c2": ["pass", "fail", "pass"]})
    write_round(tmp_path, 2, {"c1": ["pass"] * 3})
    write_round(tmp_path, 3, {"c2": ["pass"] * 3})

    result = run_iteration(tmp_path, 3)

    assert result.returncode == 0, result.stdout


def test_malformed_summary_confidences_are_rejected_not_raised(tmp_path: Path) -> None:
    write_round(tmp_path, 1, {"c1": ["pass"] * 3})
    summary_path = tmp_path / "login_flow_red_iteration1_summary.json"
    summary = json.loads(summary_path.read_text())
    summary["criteria"]["c1"]["confidences"] = ["bad"]
    summary_path.write_text(json.dumps(summary))

    result = run_iteration(tmp_path, 1)

    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert "summary_confidences:c1" in result.stdout
