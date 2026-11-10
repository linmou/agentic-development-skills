#!/usr/bin/env python3
# Purpose: Present existing redundancy tool records compactly without ranking, dropping or validating candidates.

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from code_smell_monitor import knip_records


def read_object(root: Path, relative: str, errors: list[str]) -> dict[str, Any] | None:
    try:
        value = json.loads((root / relative).read_text())
        if not isinstance(value, dict):
            raise ValueError("expected a JSON object")
        return value
    except (OSError, ValueError) as error:
        errors.append(f"{relative}: {error}")
        return None


def indexed_knip(payload: dict[str, Any]) -> dict[tuple[str, str, str], list[str]]:
    """Reuse the monitor's exact file/export/type identities and preserve raw JSON pointers."""
    categories = ("files", "exports", "types")
    if "issues" in payload:
        if not isinstance(payload["issues"], list):
            raise ValueError("issues must be an array")
        groups = [(f"/issues/{i}", group) for i, group in enumerate(payload["issues"])]
    elif any(key in payload for key in categories):
        groups = [("", payload)]
    else:
        raise ValueError("unsupported Knip shape; no issues or file/export/type arrays")
    output: dict[tuple[str, str, str], list[str]] = {}
    for pointer, group in groups:
        if not isinstance(group, dict):
            raise ValueError(f"{pointer}: expected an object")
        for category in categories:
            entries = group.get(category, [])
            if not isinstance(entries, list):
                raise ValueError(f"{pointer}/{category}: expected an array")
            for i, entry in enumerate(entries):
                if not isinstance(entry, (str, dict)):
                    raise ValueError(f"{pointer}/{category}/{i}: unsupported entry")
                if isinstance(entry, dict) and not any(key in entry for key in ("name", "file", "path")):
                    raise ValueError(f"{pointer}/{category}/{i}: missing identity")
                isolated = {"file": group.get("file", ""), category: [entry]}
                for key in knip_records({"issues": [isolated]}):
                    output.setdefault(key, []).append(f"{pointer}/{category}/{i}")
    if set(output) != knip_records(payload):
        raise ValueError("normalized candidate inventory mismatch")
    return output


def build_index(root: Path, scope_from_report: bool = False) -> dict[str, Any]:
    errors: list[str] = []
    summary = read_object(root, "summary.json", errors)
    if summary is None:
        return {"index_status": "incomplete", "errors": errors}
    if not isinstance(summary.get("results"), list) or not isinstance(summary.get("coverage"), dict):
        return {"index_status": "incomplete", "errors": ["summary.json: missing results/coverage"]}
    checks = []
    for item in summary["results"]:
        if not isinstance(item, dict) or "name" not in item or "status" not in item:
            errors.append("summary.json: malformed detector status")
            continue
        checks.append({key: item.get(key) for key in ("name", "status", "exit_code", "timed_out")})
    modes: dict[str, dict[tuple[str, str, str], list[str]]] = {}
    raw_paths = {"normal": "raw/knip_dead_code.json", "production": "raw/knip_production.json"}
    for mode, relative in raw_paths.items():
        payload = read_object(root, relative, errors)
        if payload is not None:
            try:
                modes[mode] = indexed_knip(payload)
            except ValueError as error:
                errors.append(f"{relative}: {error}")
    keys = sorted(set().union(*(set(records) for records in modes.values())))
    knip: list[dict[str, Any]] = [{"key": list(key), "raw": {mode: records[key] for mode, records in modes.items() if key in records}}
            for key in keys]
    scope_view: dict[str, Any] = {"applied": False, "total": len(knip), "excluded": 0}
    if scope_from_report:
        scope, repo = summary.get("scope"), summary.get("repo")
        if not isinstance(repo, str) or not repo or not isinstance(scope, list) or not scope or not all(isinstance(item, str) for item in scope):
            return {"index_status": "incomplete", "errors": ["requested scope filter requires nonempty repo and scope in summary.json"]}
        roots = [(Path(repo) / item).resolve() for item in scope]
        kept = []
        unknown = 0
        for row in knip:
            filename = row["key"][0]
            if not filename:
                unknown += 1
                kept.append(row)
            else:
                location = (Path(repo) / filename).resolve()
                if any(location.is_relative_to(item) for item in roots):
                    kept.append(row)
        scope_view = {"applied": True, "total": len(knip), "included": len(kept),
                      "excluded": len(knip) - len(kept), "unknown_location_retained": unknown,
                      "all_candidates": "Omit --scope-from-report to inspect the full package inventory."}
        knip = kept

    behavioral = read_object(root, "raw/behavioral_redundancy.json", errors)
    behavior_view: dict[str, Any] = {}
    if behavioral is not None:
        findings = behavioral.get("findings")
        if not isinstance(findings, list) or not all(isinstance(item, dict) for item in findings):
            errors.append("raw/behavioral_redundancy.json: malformed findings array")
        else:
            behavior_view = {key: behavioral.get(key) for key in ("status", "analysis_scope", "scanned_files", "omissions", "limitations")}
            behavior_view["findings"] = [{"raw": f"/findings/{i}", "candidate": item}
                                         for i, item in enumerate(findings)]

    clones = read_object(root, "raw/jscpd_report/jscpd-report.json", errors)
    clone_view = []
    if clones is not None:
        duplicates = clones.get("duplicates")
        if not isinstance(duplicates, list):
            errors.append("raw/jscpd_report/jscpd-report.json: malformed duplicates array")
        else:
            for i, item in enumerate(duplicates):
                if not isinstance(item, dict) or not all(isinstance(item.get(side), dict) for side in ("firstFile", "secondFile")):
                    errors.append(f"raw/jscpd_report/jscpd-report.json: malformed duplicate {i}")
                    continue
                clone_view.append({"raw": f"/duplicates/{i}",
                                   "first": [item["firstFile"].get(key) for key in ("name", "start", "end")],
                                   "second": [item["secondFile"].get(key) for key in ("name", "start", "end")],
                                   "lines": item.get("lines"), "kind": item.get("kind")})
    return {
        "index_status": "incomplete" if errors else "complete",
        "note": "Navigation only. Candidates are unvalidated; raw evidence and source checks remain necessary. No ranking. Explicit scope filtering applies only to Knip; behavioral/clone records retain package scope. Index completeness is distinct from detector coverage.",
        "repo": summary.get("repo"), "scope_ref": "summary.json#/scope",
        "detector_coverage": summary["coverage"], "checks": checks,
        "raw_sources": {**raw_paths, "behavioral": "raw/behavioral_redundancy.json", "clones": "raw/jscpd_report/jscpd-report.json"},
        "knip_columns": ["file", "category", "symbol"],
        "knip_scope": scope_view,
        "knip_comparison_available": len(modes) == 2,
        "knip": knip, "behavioral": behavior_view, "clones": clone_view, "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__ or "Compact existing JS/TS redundancy outputs; does not analyze source.")
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--scope-from-report", action="store_true", help="Filter Knip locations to recorded scope; disclose excluded and unknown locations.")
    parser.add_argument("--section", choices=("all", "checks", "knip", "behavioral", "clones"), default="all")
    args = parser.parse_args()
    view = build_index(args.report_dir, args.scope_from_report)
    if args.section != "all":
        shared = ("index_status", "note", "repo", "scope_ref", "detector_coverage", "checks", "raw_sources", "errors")
        view = {key: value for key, value in view.items() if key in shared or key == args.section or key.startswith("knip_")}
    # One record per line prevents a single oversized line from defeating range-based inspection.
    for key, value in view.items():
        if isinstance(value, list) and key in ("knip", "clones"):
            print(json.dumps({key + "_count": len(value)}, separators=(",", ":")))
            for record in value:
                print(json.dumps({key: record}, separators=(",", ":")))
        elif key == "behavioral" and isinstance(value, dict):
            print(json.dumps({key: {k: v for k, v in value.items() if k != "findings"}}, separators=(",", ":")))
            for record in value.get("findings", []):
                print(json.dumps({"behavioral_finding": record}, separators=(",", ":")))
        else:
            print(json.dumps({key: value}, separators=(",", ":")))
    return 0 if view["index_status"] == "complete" else 2


if __name__ == "__main__":
    raise SystemExit(main())
