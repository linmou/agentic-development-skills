#!/usr/bin/env python3
"""Capture, replay, and clean immutable Git snapshots for TDD phases."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import tempfile
from collections.abc import Sequence
from pathlib import Path

REF_ROOT = "refs/tdd"


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


def _snapshot_phase(phase: str, round_number: int | None) -> str:
    if round_number is None:
        return phase
    if phase != "pre_red":
        raise SnapshotError("--round is only valid with --phase pre_red")
    if round_number < 1:
        raise SnapshotError("--round must be a positive integer")
    if round_number == 1:
        return phase
    return f"pre_red_round_{round_number}"


def _is_nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_role_receipt(path: Path, feature: str, phase: str) -> dict[str, object]:
    try:
        receipt = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise SnapshotError(f"invalid role receipt: {exc}") from exc
    if not isinstance(receipt, dict):
        raise SnapshotError("role receipt must be a JSON object")
    if type(receipt.get("schema")) is not int or receipt["schema"] != 2:
        raise SnapshotError("role receipt schema must be 2")
    if receipt.get("feature") != feature:
        raise SnapshotError("role receipt feature does not match --feature")
    if receipt.get("route") not in {"compact", "full"}:
        raise SnapshotError("role receipt route must be compact or full")
    monitor_agent_id = receipt.get("monitor_agent_id")
    if not _is_nonempty_string(monitor_agent_id):
        raise SnapshotError("role receipt monitor_agent_id must be a nonempty stable identity")
    if not _is_nonempty_string(receipt.get("monitor_source")):
        raise SnapshotError("role receipt monitor_source must name the delegation mechanism")
    if phase == "pre_red":
        return receipt
    reviewer_ids = receipt.get("red_reviewer_agent_ids")
    if (
        not isinstance(reviewer_ids, list)
        or not reviewer_ids
        or any(not _is_nonempty_string(agent_id) for agent_id in reviewer_ids)
        or len(set(reviewer_ids)) != len(reviewer_ids)
        or monitor_agent_id in reviewer_ids
    ):
        raise SnapshotError(
            "role receipt red_reviewer_agent_ids must be nonempty, distinct identities "
            "separate from the monitor"
        )
    if not _is_nonempty_string(receipt.get("reviewer_source")):
        raise SnapshotError("role receipt reviewer_source must name the delegation mechanism")
    return receipt


def _sha256(path: Path, label: str) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise SnapshotError(f"unable to read {label}: {path}") from exc


def _repo_file(root: Path, path: Path, label: str) -> tuple[Path, str]:
    resolved = path.resolve()
    try:
        relative = resolved.relative_to(root).as_posix()
    except ValueError as exc:
        raise SnapshotError(f"{label} must be inside the repository: {resolved}") from exc
    return resolved, relative


def _staged_sha256(root: Path, path: Path, env: dict[str, str]) -> str:
    _, relative = _repo_file(root, path, "provenance-bound file")
    result = subprocess.run(
        ["git", "show", f":{relative}"],
        cwd=root,
        env=env,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise SnapshotError(f"provenance-bound file is absent from the snapshot: {relative}")
    return hashlib.sha256(result.stdout).hexdigest()


def _validate_provenance(
    path: Path,
    roles: Path,
    receipt: dict[str, object],
    feature: str,
    expected_iteration: int,
    root: Path,
) -> dict[Path, str]:
    try:
        provenance = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise SnapshotError(f"invalid provenance artifact: {exc}") from exc
    if not isinstance(provenance, dict):
        raise SnapshotError("provenance artifact must be a JSON object")
    expected_metadata = {
        "schema": 1,
        "decision": "provenance_valid",
        "feature": feature,
        "phase": "red",
        "monitor_agent_id": receipt["monitor_agent_id"],
        "monitor_source": receipt["monitor_source"],
        "role_receipt_path": str(roles.resolve()),
        "role_receipt_sha256": _sha256(roles, "role receipt"),
    }
    if any(provenance.get(field) != expected for field, expected in expected_metadata.items()):
        raise SnapshotError("provenance artifact does not match the current role receipt")
    iteration = provenance.get("iteration")
    if iteration != expected_iteration:
        raise SnapshotError(
            f"provenance review iteration must be {expected_iteration}, got {iteration!r}"
        )
    reviewers = provenance.get("reviewers")
    reviewer_ids = receipt["red_reviewer_agent_ids"]
    if not isinstance(reviewers, list) or not isinstance(reviewer_ids, list):
        raise SnapshotError("provenance artifact must contain receipt-bound reviewers")
    if len(reviewers) != len(reviewer_ids):
        raise SnapshotError("provenance reviewer count does not match the role receipt")
    reviewer_source = receipt["reviewer_source"]
    role_path, _ = _repo_file(root, roles, "role receipt")
    provenance_path, _ = _repo_file(root, path, "provenance artifact")
    bound_hashes = {
        role_path: _sha256(role_path, "role receipt"),
        provenance_path: _sha256(provenance_path, "provenance artifact"),
    }
    audit_directory: Path | None = None
    for index, (reviewer, reviewer_id) in enumerate(
        zip(reviewers, reviewer_ids, strict=True), start=1
    ):
        if not isinstance(reviewer, dict):
            raise SnapshotError("provenance reviewer entries must be JSON objects")
        audit_path_value = reviewer.get("audit_path")
        if (
            not isinstance(audit_path_value, str)
            or not audit_path_value.strip()
            or not Path(audit_path_value).is_absolute()
        ):
            raise SnapshotError("provenance audit_path must be an absolute path")
        audit_path, _ = _repo_file(root, Path(audit_path_value), "reviewer audit")
        expected_name = f"{feature}_red_audit{index}_iteration{expected_iteration}.json"
        if audit_path.name != expected_name:
            raise SnapshotError(f"provenance reviewer audit must be named {expected_name}")
        if audit_directory is None:
            audit_directory = audit_path.parent
        elif audit_path.parent != audit_directory:
            raise SnapshotError("provenance reviewer audits must share one directory")
        expected_reviewer = {
            "reviewer_id": f"audit{index}",
            "reviewer_agent_id": reviewer_id,
            "reviewer_source": reviewer_source,
            "audit_path": str(audit_path),
            "audit_sha256": _sha256(audit_path, "reviewer audit"),
        }
        if any(reviewer.get(field) != expected for field, expected in expected_reviewer.items()):
            raise SnapshotError("provenance audit_sha256 or reviewer ownership is stale")
        bound_hashes[audit_path] = expected_reviewer["audit_sha256"]
    assert audit_directory is not None
    iteration_pattern = re.compile(
        rf"^{re.escape(feature)}_red_audit[123]_iteration([1-9][0-9]*)\.json$"
    )
    try:
        candidates = list(audit_directory.iterdir())
    except OSError as exc:
        raise SnapshotError(f"unable to inspect reviewer audit directory: {audit_directory}") from exc
    recorded_iterations = {
        int(match.group(1))
        for candidate in candidates
        if (match := iteration_pattern.fullmatch(candidate.name)) is not None
    }
    if recorded_iterations and max(recorded_iterations) != expected_iteration:
        raise SnapshotError(
            f"review iteration {expected_iteration} is not latest; found {max(recorded_iterations)}"
        )
    return bound_hashes


def _validate_focused_provenance(
    path: Path,
    roles: Path,
    receipt: dict[str, object],
    feature: str,
    root: Path,
) -> dict[Path, str]:
    try:
        focused = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise SnapshotError(f"invalid focused provenance artifact: {exc}") from exc
    if not isinstance(focused, dict):
        raise SnapshotError("focused provenance artifact must be a JSON object")
    expected_metadata = {
        "schema": 1,
        "decision": "advance_green",
        "feature": feature,
        "phase": "red",
        "iteration": 2,
        "role_receipt_path": str(roles.resolve()),
        "role_receipt_sha256": _sha256(roles, "role receipt"),
    }
    if any(focused.get(field) != expected for field, expected in expected_metadata.items()):
        raise SnapshotError("focused provenance does not match the current role receipt")
    reviewer_id = focused.get("focused_reviewer_agent_id")
    reviewer_source = focused.get("reviewer_source")
    initial_reviewers = receipt["red_reviewer_agent_ids"]
    if (
        not _is_nonempty_string(reviewer_id)
        or not _is_nonempty_string(reviewer_source)
        or not isinstance(initial_reviewers, list)
        or reviewer_id == receipt["monitor_agent_id"]
        or reviewer_id in initial_reviewers
    ):
        raise SnapshotError("focused provenance requires a new independent reviewer identity")
    focused_path, _ = _repo_file(root, path, "focused provenance artifact")
    bound_hashes = {
        focused_path: _sha256(focused_path, "focused provenance artifact"),
    }
    file_contracts = (
        (
            "focused_audit_path",
            "focused_audit_sha256",
            f"{feature}_red_focused_iteration2.json",
            "focused reviewer audit",
        ),
        ("eligibility_path", "eligibility_sha256", None, "focused eligibility artifact"),
    )
    for path_field, hash_field, expected_name, label in file_contracts:
        path_value = focused.get(path_field)
        if not isinstance(path_value, str) or not path_value.strip() or not Path(path_value).is_absolute():
            raise SnapshotError(f"focused provenance {path_field} must be an absolute path")
        bound_path, _ = _repo_file(root, Path(path_value), label)
        if expected_name is not None and bound_path.name != expected_name:
            raise SnapshotError(f"focused reviewer audit must be named {expected_name}")
        current_hash = _sha256(bound_path, label)
        if focused.get(hash_field) != current_hash:
            raise SnapshotError(f"focused provenance {hash_field} is stale")
        bound_hashes[bound_path] = current_hash
    return bound_hashes


def create_snapshot(
    feature: str,
    phase: str,
    roles: Path,
    provenance: Path | None,
    review_iteration: int | None,
    focused_provenance: Path | None,
    *,
    round_number: int | None = None,
    repo: Path | None = None,
) -> dict[str, object]:
    """Snapshot tracked and non-ignored worktree files without changing staging."""
    resolved_phase = _snapshot_phase(phase, round_number)
    root = _repo_root(repo)
    receipt = _validate_role_receipt(roles, feature, resolved_phase)
    role_path, _ = _repo_file(root, roles, "role receipt")
    bound_hashes = {role_path: _sha256(role_path, "role receipt")}
    if resolved_phase != "pre_red":
        if provenance is None:
            raise SnapshotError("post-Red snapshots require --provenance")
        if review_iteration is None or review_iteration < 1:
            raise SnapshotError("post-Red snapshots require a positive --review-iteration")
        if round_number is not None and review_iteration != round_number - 1:
            raise SnapshotError(
                f"round {round_number} requires review iteration {round_number - 1}"
            )
        if focused_provenance is None:
            bound_hashes = _validate_provenance(
                provenance,
                roles,
                receipt,
                feature,
                review_iteration,
                root,
            )
        else:
            if resolved_phase != "pre_green" or review_iteration != 2:
                raise SnapshotError(
                    "--focused-provenance is valid only for pre_green review iteration 2"
                )
            bound_hashes = _validate_provenance(
                provenance,
                roles,
                receipt,
                feature,
                1,
                root,
            )
            bound_hashes.update(
                _validate_focused_provenance(
                    focused_provenance,
                    roles,
                    receipt,
                    feature,
                    root,
                )
            )
    ref = snapshot_ref(feature, resolved_phase)
    existing = _run(root, ["show-ref", "--verify", "--quiet", ref])
    if existing.returncode == 0:
        raise SnapshotError(f"snapshot ref already exists: {ref}")
    if existing.returncode not in {0, 1}:
        raise SnapshotError(existing.stderr.strip() or f"unable to inspect snapshot ref: {ref}")
    head = _run(root, ["rev-parse", "HEAD"])
    if head.returncode != 0:
        raise SnapshotError("snapshot requires an existing commit")
    index_dir = Path(tempfile.mkdtemp(prefix="tdd-snapshot-index-"))
    index_path = index_dir / "index"
    try:
        env = os.environ.copy()
        env["GIT_INDEX_FILE"] = str(index_path)
        read_tree = _run(root, ["read-tree", "HEAD"], env=env)
        if read_tree.returncode != 0:
            raise SnapshotError(read_tree.stderr.strip() or "unable to initialise temporary index")
        add = _run(root, ["add", "-A"], env=env)
        if add.returncode != 0:
            raise SnapshotError(add.stderr.strip() or "unable to stage worktree in temporary index")
        for path, expected_hash in bound_hashes.items():
            if _staged_sha256(root, path, env) != expected_hash:
                raise SnapshotError(
                    f"provenance-bound file changed before snapshot publication: {path}"
                )
        tree = _run(root, ["write-tree"], env=env)
        if tree.returncode != 0:
            raise SnapshotError(tree.stderr.strip() or "unable to write snapshot tree")
        commit = subprocess.run(
            [
                "git",
                "commit-tree",
                tree.stdout.strip(),
                "-p",
                head.stdout.strip(),
                "-m",
                f"TDD snapshot {feature}/{resolved_phase}",
            ],
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
        return {"feature": feature, "phase": resolved_phase, "ref": ref, "commit": commit.stdout.strip()}
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
    prefix = "tdd-snapshot-replay-"
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


def run_cache_neutral(command: Sequence[str], *, repo: Path | None = None) -> dict[str, object]:
    """Run a test command without writing pytest or Python bytecode caches."""
    root = _repo_root(repo)
    if isinstance(command, str):
        command = shlex.split(command)
    if not command:
        raise SnapshotError("run requires a command")
    run_env = os.environ.copy()
    run_env["PYTHONDONTWRITEBYTECODE"] = "1"
    run_env["PYTEST_ADDOPTS"] = "-p no:cacheprovider"
    run = subprocess.run(
        command,
        cwd=root,
        env=run_env,
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "returncode": run.returncode,
        "stdout": run.stdout,
        "stderr": run.stderr,
    }


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
    prefix_name = f"tdd-snapshot-replay-{_slug(feature)}-"
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
    create.add_argument("--roles", required=True, type=Path)
    create.add_argument("--provenance", type=Path)
    create.add_argument("--review-iteration", type=int)
    create.add_argument("--focused-provenance", type=Path)
    create.add_argument("--round", type=int)
    replay = subparsers.add_parser("replay")
    replay.add_argument("--ref", required=True)
    replay.add_argument("--test-id")
    replay.add_argument("--failure-classification")
    replay.add_argument("--feature")
    replay.add_argument("--preserve-worktree", action="store_true")
    replay.add_argument("command", nargs=argparse.REMAINDER)
    run = subparsers.add_parser("run")
    run.add_argument("command", nargs=argparse.REMAINDER)
    cleanup = subparsers.add_parser("cleanup")
    cleanup.add_argument("--feature", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload: dict[str, object]
    try:
        if args.operation == "create":
            payload = create_snapshot(
                args.feature,
                args.phase,
                args.roles,
                args.provenance,
                args.review_iteration,
                args.focused_provenance,
                round_number=args.round,
            )
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
        elif args.operation == "run":
            command = list(args.command)
            if command[:1] == ["--"]:
                command = command[1:]
            payload = run_cache_neutral(command)
        else:
            payload = cleanup_snapshots(args.feature)
    except SnapshotError as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}))
        return 1
    print(json.dumps(payload, indent=2, sort_keys=True))
    returncode = payload.get("returncode")
    if args.operation in {"replay", "run"} and isinstance(returncode, int) and returncode != 0:
        return returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
