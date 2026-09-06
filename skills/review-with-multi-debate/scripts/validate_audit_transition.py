#!/usr/bin/env python3
# Validates persisted reviewer artifacts before an audit phase handoff.
"""Fail closed when reviewer evidence cannot justify the next audit phase."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REVIEWER_IDS = ("audit1", "audit2", "audit3")
ALLOWED_VERDICTS = {"pass", "fail", "insufficient_evidence"}


def audit_path(
    audit_dir: Path, feature_name: str, phase: str, reviewer_id: str, iteration: int
) -> Path:
    return audit_dir / f"{feature_name}_{phase}_{reviewer_id}_iteration{iteration}.json"


def validate_record_round(
    audit_dir: Path, feature_name: str, phase: str, iteration: int
) -> dict[str, object]:
    missing = [
        str(audit_path(audit_dir, feature_name, phase, reviewer_id, iteration))
        for reviewer_id in REVIEWER_IDS
        if not audit_path(audit_dir, feature_name, phase, reviewer_id, iteration).is_file()
    ]
    if missing:
        return {"status": "rejected", "missing_reviewer_results": missing}
    return {
        "status": "accepted",
        "state": "round_recorded",
        "reviewer_results": [
            str(audit_path(audit_dir, feature_name, phase, reviewer_id, iteration))
            for reviewer_id in REVIEWER_IDS
        ],
    }


def _load_json(path: Path) -> tuple[dict[str, object] | None, str | None]:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"invalid_json:{path}:{exc}"
    if not isinstance(value, dict):
        return None, f"invalid_object:{path}"
    return value, None


def _validate_reviewer(
    path: Path, feature_name: str, phase: str, iteration: int, reviewer_id: str
) -> tuple[dict[str, object] | None, list[str]]:
    audit, error = _load_json(path)
    if error:
        return None, [error]
    assert audit is not None
    errors: list[str] = []
    expected_metadata = {
        "feature_name": feature_name,
        "phase": phase,
        "iteration": iteration,
        "reviewer_id": reviewer_id,
    }
    for key, expected in expected_metadata.items():
        if audit.get(key) != expected:
            errors.append(f"metadata_mismatch:{path}:{key}")
    if audit.get("overall_verdict") not in ALLOWED_VERDICTS:
        errors.append(f"invalid_overall_verdict:{path}")
    criteria = audit.get("criteria")
    if not isinstance(criteria, list) or not criteria:
        errors.append(f"missing_criteria:{path}")
        return audit, errors
    for criterion in criteria:
        if not isinstance(criterion, dict):
            errors.append(f"invalid_criterion:{path}")
            continue
        required = (
            "id",
            "text",
            "blocking",
            "verdict",
            "confidence",
            "evidence",
            "reasoning",
            "counterevidence",
        )
        for key in required:
            if key not in criterion:
                errors.append(f"missing_criterion_field:{path}:{key}")
        if criterion.get("verdict") not in ALLOWED_VERDICTS:
            errors.append(f"invalid_criterion_verdict:{path}:{criterion.get('id')}")
        if not isinstance(criterion.get("blocking"), bool):
            errors.append(f"invalid_blocking_flag:{path}:{criterion.get('id')}")
        confidence = criterion.get("confidence")
        if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            errors.append(f"invalid_confidence:{path}:{criterion.get('id')}")
        evidence = criterion.get("evidence")
        if not isinstance(evidence, list):
            errors.append(f"invalid_evidence:{path}:{criterion.get('id')}")
        elif criterion.get("verdict") != "insufficient_evidence" and not evidence:
            errors.append(f"missing_evidence:{path}:{criterion.get('id')}")
        if not isinstance(criterion.get("reasoning"), str) or not criterion.get("reasoning"):
            errors.append(f"missing_reasoning:{path}:{criterion.get('id')}")
        if not isinstance(criterion.get("counterevidence"), list):
            errors.append(f"invalid_counterevidence:{path}:{criterion.get('id')}")
    return audit, errors


def validate_advance_phase(
    audit_dir: Path,
    feature_name: str,
    from_phase: str,
    to_phase: str,
    iteration: int,
) -> dict[str, object]:
    round_result = validate_record_round(audit_dir, feature_name, from_phase, iteration)
    if round_result["status"] != "accepted":
        return {"status": "rejected", "reason": "missing_reviewer_results", **round_result}

    reviewer_audits: list[dict[str, object]] = []
    errors: list[str] = []
    for reviewer_id in REVIEWER_IDS:
        path = audit_path(audit_dir, feature_name, from_phase, reviewer_id, iteration)
        audit, reviewer_errors = _validate_reviewer(
            path, feature_name, from_phase, iteration, reviewer_id
        )
        errors.extend(reviewer_errors)
        if audit is not None:
            reviewer_audits.append(audit)
    if errors:
        return {"status": "rejected", "reason": "invalid_reviewer_results", "errors": errors}

    summary_path = audit_dir / f"{feature_name}_{from_phase}_iteration{iteration}_summary.json"
    summary, summary_error = _load_json(summary_path)
    if summary_error:
        return {"status": "rejected", "reason": "missing_summary", "summary": str(summary_path)}
    assert summary is not None
    if (
        summary.get("feature_name") != feature_name
        or summary.get("phase") != from_phase
        or summary.get("iteration") != iteration
    ):
        return {
            "status": "rejected",
            "reason": "summary_metadata_mismatch",
            "summary": str(summary_path),
        }
    if summary.get("reviewer_count") != len(REVIEWER_IDS):
        return {
            "status": "rejected",
            "reason": "summary_reviewer_count",
            "summary": str(summary_path),
        }
    if summary.get("status") not in {"converged", "not_converged"}:
        return {
            "status": "rejected",
            "reason": "summary_invalid_status",
            "summary": str(summary_path),
        }
    summary_criteria = summary.get("criteria")
    if not isinstance(summary_criteria, dict):
        return {
            "status": "rejected",
            "reason": "summary_missing_criteria",
            "summary": str(summary_path),
        }

    blocking_ids: set[str] = set()
    for audit in reviewer_audits:
        criteria = audit.get("criteria")
        if not isinstance(criteria, list):
            continue
        for criterion in criteria:
            if (
                isinstance(criterion, dict)
                and criterion.get("blocking") is True
                and isinstance(criterion.get("id"), str)
            ):
                blocking_ids.add(criterion["id"])
    invalid_blocking = []
    disputed = summary.get("disputed_criteria", [])
    if not isinstance(disputed, list):
        return {
            "status": "rejected",
            "reason": "summary_invalid_disputes",
            "summary": str(summary_path),
        }
    for criterion_id in sorted(blocking_ids):
        criterion_summary = summary_criteria.get(criterion_id)
        if not isinstance(criterion_summary, dict):
            invalid_blocking.append(criterion_id)
            continue
        if (
            criterion_id in disputed
            or criterion_summary.get("converged") is not True
            or criterion_summary.get("final_verdict") != "pass"
        ):
            invalid_blocking.append(criterion_id)
    if invalid_blocking:
        return {
            "status": "rejected",
            "reason": "not_converged"
            if summary.get("status") == "not_converged"
            else "blocking_criteria_not_pass",
            "criteria": invalid_blocking,
            "summary": str(summary_path),
        }
    return {
        "status": "accepted",
        "state": "phase_advanced",
        "from_phase": from_phase,
        "to_phase": to_phase,
        "iteration": iteration,
        "summary": str(summary_path),
        "blocking_criteria": sorted(blocking_ids),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("transition", choices=("record_round", "advance_phase"))
    parser.add_argument("--feature-name", required=True)
    parser.add_argument("--phase")
    parser.add_argument("--from-phase")
    parser.add_argument("--to-phase")
    parser.add_argument("--iteration", required=True, type=int)
    parser.add_argument("--audit-dir", required=True, type=Path)
    args = parser.parse_args()
    if args.transition == "record_round" and not args.phase:
        parser.error("record_round requires --phase")
    return args


def main() -> int:
    args = parse_args()
    if args.transition == "record_round":
        assert args.phase is not None
        result = validate_record_round(
            args.audit_dir, args.feature_name, args.phase, args.iteration
        )
    else:
        if not args.from_phase or not args.to_phase:
            raise SystemExit("advance_phase requires --from-phase and --to-phase")
        result = validate_advance_phase(
            args.audit_dir,
            args.feature_name,
            args.from_phase,
            args.to_phase,
            args.iteration,
        )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
