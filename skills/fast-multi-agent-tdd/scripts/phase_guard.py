#!/usr/bin/env python3
"""Check whether changed files stay inside the current TDD phase."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TEST_MARKERS = ("/tests/", "/__tests__/", ".test.", ".spec.")
DOC_SUFFIXES = {".md", ".rst", ".txt"}
DOC_MARKERS = ("/docs/",)


def normalize(path: str) -> str:
    return "/" + Path(path).as_posix().lstrip("/")


def classify(path: str) -> str:
    normalized = normalize(path)
    suffix = Path(normalized).suffix
    if normalized.endswith(".feature"):
        return "test"
    if any(marker in normalized for marker in TEST_MARKERS):
        return "test"
    if suffix in DOC_SUFFIXES or any(marker in normalized for marker in DOC_MARKERS):
        return "doc"
    return "prod"


def reason_for_phase(phase: str) -> str:
    if phase == "red":
        return "red may edit tests and docs only"
    if phase == "green":
        return "green may edit production files only; tests are red-phase only"
    if phase == "refactor":
        return "refactor may edit production files only; tests and docs belong to other phases"
    return "docs may edit documentation files only; production and tests belong to other phases"


def is_allowed(phase: str, kind: str) -> bool:
    if phase == "red":
        return kind in {"test", "doc"}
    if phase in {"green", "refactor"}:
        return kind == "prod"
    return kind == "doc"


def evaluate(phase: str, changed_files: list[str]) -> dict[str, object]:
    disallowed_files = []
    classified_files = []

    for path in changed_files:
        kind = classify(path)
        classified_files.append({"path": path, "kind": kind})
        if not is_allowed(phase, kind):
            disallowed_files.append(path)

    return {
        "phase": phase,
        "status": "pass" if not disallowed_files else "fail",
        "reason": reason_for_phase(phase),
        "changed_files": classified_files,
        "disallowed_files": disallowed_files,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("red", "green", "refactor", "docs"), required=True)
    parser.add_argument("--changed", nargs="+", required=True, help="Changed file paths for the phase.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = evaluate(args.phase, args.changed)
    print(json.dumps(payload, indent=2))
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
