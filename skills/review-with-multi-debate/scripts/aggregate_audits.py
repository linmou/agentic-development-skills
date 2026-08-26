#!/usr/bin/env python3
"""Aggregate reviewer audit JSON files into a convergence summary."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


DEFAULT_CONFIDENCE_GAP = 0.2


def load_audit(path: Path) -> dict:
    return json.loads(path.read_text())


def summarize_criterion(criteria: list[dict], confidence_gap: float) -> dict:
    verdicts = [criterion["verdict"] for criterion in criteria]
    confidences = [float(criterion.get("confidence", 0.0)) for criterion in criteria]
    converged = len(set(verdicts)) == 1 and (max(confidences) - min(confidences) <= confidence_gap)
    return {
        "criterion_text": criteria[0]["text"],
        "reviewer_count": len(criteria),
        "verdicts": verdicts,
        "confidences": confidences,
        "final_verdict": verdicts[0] if converged else "disputed",
        "converged": converged,
    }


def aggregate_audits(audit_paths: list[Path], confidence_gap: float = DEFAULT_CONFIDENCE_GAP) -> dict:
    audits = [load_audit(Path(path)) for path in audit_paths]
    criteria_by_id: dict[str, list[dict]] = defaultdict(list)

    for audit in audits:
        for criterion in audit.get("criteria", []):
            row = dict(criterion)
            row["reviewer_id"] = audit.get("reviewer_id", "unknown")
            criteria_by_id[criterion["id"]].append(row)

    criteria_summary = {
        criterion_id: summarize_criterion(criteria, confidence_gap)
        for criterion_id, criteria in sorted(criteria_by_id.items())
    }
    disputed_criteria = [
        criterion_id
        for criterion_id, summary in criteria_summary.items()
        if not summary["converged"]
    ]

    return {
        "feature_name": audits[0].get("feature_name") if audits else None,
        "phase": audits[0].get("phase") if audits else None,
        "iteration": audits[0].get("iteration") if audits else None,
        "reviewer_count": len(audits),
        "status": "converged" if not disputed_criteria else "not_converged",
        "disputed_criteria": disputed_criteria,
        "criteria": criteria_summary,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audit_paths", nargs="+", help="Audit JSON files to aggregate.")
    parser.add_argument(
        "--confidence-gap",
        type=float,
        default=DEFAULT_CONFIDENCE_GAP,
        help="Maximum allowed confidence spread for a criterion to count as converged.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path for the summary JSON. Prints to stdout when omitted.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = aggregate_audits([Path(path) for path in args.audit_paths], args.confidence_gap)
    content = json.dumps(summary, indent=2) + "\n"
    if args.output:
        args.output.write_text(content)
    else:
        print(content, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
