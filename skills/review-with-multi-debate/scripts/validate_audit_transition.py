#!/usr/bin/env python3
# Validates persisted reviewer artifacts before an audit phase handoff.
"""Fail closed when reviewer evidence cannot justify the next audit phase."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from review_bundle import load_criteria_manifest, verify_bundle_file

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


def _validate_shared_contract(
    audits: list[dict[str, object]],
    criteria_manifest: Path | None = None,
    review_bundle_id: str | None = None,
    criteria_manifest_digest: str | None = None,
) -> list[str]:
    if not audits:
        return ["no_reviewer_results"]

    expected: dict[str, tuple[object, object]] = {}
    errors: list[str] = []
    for audit in audits:
        reviewer_id = str(audit.get("reviewer_id", "unknown"))
        criteria = audit.get("criteria")
        if not isinstance(criteria, list):
            continue
        current: dict[str, tuple[object, object]] = {}
        for criterion in criteria:
            if not isinstance(criterion, dict) or not isinstance(criterion.get("id"), str):
                continue
            criterion_id = criterion["id"]
            if criterion_id in current:
                errors.append(f"duplicate_criterion_id:{reviewer_id}:{criterion_id}")
            current[criterion_id] = (criterion.get("text"), criterion.get("blocking"))
        if not expected:
            expected = current
        elif set(current) != set(expected):
            errors.append(f"criterion_ids_mismatch:{reviewer_id}")
        else:
            for criterion_id, definition in expected.items():
                if current[criterion_id] != definition:
                    errors.append(f"criterion_definition_mismatch:{reviewer_id}:{criterion_id}")

        if review_bundle_id is not None and audit.get("review_bundle_id") != review_bundle_id:
            errors.append(f"review_bundle_mismatch:{reviewer_id}")
        if (
            criteria_manifest_digest is not None
            and audit.get("criteria_manifest_digest") != criteria_manifest_digest
        ):
            errors.append(f"criteria_manifest_mismatch:{reviewer_id}")

    if criteria_manifest is not None:
        try:
            manifest, manifest_digest = load_criteria_manifest(criteria_manifest)
            if (
                criteria_manifest_digest is not None
                and manifest_digest != criteria_manifest_digest
            ):
                errors.append("criteria_manifest_digest_invalid")
            manifest_criteria = {
                item["id"]: (item.get("text"), item.get("blocking"))
                for item in manifest.get("criteria", [])
                if isinstance(item, dict) and isinstance(item.get("id"), str)
            }
            if set(expected) != set(manifest_criteria):
                errors.append("criteria_manifest_ids_mismatch")
            for criterion_id, definition in manifest_criteria.items():
                if expected.get(criterion_id) != definition:
                    errors.append(f"criteria_manifest_definition_mismatch:{criterion_id}")
        except (OSError, ValueError, json.JSONDecodeError, AttributeError):
            errors.append("invalid_criteria_manifest")
    return sorted(set(errors))


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
    criteria_manifest: Path | None = None,
    review_bundle_id: str | None = None,
    criteria_manifest_digest: str | None = None,
    review_bundle: Path | None = None,
    repo_root: Path | None = None,
) -> dict[str, object]:
    if review_bundle is not None:
        bundle_result = verify_bundle_file(review_bundle, repo_root or Path.cwd())
        if bundle_result["status"] != "accepted":
            return {
                "status": "rejected",
                "reason": "review_bundle_changed",
                "errors": bundle_result["errors"],
            }
        review_bundle_id = review_bundle_id or str(bundle_result["bundle_id"])
        criteria_manifest_digest = criteria_manifest_digest or str(
            bundle_result["criteria_manifest_digest"]
        )
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

    contract_errors = _validate_shared_contract(
        reviewer_audits,
        criteria_manifest,
        review_bundle_id,
        criteria_manifest_digest,
    )
    if contract_errors:
        return {
            "status": "rejected",
            "reason": "review_contract_mismatch",
            "errors": contract_errors,
        }

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
    parser.add_argument("--criteria-manifest", type=Path)
    parser.add_argument("--review-bundle-id")
    parser.add_argument("--criteria-manifest-digest")
    parser.add_argument("--review-bundle", type=Path)
    parser.add_argument("--repo-root", type=Path)
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
            args.criteria_manifest,
            args.review_bundle_id,
            args.criteria_manifest_digest,
            args.review_bundle,
            args.repo_root,
        )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
