#!/usr/bin/env python3
# Purpose: run one owning-phase command and recover only authenticated, command-caused scope violations.
"""Recover a narrow class of accidental TDD phase-state violations."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import TextIO

from phase_guard import ScopeError, _load_scope, _repo_root, evaluate

RECOVERABLE_CAUSE = "accidental_phase_write"
REGULAR_MODES = {"100644", "100755"}


class RecoveryError(RuntimeError):
    """Raised when provenance or scope is not strong enough for restoration."""


def _git(
    repo: Path,
    args: Sequence[str],
    *,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def _required_git(repo: Path, args: Sequence[str], *, env: dict[str, str] | None = None) -> str:
    result = _git(repo, args, env=env)
    if result.returncode != 0:
        raise RecoveryError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def _capture_worktree_tree(repo: Path, baseline_commit: str) -> str:
    """Store the current tracked worktree as a Git tree without touching the real index."""
    index_dir = Path(tempfile.mkdtemp(prefix="tdd-phase-recovery-index-"))
    try:
        env = os.environ.copy()
        env["GIT_INDEX_FILE"] = str(index_dir / "index")
        _required_git(repo, ["read-tree", baseline_commit], env=env)
        _required_git(repo, ["add", "-A", "--", "."], env=env)
        return _required_git(repo, ["write-tree"], env=env)
    finally:
        shutil.rmtree(index_dir, ignore_errors=True)


def _tree_entry(repo: Path, tree: str, path: str) -> dict[str, str] | None:
    result = subprocess.run(
        ["git", "ls-tree", "-z", tree, "--", path],
        cwd=repo,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RecoveryError(result.stderr.decode(errors="replace").strip() or "git ls-tree failed")
    records = [record for record in result.stdout.split(b"\0") if record]
    if not records:
        return None
    if len(records) != 1 or b"\t" not in records[0]:
        raise RecoveryError(f"ambiguous Git tree entry for {path!r}")
    metadata, raw_path = records[0].split(b"\t", 1)
    parts = metadata.decode("ascii").split()
    if len(parts) != 3 or raw_path.decode(errors="surrogateescape") != path:
        raise RecoveryError(f"malformed Git tree entry for {path!r}")
    return {"mode": parts[0], "type": parts[1], "object": parts[2]}


def _blob_evidence(repo: Path, entry: dict[str, str] | None) -> dict[str, object]:
    if entry is None:
        return {"state": "deleted", "entry": None, "content_base64": None}
    result = subprocess.run(
        ["git", "cat-file", "blob", entry["object"]],
        cwd=repo,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RecoveryError(result.stderr.decode(errors="replace").strip() or "git cat-file failed")
    return {
        "state": "present",
        "entry": entry,
        "content_base64": base64.b64encode(result.stdout).decode("ascii"),
        "content_sha256": _sha256_bytes(result.stdout),
    }


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _validate_receipt_path(receipt: Path, repo: Path) -> Path:
    resolved = receipt.resolve(strict=False)
    try:
        resolved.relative_to(repo)
    except ValueError:
        pass
    else:
        raise RecoveryError("recovery receipt must be outside the repository")
    if resolved.exists():
        raise RecoveryError("recovery receipt already exists")
    if not resolved.parent.is_dir():
        raise RecoveryError("recovery receipt parent directory does not exist")
    return resolved


def _write_event(handle: TextIO, payload: dict[str, object]) -> None:
    handle.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")
    handle.flush()
    os.fsync(handle.fileno())


def _non_recoverable(reason: str, *, child_returncode: int | None = None) -> tuple[dict[str, object], int]:
    payload: dict[str, object] = {
        "schema": 1,
        "status": "non_recoverable",
        "recovered": False,
        "reason": reason,
    }
    if child_returncode is not None:
        payload["child_returncode"] = child_returncode
    return payload, 2


def _recovery_candidates(
    *,
    repo: Path,
    baseline_commit: str,
    pre_tree: str,
    post_tree: str,
    guard: dict[str, object],
) -> list[dict[str, object]]:
    errors = guard.get("errors", [])
    ambiguous = guard.get("ambiguous_files", [])
    raw_paths = guard.get("disallowed_files", [])
    if errors:
        raise RecoveryError("scope authentication or structure failed")
    if ambiguous:
        raise RecoveryError("ambiguous semantic classification is not recoverable")
    if not isinstance(raw_paths, list) or not raw_paths:
        raise RecoveryError("guard failure has no exact disallowed path set")

    candidates: list[dict[str, object]] = []
    for raw_path in raw_paths:
        if not isinstance(raw_path, str):
            raise RecoveryError("guard returned a non-string path")
        if raw_path == "audits" or raw_path.startswith("audits/"):
            raise RecoveryError("reviewer and audit artifacts are never auto-recoverable")
        baseline = _tree_entry(repo, baseline_commit, raw_path)
        before = _tree_entry(repo, pre_tree, raw_path)
        after = _tree_entry(repo, post_tree, raw_path)
        if baseline is None:
            raise RecoveryError(f"untracked or renamed path has ambiguous provenance: {raw_path}")
        if baseline != before:
            raise RecoveryError(f"path did not match the authenticated baseline before the command: {raw_path}")
        if baseline["type"] != "blob" or baseline["mode"] not in REGULAR_MODES:
            raise RecoveryError(f"non-regular baseline path is not recoverable: {raw_path}")
        if after is not None and (after["type"] != "blob" or after["mode"] not in REGULAR_MODES):
            raise RecoveryError(f"non-regular replacement is not recoverable: {raw_path}")
        candidates.append(
            {
                "path": raw_path,
                "baseline": baseline,
                "violating": _blob_evidence(repo, after),
            }
        )
    return candidates


def run_recovery(
    *,
    phase: str,
    scope_path: Path,
    receipt_path: Path,
    cause: str,
    command: Sequence[str],
    repo: Path | None = None,
) -> tuple[dict[str, object], int]:
    """Run ``command`` and recover only a proven, wrong-phase tracked-file delta."""
    if cause != RECOVERABLE_CAUSE:
        return _non_recoverable("semantic or unspecified causes are not recoverable")
    if not command:
        return _non_recoverable("recovery command is required")

    try:
        root = (repo or _repo_root()).resolve()
        receipt = _validate_receipt_path(receipt_path, root)
        scope_file = scope_path if scope_path.is_absolute() else root / scope_path
        scope, scope_relative = _load_scope(scope_file, phase, root)
        baseline_ref = str(scope["baseline_ref"])
        baseline_commit = _required_git(root, ["rev-parse", "--verify", f"{baseline_ref}^{{commit}}"])
        initial_guard = evaluate(phase, scope_file, repo=root)
        if initial_guard["status"] != "pass":
            return _non_recoverable("phase state was already invalid before the command")

        pre_tree = _capture_worktree_tree(root, baseline_commit)
        pre_index_tree = _required_git(root, ["write-tree"])
        child = subprocess.run(command, cwd=root, capture_output=True, check=False)
        post_guard = evaluate(phase, scope_file, repo=root)
        if post_guard["status"] == "pass":
            payload: dict[str, object] = {
                "schema": 1,
                "status": "pass" if child.returncode == 0 else "command_failed",
                "recovered": False,
                "child_returncode": child.returncode,
                "guard_status": "pass",
            }
            return payload, child.returncode

        post_index_tree = _required_git(root, ["write-tree"])
        if post_index_tree != pre_index_tree:
            return _non_recoverable("the command changed the real Git index", child_returncode=child.returncode)
        post_tree = _capture_worktree_tree(root, baseline_commit)
        candidates = _recovery_candidates(
            repo=root,
            baseline_commit=baseline_commit,
            pre_tree=pre_tree,
            post_tree=post_tree,
            guard=post_guard,
        )
        scope_bytes = scope_file.read_bytes()
        command_bytes = json.dumps(list(command), separators=(",", ":")).encode()
        planned = {
            "schema": 1,
            "event": "recovery_planned",
            "feature": scope["feature"],
            "phase": phase,
            "cause": cause,
            "scope_path": scope_relative,
            "scope_sha256": _sha256_bytes(scope_bytes),
            "baseline_ref": baseline_ref,
            "baseline_commit": baseline_commit,
            "pre_worktree_tree": pre_tree,
            "post_worktree_tree": post_tree,
            "index_tree": pre_index_tree,
            "command_sha256": _sha256_bytes(command_bytes),
            "child_returncode": child.returncode,
            "child_stdout_sha256": _sha256_bytes(child.stdout),
            "child_stderr_sha256": _sha256_bytes(child.stderr),
            "paths": candidates,
        }

        with receipt.open("x", encoding="utf-8") as handle:
            _write_event(handle, planned)
            if _required_git(root, ["write-tree"]) != pre_index_tree:
                raise RecoveryError("Git index drifted after recovery planning")
            if _capture_worktree_tree(root, baseline_commit) != post_tree:
                raise RecoveryError("worktree drifted after recovery planning")
            paths = [str(item["path"]) for item in candidates]
            restore = _git(root, ["restore", f"--source={baseline_commit}", "--worktree", "--", *paths])
            if restore.returncode != 0:
                _write_event(
                    handle,
                    {"schema": 1, "event": "recovery_failed", "reason": restore.stderr.strip()},
                )
                raise RecoveryError(restore.stderr.strip() or "Git restore failed")
            final_guard = evaluate(phase, scope_file, repo=root)
            if final_guard["status"] != "pass":
                _write_event(
                    handle,
                    {"schema": 1, "event": "recovery_failed", "reason": "final guard failed"},
                )
                raise RecoveryError("phase guard still fails after bounded restoration")
            status = "recovered" if child.returncode == 0 else "recovered_command_failed"
            completed = {
                "schema": 1,
                "event": "recovery_completed",
                "status": status,
                "restored_paths": paths,
                "final_guard_status": "pass",
            }
            _write_event(handle, completed)
        payload = {
            "schema": 1,
            "status": status,
            "recovered": True,
            "child_returncode": child.returncode,
            "guard_status": "pass",
            "receipt": str(receipt),
            "restored_paths": paths,
        }
        return payload, child.returncode
    except (OSError, ScopeError, RecoveryError) as exc:
        return _non_recoverable(str(exc))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", required=True)
    parser.add_argument("--scope", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--cause", required=True, choices=(RECOVERABLE_CAUSE,))
    parser.add_argument("command", nargs=argparse.REMAINDER)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    command = list(args.command)
    if command[:1] == ["--"]:
        command = command[1:]
    payload, returncode = run_recovery(
        phase=str(args.phase),
        scope_path=args.scope,
        receipt_path=args.receipt,
        cause=str(args.cause),
        command=command,
    )
    print(json.dumps(payload, sort_keys=True))
    return returncode


if __name__ == "__main__":
    raise SystemExit(main())
