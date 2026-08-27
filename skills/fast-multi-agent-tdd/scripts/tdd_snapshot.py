#!/usr/bin/env python3
"""Capture, replay, and clean immutable Git snapshots for TDD phases."""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import tempfile
from collections.abc import Sequence
from pathlib import Path

REF_ROOT = "refs/codex/tdd"


class SnapshotError(RuntimeError):
    """Raised when Git cannot create or replay a snapshot."""


def _run(repo: Path, args: Sequence[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=repo, env=env, text=True, capture_output=True, check=False)


def _repo_root(repo: Path | None) -> Path:
    candidate = (repo or Path.cwd()).resolve()
    result = _run(candidate, ["rev-parse", "--show-toplevel"])
    if result.returncode != 0:
        raise SnapshotError("Git repository is required")
    return Path(result.stdout.strip()).resolve()


def _slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._")
    if not slug:
        raise SnapshotError("feature and phase names must contain a safe character")
    return slug


def snapshot_ref(feature: str, phase: str) -> str:
    return f"{REF_ROOT}/{_slug(feature)}/{_slug(phase)}"


def create_snapshot(feature: str, phase: str, *, repo: Path | None = None) -> dict[str, object]:
    """Commit the complete worktree state into a temporary phase ref."""
    root = _repo_root(repo)
    ref = snapshot_ref(feature, phase)
    existing = _run(root, ["show-ref", "--verify", "--quiet", ref])
    if existing.returncode == 0:
        raise SnapshotError(f"snapshot ref already exists: {ref}")
    if existing.returncode not in {0, 1}:
        raise SnapshotError(existing.stderr.strip() or f"unable to inspect snapshot ref: {ref}")
    head = _run(root, ["rev-parse", "HEAD"])
    if head.returncode != 0:
        raise SnapshotError("snapshot requires an existing commit")
    index_dir = Path(tempfile.mkdtemp(prefix="codex-tdd-index-"))
    index_path = index_dir / "index"
    try:
        env = os.environ.copy()
        env["GIT_INDEX_FILE"] = str(index_path)
        read_tree = _run(root, ["read-tree", "HEAD"], env=env)
        if read_tree.returncode != 0:
            raise SnapshotError(read_tree.stderr.strip() or "unable to initialise temporary index")
        add = _run(root, ["add", "-A", "-f"], env=env)
        if add.returncode != 0:
            raise SnapshotError(add.stderr.strip() or "unable to stage worktree in temporary index")
        tree = _run(root, ["write-tree"], env=env)
        if tree.returncode != 0:
            raise SnapshotError(tree.stderr.strip() or "unable to write snapshot tree")
        commit = subprocess.run(
            ["git", "commit-tree", tree.stdout.strip(), "-p", head.stdout.strip(), "-m", f"TDD snapshot {feature}/{phase}"],
            cwd=root,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        if commit.returncode != 0:
            raise SnapshotError(commit.stderr.strip() or "unable to create snapshot commit")
        update = _run(root, ["update-ref", ref, commit.stdout.strip(), "0" * 40])
        if update.returncode != 0:
            raise SnapshotError(update.stderr.strip() or "unable to publish snapshot ref")
        return {"feature": feature, "phase": phase, "ref": ref, "commit": commit.stdout.strip()}
    finally:
        shutil.rmtree(index_dir, ignore_errors=True)


def replay_snapshot(
    ref: str,
    command: Sequence[str],
    *,
    repo: Path | None = None,
    test_id: str | None = None,
    failure_classification: str | None = None,
    preserve_worktree: bool = False,
    feature: str | None = None,
) -> dict[str, object]:
    """Run a command in a detached temporary worktree at ``ref``."""
    root = _repo_root(repo)
    verify = _run(root, ["rev-parse", "--verify", f"{ref}^{{commit}}"])
    if verify.returncode != 0:
        raise SnapshotError(f"snapshot ref does not resolve to a commit: {ref}")
    if isinstance(command, str):
        command = shlex.split(command)
    if not command:
        raise SnapshotError("replay requires a command")
    prefix = "codex-tdd-replay-"
    if feature:
        prefix += f"{_slug(feature)}-"
    worktree = Path(tempfile.mkdtemp(prefix=prefix))
    shutil.rmtree(worktree)
    try:
        add = _run(root, ["worktree", "add", "--detach", "--quiet", str(worktree), ref])
        if add.returncode != 0:
            raise SnapshotError(add.stderr.strip() or "unable to create replay worktree")
        replay_env = os.environ.copy()
        replay_env.pop("GIT_INDEX_FILE", None)
        run = subprocess.run(
            command,
            cwd=worktree,
            env=replay_env,
            text=True,
            capture_output=True,
            check=False,
        )
        stable_id = test_id or next((part for part in command if "::" in part), "")
        classification = failure_classification or ("passed" if run.returncode == 0 else "nonzero_exit")
        payload: dict[str, object] = {
            "ref": ref,
            "worktree": str(worktree),
            "returncode": run.returncode,
            "stdout": run.stdout,
            "stderr": run.stderr,
            "test_id": stable_id,
            "failure_classification": classification,
            "preserved": preserve_worktree,
        }
        return payload
    finally:
        if not preserve_worktree:
            _run(root, ["worktree", "remove", "--force", str(worktree)])
            shutil.rmtree(worktree, ignore_errors=True)


def cleanup_snapshots(feature: str, *, repo: Path | None = None) -> dict[str, object]:
    """Delete phase refs for a feature after successful terminal closeout."""
    root = _repo_root(repo)
    prefix = f"{REF_ROOT}/{_slug(feature)}/"
    refs = _run(root, ["for-each-ref", "--format=%(refname)", prefix])
    if refs.returncode != 0:
        raise SnapshotError(refs.stderr.strip() or "unable to list snapshot refs")
    removed: list[str] = []
    for ref in refs.stdout.splitlines():
        if ref:
            result = _run(root, ["update-ref", "-d", ref])
            if result.returncode != 0:
                raise SnapshotError(result.stderr.strip() or f"unable to remove {ref}")
            removed.append(ref)
    worktrees = _run(root, ["worktree", "list", "--porcelain"])
    prefix_name = f"codex-tdd-replay-{_slug(feature)}-"
    removed_worktrees: list[str] = []
    if worktrees.returncode == 0:
        for line in worktrees.stdout.splitlines():
            if not line.startswith("worktree "):
                continue
            path = line.removeprefix("worktree ")
            if Path(path).name.startswith(prefix_name):
                result = _run(root, ["worktree", "remove", "--force", path])
                if result.returncode == 0:
                    removed_worktrees.append(path)
    return {"feature": feature, "removed_refs": removed, "removed_worktrees": removed_worktrees}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="operation", required=True)
    create = subparsers.add_parser("create")
    create.add_argument("--feature", required=True)
    create.add_argument("--phase", required=True)
    replay = subparsers.add_parser("replay")
    replay.add_argument("--ref", required=True)
    replay.add_argument("--test-id")
    replay.add_argument("--failure-classification")
    replay.add_argument("--feature")
    replay.add_argument("--preserve-worktree", action="store_true")
    replay.add_argument("command", nargs=argparse.REMAINDER)
    cleanup = subparsers.add_parser("cleanup")
    cleanup.add_argument("--feature", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload: dict[str, object]
    try:
        if args.operation == "create":
            payload = create_snapshot(args.feature, args.phase)
        elif args.operation == "replay":
            command = list(args.command)
            if command[:1] == ["--"]:
                command = command[1:]
            payload = replay_snapshot(
                args.ref,
                command,
                test_id=args.test_id,
                failure_classification=args.failure_classification,
                preserve_worktree=args.preserve_worktree,
                feature=args.feature,
            )
        else:
            payload = cleanup_snapshots(args.feature)
    except SnapshotError as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}))
        return 1
    print(json.dumps(payload, indent=2, sort_keys=True))
    returncode = payload.get("returncode")
    if args.operation == "replay" and isinstance(returncode, int) and returncode != 0:
        return returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
