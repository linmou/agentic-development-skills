#!/usr/bin/env python3
"""Enforce a TDD phase against a Git-backed dynamic scope artifact."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

PHASES = ("red", "green", "refactor", "test_refactor", "docs")
KINDS = {"test", "doc", "prod"}
DOC_SUFFIXES = {".md", ".rst", ".txt"}
TEST_MARKERS = ("/tests/", "/__tests__/", ".test.", ".spec.")
DOC_MARKERS = ("/docs/",)


class ScopeError(ValueError):
    """Raised when a scope artifact or repository path is unsafe."""


def _repo_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise ScopeError("Git repository is required")
    return Path(result.stdout.strip()).resolve()


def normalize(path: str) -> str:
    """Return a validated repository-relative POSIX path."""
    if (
        not isinstance(path, str)
        or not path
        or "\\" in path
        or (len(path) > 1 and path[1] == ":")
        or "//" in path
        or path.startswith("./")
        or path.endswith("/")
        or any(ord(char) < 32 for char in path)
    ):
        raise ScopeError(f"invalid repository path: {path!r}")
    candidate = PurePosixPath(path)
    if candidate.is_absolute() or any(part in {"", ".", ".."} for part in candidate.parts):
        raise ScopeError(f"invalid repository path: {path!r}")
    return candidate.as_posix()


def normalize_git_path(path: str) -> str:
    """Normalize a path emitted by Git without rejecting valid filename bytes."""
    if not isinstance(path, str) or not path or "\0" in path:
        raise ScopeError(f"invalid Git path: {path!r}")
    candidate = PurePosixPath(path)
    if candidate.is_absolute() or any(part in {"", ".", ".."} for part in candidate.parts):
        raise ScopeError(f"invalid Git path: {path!r}")
    return candidate.as_posix()


def normalize_pattern(pattern: str) -> str:
    if not isinstance(pattern, str) or not pattern:
        raise ScopeError(f"invalid scope pattern: {pattern!r}")
    if pattern.endswith("/**"):
        stem = pattern[:-3]
        if not stem:
            raise ScopeError(f"invalid scope pattern: {pattern!r}")
        if any(char in stem for char in "*?[]"):
            raise ScopeError(f"scope patterns must be exact paths or terminal /**: {pattern!r}")
        return normalize(stem) + "/**"
    if "*" in pattern or "?" in pattern or "[" in pattern or "]" in pattern:
        raise ScopeError(f"scope patterns must be exact paths or terminal /**: {pattern!r}")
    return normalize(pattern)


def pattern_matches(path: str, pattern: str) -> bool:
    path = normalize_git_path(path)
    pattern = normalize_pattern(pattern)
    if pattern.endswith("/**"):
        stem = pattern[:-3]
        return path == stem or path.startswith(stem + "/")
    return path == pattern


def lexical_classify(path: str) -> tuple[str, bool]:
    """Return the default kind and whether the lexical result is ambiguous."""
    path = normalize_git_path(path)
    normalized = "/" + path
    suffix = PurePosixPath(path).suffix
    is_root_test_tree = path.startswith(("tests/", "__tests__/"))
    has_test_marker = path.endswith(".feature") or any(marker in normalized for marker in TEST_MARKERS)
    has_doc_marker = suffix in DOC_SUFFIXES or any(marker in normalized for marker in DOC_MARKERS)
    # A runtime-looking file nested below a marker is a semantic collision.
    ambiguous = ("/tests/" in normalized or "/__tests__/" in normalized) and not is_root_test_tree and not (
        ".test." in path or ".spec." in path or path.endswith(".feature")
    )
    ambiguous = ambiguous or ("/docs/" in normalized and suffix not in DOC_SUFFIXES)
    if has_test_marker:
        return "test", ambiguous
    if has_doc_marker:
        return "doc", ambiguous
    return "prod", False


def classify(path: str, semantic_overrides: dict[str, str] | None = None) -> str:
    """Classify a path, raising when a semantic collision has no override."""
    normalized = normalize_git_path(path)
    overrides = semantic_overrides or {}
    matching_kinds = {kind for pattern, kind in overrides.items() if pattern_matches(normalized, pattern)}
    if len(matching_kinds) > 1:
        raise ScopeError(f"conflicting semantic overrides match: {normalized}")
    if matching_kinds:
        return matching_kinds.pop()
    kind, ambiguous = lexical_classify(normalized)
    if ambiguous:
        raise ScopeError(f"ambiguous semantic classification requires an override: {normalized}")
    return kind


def reason_for_phase(phase: str) -> str:
    if phase == "red":
        return "red may edit tests and docs only"
    if phase == "green":
        return "green may edit production files only; tests are red-phase only"
    if phase == "refactor":
        return "refactor may edit production files only; tests and docs belong to other phases"
    if phase == "test_refactor":
        return "test refactor may edit explicitly editable test files only"
    return "docs may edit explicitly editable documentation files only"


def is_allowed(phase: str, kind: str) -> bool:
    if phase == "red":
        return kind in {"test", "doc"}
    if phase in {"green", "refactor"}:
        return kind == "prod"
    if phase == "test_refactor":
        return kind == "test"
    return kind == "doc"


def _git(
    *args: str,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], check=False, capture_output=True, text=True, cwd=cwd, env=env)


def _scope_identity(scope_path: Path, repo: Path) -> tuple[Path, str]:
    candidate = scope_path if scope_path.is_absolute() else repo / scope_path
    candidate = candidate.absolute()
    try:
        relative = candidate.relative_to(repo)
    except ValueError as exc:
        raise ScopeError("scope artifact must be inside the Git repository") from exc
    current = repo
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise ScopeError("scope artifact path must not contain a symlink")
    return candidate, normalize(relative.as_posix())


def _parse_name_status(raw: bytes) -> list[str]:
    tokens = raw.split(b"\0")
    paths: list[str] = []
    index = 0
    while index < len(tokens):
        status = tokens[index].decode(errors="replace")
        index += 1
        if not status:
            continue
        if index >= len(tokens):
            raise ScopeError("malformed Git name-status output")
        paths.append(normalize_git_path(tokens[index].decode(errors="surrogateescape")))
        index += 1
        if status[0] in {"R", "C"}:
            if index >= len(tokens):
                raise ScopeError("malformed Git rename output")
            paths.append(normalize_git_path(tokens[index].decode(errors="surrogateescape")))
            index += 1
    return paths


def _changed_paths(baseline_ref: str, scope_relative: str, repo: Path) -> list[str]:
    verify = _git("rev-parse", "--verify", f"{baseline_ref}^{{commit}}", cwd=repo)
    if verify.returncode != 0:
        raise ScopeError(f"baseline ref does not resolve to a commit: {baseline_ref}")
    index_dir = Path(tempfile.mkdtemp(prefix="tdd-phase-guard-index-"))
    try:
        env = os.environ.copy()
        env["GIT_INDEX_FILE"] = str(index_dir / "index")
        read_tree = _git("read-tree", baseline_ref, cwd=repo, env=env)
        if read_tree.returncode != 0:
            raise ScopeError(read_tree.stderr.strip() or "unable to initialise comparison index")
        add = _git("add", "-A", "--", ".", cwd=repo, env=env)
        if add.returncode != 0:
            raise ScopeError(add.stderr.strip() or "unable to stage current worktree")
        diff = subprocess.run(
            ["git", "diff", "--cached", "--name-status", "--find-renames", "-z", baseline_ref, "--"],
            check=False,
            capture_output=True,
            cwd=repo,
            env=env,
        )
        if diff.returncode != 0:
            raise ScopeError(diff.stderr.decode(errors="replace").strip() or "unable to inspect Git changes")
        paths = _parse_name_status(diff.stdout)
    finally:
        shutil.rmtree(index_dir, ignore_errors=True)
    return sorted({path for path in paths if path != scope_relative})


def _patterns_overlap(left: str, right: str) -> bool:
    left_tree = left.endswith("/**")
    right_tree = right.endswith("/**")
    if not left_tree and not right_tree:
        return left == right
    if left_tree and right_tree:
        left_stem = left[:-3]
        right_stem = right[:-3]
        return left_stem == right_stem or left_stem.startswith(right_stem + "/") or right_stem.startswith(
            left_stem + "/"
        )
    if left_tree:
        return pattern_matches(right, left)
    return pattern_matches(left, right)


def _load_scope(scope_path: Path, phase: str, repo: Path) -> tuple[dict[str, Any], str]:
    scope_file, scope_relative = _scope_identity(scope_path, repo)
    try:
        raw = scope_file.read_bytes()
    except OSError as exc:
        raise ScopeError(f"invalid scope artifact: {exc}") from exc
    try:
        provisional = json.loads(raw)
    except json.JSONDecodeError:
        provisional = None
    baseline_ref = provisional.get("baseline_ref") if isinstance(provisional, dict) else None
    if not isinstance(baseline_ref, str) or not baseline_ref.strip() or baseline_ref.startswith("-"):
        if provisional is not None:
            raise ScopeError("scope baseline_ref must be a non-empty safe string")
        baseline_ref = "HEAD"
    baseline = subprocess.run(
        ["git", "show", f"{baseline_ref}:{scope_relative}"],
        check=False,
        capture_output=True,
        cwd=repo,
    )
    if baseline.returncode != 0:
        raise ScopeError("scope artifact is missing from baseline_ref")
    if baseline.stdout != raw:
        raise ScopeError("scope artifact differs from immutable baseline copy")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ScopeError(f"invalid scope artifact: {exc}") from exc
    if not isinstance(payload, dict):
        raise ScopeError("scope artifact must be a JSON object")
    if type(payload.get("schema")) is not int or payload["schema"] != 1:
        raise ScopeError("unsupported or missing scope schema")
    if payload.get("phase") != phase:
        raise ScopeError("scope artifact phase does not match --phase")
    if not isinstance(payload.get("feature"), str) or not payload["feature"].strip():
        raise ScopeError("scope feature must be a non-empty string")
    if not isinstance(payload.get("baseline_ref"), str) or not payload["baseline_ref"].strip():
        raise ScopeError("scope baseline_ref must be a non-empty safe string")
    if any(ord(char) < 32 for char in payload["baseline_ref"]):
        raise ScopeError("scope baseline_ref contains control characters")
    if not isinstance(payload.get("protected"), list):
        raise ScopeError("scope protected must be a list")
    if phase in {"test_refactor", "docs"} and "editable" not in payload:
        raise ScopeError(f"scope editable list is required for {phase}")
    if "editable" in payload and not isinstance(payload["editable"], list):
        raise ScopeError("scope editable must be a list")
    overrides = payload.get("semantic_overrides", {})
    if not isinstance(overrides, dict):
        raise ScopeError("scope semantic_overrides must be an object")
    normalized_overrides: dict[str, str] = {}
    for key, value in overrides.items():
        normalized_key = normalize_pattern(key)
        if not isinstance(value, str) or value not in KINDS:
            raise ScopeError(f"invalid semantic override for {key!r}")
        normalized_overrides[normalized_key] = value
    override_items = list(normalized_overrides.items())
    for index, (left_pattern, left_kind) in enumerate(override_items):
        for right_pattern, right_kind in override_items[index + 1 :]:
            if left_kind != right_kind and _patterns_overlap(left_pattern, right_pattern):
                raise ScopeError(
                    f"conflicting semantic override patterns: {left_pattern!r} and {right_pattern!r}"
                )
    payload["protected"] = [normalize_pattern(item) for item in payload["protected"]]
    payload["editable"] = [normalize_pattern(item) for item in payload.get("editable", [])]
    payload["semantic_overrides"] = normalized_overrides
    return payload, scope_relative


def evaluate(phase: str, scope_path: str | Path, *, repo: Path | None = None) -> dict[str, object]:
    try:
        repo_path = (repo or _repo_root()).resolve()
        scope = Path(scope_path)
        if not scope.is_absolute():
            scope = repo_path / scope
        payload, scope_relative = _load_scope(scope, phase, repo_path)
        changed = _changed_paths(payload["baseline_ref"], scope_relative, repo_path)
        classified: list[dict[str, str]] = []
        disallowed: list[str] = []
        ambiguous: list[str] = []
        protected: list[str] = []
        editable_violations: list[str] = []
        for path in changed:
            try:
                kind = classify(path, payload["semantic_overrides"])
            except ScopeError as exc:
                ambiguous.append(path)
                disallowed.append(path)
                classified.append({"path": path, "kind": "ambiguous", "error": str(exc)})
                continue
            classified.append({"path": path, "kind": kind})
            if not is_allowed(phase, kind):
                disallowed.append(path)
            if any(pattern_matches(path, pattern) for pattern in payload["protected"]):
                protected.append(path)
                disallowed.append(path)
            if (phase in {"test_refactor", "docs"} or payload["editable"]) and not any(
                pattern_matches(path, pattern) for pattern in payload["editable"]
            ):
                editable_violations.append(path)
                disallowed.append(path)
        disallowed = sorted(set(disallowed))
        status = "pass" if not disallowed and not ambiguous else "fail"
        return {
            "phase": phase,
            "status": status,
            "reason": reason_for_phase(phase),
            "feature": payload["feature"],
            "baseline_ref": payload["baseline_ref"],
            "changed_paths": changed,
            "changed_files": classified,
            "protected_files": protected,
            "editable_violations": editable_violations,
            "ambiguous_files": ambiguous,
            "disallowed_files": disallowed,
        }
    except ScopeError as exc:
        return {
            "phase": phase,
            "status": "fail",
            "reason": str(exc),
            "changed_paths": [],
            "changed_files": [],
            "disallowed_files": [],
            "errors": [str(exc)],
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=PHASES, required=True)
    parser.add_argument("--scope", required=True, help="JSON scope artifact")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = evaluate(args.phase, args.scope)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
