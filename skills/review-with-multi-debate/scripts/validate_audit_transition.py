#!/usr/bin/env python3
# Validates persisted reviewer artifacts before a coarse audit workflow handoff.
"""Reject audit handoffs that do not have all required reviewer result files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REVIEWER_IDS = ("audit1", "audit2", "audit3")


def audit_path(audit_dir: Path, feature_name: str, phase: str, reviewer_id: str, iteration: int) -> Path:
    return audit_dir / f"{feature_name}_{phase}_{reviewer_id}_iteration{iteration}.json"


def validate_record_round(audit_dir: Path, feature_name: str, phase: str, iteration: int) -> dict[str, object]:
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("transition", choices=("record_round",))
    parser.add_argument("--feature-name", required=True)
    parser.add_argument("--phase", required=True)
    parser.add_argument("--iteration", required=True, type=int)
    parser.add_argument("--audit-dir", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = validate_record_round(args.audit_dir, args.feature_name, args.phase, args.iteration)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
