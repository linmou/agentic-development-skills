#!/usr/bin/env python3
# Purpose: Enforce the narrow low-risk Red focused re-review eligibility gate.

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

NORMAL_FOLLOW_UP = {"decision": "normal_three_reviewer_follow_up"}
AUDIT_FIELDS = {
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
}
CRITERION_FIELDS = {
    "id",
    "text",
    "blocking",
    "verdict",
    "confidence",
    "evidence",
    "reasoning",
    "counterevidence",
}
RECEIPT_FIELDS = {
    "schema",
    "feature",
    "route",
    "monitor_agent_id",
    "monitor_source",
    "red_reviewer_agent_ids",
    "reviewer_source",
}
ELIGIBILITY_FIELDS = {
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
}
VERDICTS = {"pass", "fail", "insufficient_evidence"}


class InvalidGateInput(ValueError):
    pass


def load_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise InvalidGateInput from exc
    if not isinstance(payload, dict):
        raise InvalidGateInput
    return payload


def is_nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def is_agent_identity(value: object) -> bool:
    return is_nonempty_string(value)


def is_confidence(value: object) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float)) and 0 <= value <= 1


def validate_citations(value: object, *, allow_empty: bool) -> None:
    if not isinstance(value, list) or (not value and not allow_empty):
        raise InvalidGateInput
    for citation in value:
        if not isinstance(citation, dict):
            raise InvalidGateInput
        if not is_nonempty_string(citation.get("kind")):
            raise InvalidGateInput
        if not is_nonempty_string(citation.get("location")):
            raise InvalidGateInput


def validate_criterion(value: object) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != CRITERION_FIELDS:
        raise InvalidGateInput
    if not is_nonempty_string(value["id"]) or not is_nonempty_string(value["text"]):
        raise InvalidGateInput
    if not isinstance(value["blocking"], bool) or value["verdict"] not in VERDICTS:
        raise InvalidGateInput
    if not is_confidence(value["confidence"]) or not is_nonempty_string(value["reasoning"]):
        raise InvalidGateInput
    validate_citations(
        value["evidence"], allow_empty=value["verdict"] == "insufficient_evidence"
    )
    validate_citations(value["counterevidence"], allow_empty=True)
    return value


def expected_overall(criteria: list[dict[str, Any]]) -> str:
    if any(item["verdict"] == "insufficient_evidence" for item in criteria):
        return "insufficient_evidence"
    if any(item["verdict"] == "fail" for item in criteria):
        return "fail"
    return "pass"


def validate_audit(path: Path) -> dict[str, Any]:
    payload = load_object(path)
    if set(payload) != AUDIT_FIELDS:
        raise InvalidGateInput
    string_fields = ("feature_name", "phase", "reviewer_id", "reviewer_agent_id", "claim")
    if any(not is_nonempty_string(payload[field]) for field in string_fields):
        raise InvalidGateInput
    if not is_agent_identity(payload["reviewer_agent_id"]):
        raise InvalidGateInput
    if not is_nonempty_string(payload["reviewer_source"]):
        raise InvalidGateInput
    if isinstance(payload["iteration"], bool) or not isinstance(payload["iteration"], int):
        raise InvalidGateInput
    if payload["overall_verdict"] not in VERDICTS:
        raise InvalidGateInput
    if not is_confidence(payload["overall_confidence"]):
        raise InvalidGateInput
    if not isinstance(payload["criteria"], list) or not payload["criteria"]:
        raise InvalidGateInput
    criteria = [validate_criterion(item) for item in payload["criteria"]]
    if len({item["id"] for item in criteria}) != len(criteria):
        raise InvalidGateInput
    for field in ("open_questions", "disputed_points_if_any"):
        value = payload[field]
        if not isinstance(value, list) or any(not is_nonempty_string(item) for item in value):
            raise InvalidGateInput
    if payload["overall_verdict"] != expected_overall(criteria):
        raise InvalidGateInput
    return payload


def validate_receipt(path: Path, *, route: str | None) -> dict[str, Any]:
    payload = load_object(path)
    if set(payload) != RECEIPT_FIELDS or payload["schema"] != 2:
        raise InvalidGateInput
    if (
        not is_nonempty_string(payload["feature"])
        or payload["route"] not in {"compact", "full"}
        or (route is not None and payload["route"] != route)
    ):
        raise InvalidGateInput
    if not is_agent_identity(payload["monitor_agent_id"]):
        raise InvalidGateInput
    if not is_nonempty_string(payload["monitor_source"]) or not is_nonempty_string(
        payload["reviewer_source"]
    ):
        raise InvalidGateInput
    owners = payload["red_reviewer_agent_ids"]
    if not isinstance(owners, list) or len(owners) != 3:
        raise InvalidGateInput
    if any(not is_agent_identity(owner) for owner in owners) or len(set(owners)) != 3:
        raise InvalidGateInput
    if payload["monitor_agent_id"] in owners:
        raise InvalidGateInput
    return payload


def criterion_identity(item: dict[str, Any]) -> tuple[str, str, bool]:
    return item["id"], item["text"], item["blocking"]


def validate_owned_red_audits(
    receipt: dict[str, Any],
    audit_paths: list[Path],
    *,
    iteration: int,
) -> list[dict[str, Any]]:
    if len(audit_paths) != 3 or iteration < 1:
        raise InvalidGateInput
    slots = ("audit1", "audit2", "audit3")
    audits: list[dict[str, Any]] = []
    for index, (slot, path) in enumerate(zip(slots, audit_paths, strict=True)):
        expected_name = f"{receipt['feature']}_red_{slot}_iteration{iteration}.json"
        audit = validate_audit(path)
        expected_metadata = {
            "feature_name": receipt["feature"],
            "phase": "red",
            "iteration": iteration,
            "reviewer_id": slot,
            "reviewer_agent_id": receipt["red_reviewer_agent_ids"][index],
            "reviewer_source": receipt["reviewer_source"],
        }
        if path.name != expected_name or any(
            audit[field] != expected for field, expected in expected_metadata.items()
        ):
            raise InvalidGateInput
        audits.append(audit)
    return audits


def provenance_decision(args: argparse.Namespace) -> dict[str, Any]:
    receipt_path = Path(args.role_receipt)
    receipt = validate_receipt(receipt_path, route=None)
    audit_paths = [Path(path) for path in args.audits]
    audits = validate_owned_red_audits(receipt, audit_paths, iteration=args.iteration)
    return {
        "schema": 1,
        "decision": "provenance_valid",
        "feature": receipt["feature"],
        "phase": "red",
        "iteration": args.iteration,
        "monitor_agent_id": receipt["monitor_agent_id"],
        "monitor_source": receipt["monitor_source"],
        "role_receipt_path": str(receipt_path.resolve()),
        "role_receipt_sha256": hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
        "reviewers": [
            {
                "reviewer_id": audit["reviewer_id"],
                "reviewer_agent_id": audit["reviewer_agent_id"],
                "reviewer_source": audit["reviewer_source"],
                "audit_path": str(path.resolve()),
                "audit_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
            for path, audit in zip(audit_paths, audits, strict=True)
        ],
    }


def initial_decision(args: argparse.Namespace) -> dict[str, Any]:
    audit_paths = [Path(path) for path in args.audits]
    if len(audit_paths) != 3 or args.route != "compact" or args.risk_tier != "low":
        raise InvalidGateInput
    receipt_path = Path(args.role_receipt)
    receipt = validate_receipt(receipt_path, route=args.route)
    audits = validate_owned_red_audits(receipt, audit_paths, iteration=1)

    expected_criteria = [criterion_identity(item) for item in audits[0]["criteria"]]
    failed_ids: list[str] = []
    for audit in audits:
        if [criterion_identity(item) for item in audit["criteria"]] != expected_criteria:
            raise InvalidGateInput
        if audit["open_questions"] or audit["disputed_points_if_any"]:
            raise InvalidGateInput
        if any(item["counterevidence"] for item in audit["criteria"]):
            raise InvalidGateInput
        if any(item["verdict"] == "insufficient_evidence" for item in audit["criteria"]):
            raise InvalidGateInput
        failures = [item for item in audit["criteria"] if item["verdict"] == "fail"]
        if len(failures) != 1 or not failures[0]["blocking"]:
            raise InvalidGateInput
        failed_ids.append(failures[0]["id"])
    if len(set(failed_ids)) != 1:
        raise InvalidGateInput

    repaired = next(item for item in audits[0]["criteria"] if item["id"] == failed_ids[0])
    receipt_bytes = receipt_path.read_bytes()
    return {
        "schema": 1,
        "decision": "focused_re_review",
        "feature": receipt["feature"],
        "route": args.route,
        "risk_tier": args.risk_tier,
        "monitor_agent_id": receipt["monitor_agent_id"],
        "monitor_source": receipt["monitor_source"],
        "initial_reviewer_agent_ids": receipt["red_reviewer_agent_ids"],
        "reviewer_source": receipt["reviewer_source"],
        "role_receipt_path": str(receipt_path.resolve()),
        "role_receipt_sha256": hashlib.sha256(receipt_bytes).hexdigest(),
        "repaired_criterion": {
            "id": repaired["id"],
            "text": repaired["text"],
            "blocking": repaired["blocking"],
        },
    }


def validate_eligibility(path: Path, receipt_path: Path) -> dict[str, Any]:
    eligibility = load_object(path)
    if set(eligibility) != ELIGIBILITY_FIELDS or eligibility["schema"] != 1:
        raise InvalidGateInput
    if eligibility["decision"] != "focused_re_review":
        raise InvalidGateInput
    if eligibility["route"] != "compact" or eligibility["risk_tier"] != "low":
        raise InvalidGateInput
    if not is_nonempty_string(eligibility["feature"]):
        raise InvalidGateInput
    if not is_agent_identity(eligibility["monitor_agent_id"]):
        raise InvalidGateInput
    if not is_nonempty_string(eligibility["monitor_source"]):
        raise InvalidGateInput
    owners = eligibility["initial_reviewer_agent_ids"]
    if not isinstance(owners, list) or len(owners) != 3:
        raise InvalidGateInput
    if any(not is_agent_identity(owner) for owner in owners) or len(set(owners)) != 3:
        raise InvalidGateInput
    if eligibility["monitor_agent_id"] in owners:
        raise InvalidGateInput
    if not is_nonempty_string(eligibility["reviewer_source"]):
        raise InvalidGateInput
    if eligibility["role_receipt_path"] != str(receipt_path.resolve()):
        raise InvalidGateInput
    try:
        receipt_bytes = receipt_path.read_bytes()
    except OSError as exc:
        raise InvalidGateInput from exc
    if eligibility["role_receipt_sha256"] != hashlib.sha256(receipt_bytes).hexdigest():
        raise InvalidGateInput
    repaired = eligibility["repaired_criterion"]
    if not isinstance(repaired, dict) or set(repaired) != {"id", "text", "blocking"}:
        raise InvalidGateInput
    if not is_nonempty_string(repaired["id"]) or not is_nonempty_string(repaired["text"]):
        raise InvalidGateInput
    if repaired["blocking"] is not True:
        raise InvalidGateInput

    receipt = validate_receipt(receipt_path, route="compact")
    receipt_pairs = (
        ("feature", "feature"),
        ("monitor_agent_id", "monitor_agent_id"),
        ("monitor_source", "monitor_source"),
        ("red_reviewer_agent_ids", "initial_reviewer_agent_ids"),
        ("reviewer_source", "reviewer_source"),
    )
    if any(receipt[left] != eligibility[right] for left, right in receipt_pairs):
        raise InvalidGateInput
    return eligibility


def focused_decision(args: argparse.Namespace) -> dict[str, Any]:
    receipt_path = Path(args.role_receipt)
    eligibility_path = Path(args.eligibility)
    eligibility = validate_eligibility(eligibility_path, receipt_path)
    if not is_agent_identity(args.focused_reviewer_agent_id):
        raise InvalidGateInput
    if not is_nonempty_string(args.reviewer_source):
        raise InvalidGateInput
    prior_ids = [eligibility["monitor_agent_id"], *eligibility["initial_reviewer_agent_ids"]]
    if args.focused_reviewer_agent_id in prior_ids:
        raise InvalidGateInput

    audit_path = Path(args.focused_audit)
    if audit_path.name != f"{eligibility['feature']}_red_focused_iteration2.json":
        raise InvalidGateInput
    audit = validate_audit(audit_path)
    expected_metadata = {
        "feature_name": eligibility["feature"],
        "phase": "red",
        "iteration": 2,
        "reviewer_id": "focused",
        "reviewer_agent_id": args.focused_reviewer_agent_id,
        "reviewer_source": args.reviewer_source,
        "overall_verdict": "pass",
    }
    if any(audit[field] != value for field, value in expected_metadata.items()):
        raise InvalidGateInput
    if audit["open_questions"] or audit["disputed_points_if_any"]:
        raise InvalidGateInput
    if len(audit["criteria"]) != 1:
        raise InvalidGateInput
    reviewed = audit["criteria"][0]
    repaired = eligibility["repaired_criterion"]
    if criterion_identity(reviewed) != (
        repaired["id"],
        repaired["text"],
        repaired["blocking"],
    ):
        raise InvalidGateInput
    if reviewed["verdict"] != "pass" or reviewed["counterevidence"]:
        raise InvalidGateInput
    return {
        "schema": 1,
        "decision": "advance_green",
        "feature": eligibility["feature"],
        "phase": "red",
        "iteration": 2,
        "focused_reviewer_agent_id": args.focused_reviewer_agent_id,
        "reviewer_source": args.reviewer_source,
        "focused_audit_path": str(audit_path.resolve()),
        "focused_audit_sha256": hashlib.sha256(audit_path.read_bytes()).hexdigest(),
        "role_receipt_path": str(receipt_path.resolve()),
        "role_receipt_sha256": hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
        "eligibility_path": str(eligibility_path.resolve()),
        "eligibility_sha256": hashlib.sha256(eligibility_path.read_bytes()).hexdigest(),
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    initial = subparsers.add_parser("initial")
    initial.add_argument("--route", choices=("compact", "full"), required=True)
    initial.add_argument("--risk-tier", choices=("low", "medium", "high"), required=True)
    initial.add_argument("--role-receipt", required=True)
    initial.add_argument("--output", required=True)
    initial.add_argument("audits", nargs="+")

    provenance = subparsers.add_parser("provenance")
    provenance.add_argument("--role-receipt", required=True)
    provenance.add_argument("--iteration", required=True, type=int)
    provenance.add_argument("--output", required=True)
    provenance.add_argument("audits", nargs="+")

    focused = subparsers.add_parser("focused")
    focused.add_argument("--eligibility", required=True)
    focused.add_argument("--role-receipt", required=True)
    focused.add_argument("--focused-audit", required=True)
    focused.add_argument("--focused-reviewer-agent-id", required=True)
    focused.add_argument("--reviewer-source", required=True)
    focused.add_argument("--output", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "initial":
            result = initial_decision(args)
        elif args.command == "provenance":
            result = provenance_decision(args)
        else:
            result = focused_decision(args)
        write_json(Path(args.output), result)
    except (InvalidGateInput, OSError):
        print(json.dumps(NORMAL_FOLLOW_UP, sort_keys=True))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
