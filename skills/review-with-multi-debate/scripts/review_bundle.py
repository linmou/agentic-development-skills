#!/usr/bin/env python3
# Freeze and verify the narrow set of inputs shared by independent reviewers.

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def criteria_manifest_digest(manifest: dict) -> str:
    payload = dict(manifest)
    payload.pop("manifest_id", None)
    return _digest(payload)


def load_criteria_manifest(path: Path) -> tuple[dict, str]:
    manifest = json.loads(path.read_text())
    if not isinstance(manifest, dict):
        raise ValueError("criteria manifest must be a JSON object")
    criteria = manifest.get("criteria")
    if not isinstance(criteria, list) or not criteria:
        raise ValueError("criteria manifest must contain criteria")
    ids = [item.get("id") for item in criteria if isinstance(item, dict)]
    if len(ids) != len(criteria) or len(set(ids)) != len(ids):
        raise ValueError("criteria manifest IDs must be unique")
    for item in criteria:
        if not isinstance(item.get("text"), str) or not item["text"]:
            raise ValueError(f"criterion {item.get('id')} is missing text")
        if not isinstance(item.get("blocking"), bool):
            raise ValueError(f"criterion {item.get('id')} has invalid blocking flag")
    digest = criteria_manifest_digest(manifest)
    if manifest.get("manifest_id") not in (None, digest):
        raise ValueError("criteria manifest_id does not match manifest contents")
    return manifest, digest


def _repo_path(repo_root: Path, path: str) -> Path:
    candidate = (repo_root / path).resolve()
    root = repo_root.resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError(f"path is outside repository: {path}")
    return candidate


def _file_record(repo_root: Path, relative_path: str) -> dict:
    path = _repo_path(repo_root, relative_path)
    if not path.is_file():
        raise ValueError(f"review input is not a file: {relative_path}")
    data = path.read_bytes()
    return {"sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}


def _scope_files(repo_root: Path, scope_path: Path) -> list[str]:
    scope = json.loads(scope_path.read_text())
    patterns = [*scope.get("editable", []), *scope.get("protected", [])]
    paths: set[str] = set()
    for pattern in patterns:
        matches = (
            (repo_root / pattern).parent.glob(Path(pattern).name)
            if "**" in pattern
            else repo_root.glob(pattern)
        )
        for match in matches:
            if match.is_file():
                paths.add(str(match.resolve().relative_to(repo_root.resolve())))
            elif match.is_dir():
                for child in match.rglob("*"):
                    if child.is_file():
                        paths.add(str(child.resolve().relative_to(repo_root.resolve())))
    return sorted(paths)


def _git_head(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def freeze(
    repo_root: Path,
    output: Path,
    feature_name: str,
    phase: str,
    iteration: int,
    criteria_manifest: Path,
    scope: Path | None,
    include: list[str],
) -> dict:
    manifest, manifest_digest = load_criteria_manifest(criteria_manifest)
    if (
        manifest.get("feature_name") != feature_name
        or manifest.get("phase") != phase
        or manifest.get("iteration") != iteration
    ):
        raise ValueError("criteria manifest metadata does not match review bundle")

    relative_manifest = str(criteria_manifest.resolve().relative_to(repo_root.resolve()))
    scoped_paths = _scope_files(repo_root, scope) if scope is not None else []
    scope_path = (
        str(scope.resolve().relative_to(repo_root.resolve())) if scope is not None else None
    )
    paths = list(dict.fromkeys([relative_manifest, scope_path, *scoped_paths, *include]))
    paths = [path for path in paths if path is not None]
    files = {path: _file_record(repo_root, path) for path in paths}
    payload = {
        "schema": 1,
        "feature_name": feature_name,
        "phase": phase,
        "iteration": iteration,
        "git_head": _git_head(repo_root),
        "criteria_manifest": relative_manifest,
        "criteria_manifest_digest": manifest_digest,
        "files": files,
        "frozen_at": datetime.now(timezone.utc).isoformat(),
    }
    bundle = dict(payload)
    bundle["bundle_id"] = _digest(payload)
    output.write_text(json.dumps(bundle, indent=2) + "\n")
    return bundle


def verify_bundle_file(bundle_path: Path, repo_root: Path) -> dict:
    bundle = json.loads(bundle_path.read_text())
    errors: list[str] = []
    signed_payload = dict(bundle)
    expected_bundle_id = signed_payload.pop("bundle_id", None)
    if expected_bundle_id != _digest(signed_payload):
        errors.append("bundle_id_invalid")
    try:
        if _git_head(repo_root) != bundle.get("git_head"):
            errors.append("git_head_changed")
    except (OSError, subprocess.CalledProcessError) as exc:
        errors.append(f"git_head_unavailable:{exc}")

    for relative_path, expected in bundle.get("files", {}).items():
        path = _repo_path(repo_root, relative_path)
        if not path.is_file():
            errors.append(f"missing:{relative_path}")
            continue
        actual = _file_record(repo_root, relative_path)
        if actual != expected:
            errors.append(f"changed:{relative_path}")

    manifest_path = _repo_path(repo_root, bundle["criteria_manifest"])
    try:
        _, digest = load_criteria_manifest(manifest_path)
        if digest != bundle.get("criteria_manifest_digest"):
            errors.append("criteria_manifest_digest_changed")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors.append(f"invalid_criteria_manifest:{exc}")

    return {
        "status": "accepted" if not errors else "rejected",
        "bundle_id": bundle.get("bundle_id"),
        "criteria_manifest_digest": bundle.get("criteria_manifest_digest"),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    freeze_parser = subparsers.add_parser("freeze")
    freeze_parser.add_argument("--repo-root", type=Path, required=True)
    freeze_parser.add_argument("--output", type=Path, required=True)
    freeze_parser.add_argument("--feature-name", required=True)
    freeze_parser.add_argument("--phase", required=True)
    freeze_parser.add_argument("--iteration", type=int, required=True)
    freeze_parser.add_argument("--criteria-manifest", type=Path, required=True)
    freeze_parser.add_argument("--scope", type=Path)
    freeze_parser.add_argument("--include", action="append", default=[])

    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--repo-root", type=Path, required=True)
    verify_parser.add_argument("--bundle", type=Path, required=True)

    args = parser.parse_args()
    if args.command == "freeze":
        result = freeze(
            args.repo_root,
            args.output,
            args.feature_name,
            args.phase,
            args.iteration,
            args.criteria_manifest,
            args.scope,
            args.include,
        )
    else:
        result = verify_bundle_file(args.bundle, args.repo_root)
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("status") == "accepted" or args.command == "freeze" else 1


if __name__ == "__main__":
    raise SystemExit(main())
