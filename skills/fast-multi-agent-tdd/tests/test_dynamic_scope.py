#!/usr/bin/env python3
# Responsible file: dynamic phase protection and snapshot behavior tests.

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

import pytest

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "scripts" / "phase_guard.py"
SNAPSHOT = ROOT / "scripts" / "tdd_snapshot.py"
SKILL = ROOT / "SKILL.md"


def git(cwd: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()


def init_repo(tmp_path: Path) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / "app.py").write_text("value = 1\n")
    (tmp_path / "tests" / "test_app.py").write_text("def test_app(): pass\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "initial")
    return tmp_path


def scope_file(repo: Path, *, commit: bool = True, **overrides: object) -> Path:
    payload: dict[str, object] = {
        "schema": 1,
        "feature": "feature",
        "phase": "green",
        "baseline_ref": "HEAD",
        "protected": ["tests/**", "docs/**"],
        "editable": [],
        "semantic_overrides": {},
    }
    payload.update(overrides)
    path = repo / "scope.json"
    path.write_text(json.dumps(payload))
    if commit:
        git(repo, "add", "-f", "scope.json")
        git(repo, "commit", "-qm", "scope baseline", "--", "scope.json")
    return path


def run_guard(repo: Path, phase: str, scope: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(GUARD), "--phase", phase, "--scope", str(scope)],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )


def role_receipt(repo: Path, expected_feature: str, **overrides: object) -> Path:
    payload: dict[str, object] = {
        "schema": 2,
        "feature": expected_feature,
        "route": "compact",
        "monitor_agent_id": "agent:monitor",
        "monitor_source": "test.delegate",
        "red_reviewer_agent_ids": ["agent:reviewer-1", "agent:reviewer-2", "agent:reviewer-3"],
        "reviewer_source": "test.delegate",
    }
    payload.update(overrides)
    path = repo / f"{expected_feature}-roles.json"
    path.write_text(json.dumps(payload))
    return path


def portable_role_receipt(
    repo: Path,
    expected_feature: str,
    *,
    include_reviewers: bool,
) -> Path:
    payload: dict[str, object] = {
        "schema": 2,
        "feature": expected_feature,
        "route": "compact",
        "monitor_agent_id": "mcp://multi-agent/monitor-17",
        "monitor_source": "multi_agent_v1.delegate",
    }
    if include_reviewers:
        payload.update(
            {
                "red_reviewer_agent_ids": [
                    "task:reviewer-a",
                    "task:reviewer-b",
                    "task:reviewer-c",
                ],
                "reviewer_source": "task.delegate",
            }
        )
    path = repo / f"{expected_feature}-portable-roles.json"
    path.write_text(json.dumps(payload))
    return path


def provenance_receipt(repo: Path, feature: str, roles: Path, *, iteration: int = 1) -> Path:
    receipt = json.loads(roles.read_text())
    reviewer_ids = receipt.get("red_reviewer_agent_ids", [])
    if not isinstance(reviewer_ids, list):
        reviewer_ids = []
    reviewers: list[dict[str, object]] = []
    for index, reviewer_id in enumerate(reviewer_ids, start=1):
        audit_path = repo / f"{feature}_red_audit{index}_iteration{iteration}.json"
        audit_path.write_text(json.dumps({"reviewer_agent_id": reviewer_id}))
        reviewers.append(
            {
                "reviewer_id": f"audit{index}",
                "reviewer_agent_id": reviewer_id,
                "reviewer_source": receipt.get("reviewer_source"),
                "audit_path": str(audit_path.resolve()),
                "audit_sha256": hashlib.sha256(audit_path.read_bytes()).hexdigest(),
            }
        )
    path = repo / f"{feature}-provenance.json"
    path.write_text(
        json.dumps(
            {
                "schema": 1,
                "decision": "provenance_valid",
                "feature": feature,
                "phase": "red",
                "iteration": iteration,
                "monitor_agent_id": receipt.get("monitor_agent_id"),
                "monitor_source": receipt.get("monitor_source"),
                "role_receipt_path": str(roles.resolve()),
                "role_receipt_sha256": hashlib.sha256(roles.read_bytes()).hexdigest(),
                "reviewers": reviewers,
            }
        )
    )
    return path


def focused_provenance_receipt(repo: Path, feature: str, roles: Path) -> Path:
    eligibility = repo / f"{feature}-focused-eligibility.json"
    eligibility.write_text(json.dumps({"decision": "focused_re_review"}))
    focused_audit = repo / f"{feature}_red_focused_iteration2.json"
    focused_audit.write_text(json.dumps({"reviewer_agent_id": "agent:focused-reviewer"}))
    path = repo / f"{feature}-focused-gate.json"
    path.write_text(
        json.dumps(
            {
                "schema": 1,
                "decision": "advance_green",
                "feature": feature,
                "phase": "red",
                "iteration": 2,
                "focused_reviewer_agent_id": "agent:focused-reviewer",
                "reviewer_source": "focused.delegate",
                "focused_audit_path": str(focused_audit.resolve()),
                "focused_audit_sha256": hashlib.sha256(focused_audit.read_bytes()).hexdigest(),
                "role_receipt_path": str(roles.resolve()),
                "role_receipt_sha256": hashlib.sha256(roles.read_bytes()).hexdigest(),
                "eligibility_path": str(eligibility.resolve()),
                "eligibility_sha256": hashlib.sha256(eligibility.read_bytes()).hexdigest(),
            }
        )
    )
    return path


def documented_pre_red_role_receipt(repo: Path, feature: str) -> tuple[Path, dict[str, object]]:
    contract = SKILL.read_text().split("<!-- pre-red-role-receipt-contract -->", 1)[1]
    contract = contract.split("<!-- /pre-red-role-receipt-contract -->", 1)[0]
    payload = cast(dict[str, object], json.loads(contract.split("```json", 1)[1].split("```", 1)[0]))
    payload["feature"] = feature
    payload["route"] = "compact"
    payload["monitor_agent_id"] = "agent:monitor"
    payload["monitor_source"] = "test.delegate"
    path = repo / f"{feature}-documented-roles.json"
    path.write_text(json.dumps(payload))
    return path, payload


def run_snapshot_create(
    repo: Path,
    feature: str,
    phase: str,
    *,
    roles: Path | None = None,
    round_number: int | None = None,
    auto_provenance: bool = True,
    provenance: Path | None = None,
    review_iteration: int | None = None,
    focused_provenance: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(SNAPSHOT), "create", "--feature", feature, "--phase", phase]
    if roles is not None:
        command.extend(["--roles", str(roles)])
        if provenance is not None:
            command.extend(["--provenance", str(provenance)])
            if review_iteration is None:
                review_iteration = int(json.loads(provenance.read_text())["iteration"])
        elif auto_provenance and (phase != "pre_red" or round_number not in {None, 1}):
            provenance = provenance_receipt(repo, feature, roles)
            command.extend(["--provenance", str(provenance)])
            review_iteration = 1
        if review_iteration is not None:
            command.extend(["--review-iteration", str(review_iteration)])
        if focused_provenance is not None:
            command.extend(["--focused-provenance", str(focused_provenance)])
    if round_number is not None:
        command.extend(["--round", str(round_number)])
    return subprocess.run(command, cwd=repo, text=True, capture_output=True, check=False)


def test_guard_derives_tracked_and_untracked_changes(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    scope = scope_file(repo)
    (repo / "src" / "app.py").write_text("value = 2\n")
    (repo / "src" / "new_module.py").write_text("value = 3\n")

    result = run_guard(repo, "green", scope)

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert {item["path"] for item in payload["changed_files"]} == {
        "src/app.py",
        "src/new_module.py",
    }
    assert "scope_digest" not in payload
    assert "artifact_digest" not in payload


def test_guard_rejects_protected_change_and_old_changed_interface(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    scope = scope_file(repo)
    (repo / "tests" / "test_app.py").write_text("def test_app(): assert False\n")

    result = run_guard(repo, "green", scope)
    assert result.returncode == 1
    assert "tests/test_app.py" in json.loads(result.stdout)["disallowed_files"]

    old = subprocess.run(
        [sys.executable, str(GUARD), "--phase", "green", "--changed", "src/app.py"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )
    assert old.returncode != 0


def test_guard_enforces_editable_paths_for_test_refactor(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    scope = scope_file(repo, phase="test_refactor", protected=[], editable=["tests/test_app.py"])
    (repo / "tests" / "test_app.py").write_text("def test_app(): assert True\n")
    (repo / "tests" / "test_other.py").write_text("def test_other(): pass\n")

    result = run_guard(repo, "test_refactor", scope)

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["disallowed_files"] == ["tests/test_other.py"]


def test_guard_supports_exact_and_bounded_patterns(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    scope = scope_file(repo, protected=["src/app.py"])
    (repo / "src" / "app.py").write_text("value = 2\n")
    (repo / "src" / "other.py").write_text("value = 3\n")
    assert run_guard(repo, "green", scope).returncode == 1
    scope = scope_file(repo, protected=["src/**"])
    assert run_guard(repo, "green", scope).returncode == 1


def test_guard_exact_and_bounded_patterns_do_not_match_sibling_prefixes(tmp_path: Path) -> None:
    exact_repo = init_repo(tmp_path / "exact")
    exact_scope = scope_file(exact_repo, protected=["src/app.py"])
    (exact_repo / "src" / "other.py").write_text("value = 3\n")
    exact = run_guard(exact_repo, "green", exact_scope)
    assert exact.returncode == 0, exact.stdout + exact.stderr

    bounded_repo = init_repo(tmp_path / "bounded")
    bounded_scope = scope_file(bounded_repo, protected=["src/**"])
    (bounded_repo / "src2").mkdir()
    (bounded_repo / "src2" / "app.py").write_text("value = 3\n")
    bounded = run_guard(bounded_repo, "green", bounded_scope)
    assert bounded.returncode == 0, bounded.stdout + bounded.stderr


def test_guard_requires_override_for_ambiguous_semantic_path(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    (repo / "src" / "tests").mkdir()
    path = repo / "src" / "tests" / "runtime.py"
    scope = scope_file(repo, protected=[], editable=[])
    path.write_text("value = 2\n")
    result = run_guard(repo, "green", scope)
    assert result.returncode == 1
    assert "semantic" in result.stdout.lower()

    scope = scope_file(repo, protected=[], semantic_overrides={"src/tests/runtime.py": "prod"})
    assert run_guard(repo, "green", scope).returncode == 0


def test_guard_handles_rename_and_deletion_from_baseline(tmp_path: Path) -> None:
    renamed_repo = init_repo(tmp_path / "renamed")
    renamed_scope = scope_file(renamed_repo, protected=["src/app.py"])
    git(renamed_repo, "mv", "src/app.py", "src/renamed.py")
    (renamed_repo / "src" / "other.py").write_text("x = 1\n")
    result = run_guard(renamed_repo, "green", renamed_scope)
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert "src/app.py" in payload["changed_paths"]
    assert "src/renamed.py" in payload["changed_paths"]

    deleted_repo = init_repo(tmp_path / "deleted")
    deleted_scope = scope_file(deleted_repo, protected=["src/app.py"])
    (deleted_repo / "src" / "app.py").unlink()
    assert run_guard(deleted_repo, "green", deleted_scope).returncode == 1


def test_guard_rejects_missing_or_mismatched_baseline(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    missing = scope_file(repo, commit=False, baseline_ref="refs/tdd/missing")
    assert run_guard(repo, "green", missing).returncode == 1
    mismatch = scope_file(repo, phase="red")
    assert run_guard(repo, "green", mismatch).returncode == 1


@pytest.mark.parametrize(
    "scope_override",
    [
        {"schema": 2},
        {"protected": ["src/*/app.py"]},
    ],
)
def test_guard_rejects_unsupported_schema_and_unbounded_patterns(
    tmp_path: Path, scope_override: dict[str, object]
) -> None:
    repo = init_repo(tmp_path)
    scope = scope_file(repo, **cast(dict[str, Any], scope_override))

    result = run_guard(repo, "green", scope)

    assert result.returncode == 1
    assert json.loads(result.stdout)["status"] == "fail"


def test_guard_accepts_scope_unchanged_from_baseline(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    scope = scope_file(repo)
    (repo / "src" / "app.py").write_text("value = 2\n")

    result = run_guard(repo, "green", scope)

    assert result.returncode == 0, result.stdout + result.stderr


def test_guard_rejects_scope_mutation_deletion_and_missing_baseline_copy(tmp_path: Path) -> None:
    mutated_repo = init_repo(tmp_path / "mutated")
    mutated_scope = scope_file(mutated_repo)
    mutated_scope.write_text(mutated_scope.read_text() + "\n")
    mutated = run_guard(mutated_repo, "green", mutated_scope)
    assert mutated.returncode == 1
    assert "baseline" in mutated.stdout.lower() or "scope" in mutated.stdout.lower()

    deleted_repo = init_repo(tmp_path / "deleted")
    deleted_scope = scope_file(deleted_repo)
    deleted_scope.unlink()
    deleted = run_guard(deleted_repo, "green", deleted_scope)
    assert deleted.returncode == 1

    missing_repo = init_repo(tmp_path / "missing")
    missing_scope = scope_file(missing_repo, commit=False)
    missing = run_guard(missing_repo, "green", missing_scope)
    assert missing.returncode == 1
    assert "baseline" in missing.stdout.lower()


def test_guard_rejects_symlink_and_outside_scope_paths(tmp_path: Path) -> None:
    repo = init_repo(tmp_path / "repo")
    outside = tmp_path / "outside.json"
    outside.write_text("{}")
    symlink = repo / "linked_scope.json"
    symlink.symlink_to(outside)

    linked = run_guard(repo, "green", symlink)
    external = run_guard(repo, "green", outside)

    assert linked.returncode == 1
    assert external.returncode == 1


def test_guard_rejects_in_repository_scope_symlink_alias(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    scope = scope_file(repo)
    alias = repo / "scope_alias.json"
    alias.symlink_to(scope.name)

    result = run_guard(repo, "green", alias)

    assert result.returncode == 1
    assert "symlink" in result.stdout.lower()


def test_guard_rejects_malformed_scope_even_when_baseline_matches(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    scope = repo / "scope.json"
    scope.write_text("not-json\n")
    git(repo, "add", "scope.json")
    git(repo, "commit", "-qm", "malformed scope", "--", "scope.json")

    result = run_guard(repo, "green", scope)

    assert result.returncode == 1
    assert "invalid scope artifact" in result.stdout.lower()


def test_guard_discovers_normal_and_ignored_untracked_paths_nul_safely(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    (repo / ".gitignore").write_text("ignored-*\n")
    git(repo, "add", ".gitignore")
    git(repo, "commit", "-qm", "ignore rule")
    scope = scope_file(repo)
    normal_name = "src/normal name.py"
    ignored_name = "ignored-line\nbreak.py"
    (repo / normal_name).write_text("value = 1\n")
    (repo / ignored_name).write_text("value = 2\n")

    result = run_guard(repo, "green", scope)

    assert result.returncode == 0, result.stdout + result.stderr
    assert set(json.loads(result.stdout)["changed_paths"]) == {normal_name, ignored_name}


def test_guard_applies_phase_policy_to_ignored_untracked_paths(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    (repo / ".gitignore").write_text("*.test.py\n")
    git(repo, "add", ".gitignore")
    git(repo, "commit", "-qm", "ignore tests")
    scope = scope_file(repo, protected=[])
    ignored_test = "hidden.test.py"
    (repo / ignored_test).write_text("def test_hidden(): pass\n")

    result = run_guard(repo, "green", scope)

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert ignored_test in payload["changed_paths"]
    assert ignored_test in payload["disallowed_files"]


def test_protected_path_wins_over_editable_path(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    path = "tests/test_app.py"
    scope = scope_file(repo, phase="test_refactor", protected=[path], editable=[path])
    (repo / path).write_text("def test_app(): assert True\n")

    result = run_guard(repo, "test_refactor", scope)

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert path in payload["protected_files"]
    assert path in payload["disallowed_files"]


def test_guard_rejects_conflicting_overlapping_semantic_overrides(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    conflict = scope_file(
        repo,
        protected=[],
        semantic_overrides={"src/tests/**": "test", "src/tests/runtime.py": "prod"},
    )

    result = run_guard(repo, "green", conflict)

    assert result.returncode == 1
    assert "conflict" in result.stdout.lower()


def test_guard_accepts_overlapping_semantic_overrides_with_same_kind(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    scope = scope_file(
        repo,
        protected=[],
        semantic_overrides={"src/tests/**": "prod", "src/tests/runtime.py": "prod"},
    )
    (repo / "src" / "tests").mkdir()
    (repo / "src" / "tests" / "runtime.py").write_text("value = 2\n")

    result = run_guard(repo, "green", scope)

    assert result.returncode == 0, result.stdout + result.stderr


def test_snapshot_create_replay_and_cleanup_preserve_index(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    (repo / "src" / "app.py").write_text("value = 2\n")
    git(repo, "add", "src/app.py")
    index_before = git(repo, "write-tree")
    result = run_snapshot_create(repo, "feature", "pre_red", roles=role_receipt(repo, "feature"))
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert git(repo, "write-tree") == index_before
    assert git(repo, "rev-parse", "--verify", payload["ref"])
    replay = subprocess.run(
        [sys.executable, str(SNAPSHOT), "replay", "--ref", payload["ref"], "--", sys.executable, "-c", "print('ok')"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )
    assert replay.returncode == 0
    cleanup = subprocess.run(
        [sys.executable, str(SNAPSHOT), "cleanup", "--feature", "feature"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )
    assert cleanup.returncode == 0
    assert subprocess.run(["git", "show-ref", "--verify", payload["ref"]], cwd=repo, check=False).returncode != 0


def test_snapshot_ref_is_append_only(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    roles = role_receipt(repo, "feature")
    first = run_snapshot_create(repo, "feature", "pre_red", roles=roles)
    assert first.returncode == 0, first.stdout + first.stderr
    ref = json.loads(first.stdout)["ref"]
    original_oid = git(repo, "rev-parse", ref)
    (repo / "src" / "app.py").write_text("value = 99\n")

    repeated = run_snapshot_create(repo, "feature", "pre_red", roles=roles)

    assert repeated.returncode == 1
    assert "exists" in repeated.stdout.lower()
    assert git(repo, "rev-parse", ref) == original_oid


def test_snapshot_captures_complete_state_without_mutating_repository(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    (repo / ".gitignore").write_text("ignored.py\n")
    (repo / "src" / "deleted.py").write_text("delete me\n")
    (repo / "src" / "rename_me.py").write_text("rename me\n")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "snapshot fixtures")
    (repo / "src" / "app.py").write_text("staged = True\n")
    git(repo, "add", "src/app.py")
    (repo / "tests" / "test_app.py").write_text("unstaged = True\n")
    (repo / "src" / "deleted.py").unlink()
    git(repo, "mv", "src/rename_me.py", "src/renamed.py")
    (repo / "normal.py").write_text("normal = True\n")
    (repo / "ignored.py").write_text("ignored = True\n")
    roles = role_receipt(repo, "complete")
    index_before = git(repo, "write-tree")
    branch_before = git(repo, "branch", "--show-current")
    status_before = subprocess.check_output(["git", "status", "--porcelain=v1", "--ignored"], cwd=repo)

    result = run_snapshot_create(repo, "complete", "pre_red", roles=roles)

    assert result.returncode == 0, result.stdout + result.stderr
    ref = json.loads(result.stdout)["ref"]
    assert git(repo, "show", f"{ref}:src/app.py") == "staged = True"
    assert git(repo, "show", f"{ref}:tests/test_app.py") == "unstaged = True"
    assert git(repo, "show", f"{ref}:src/renamed.py") == "rename me"
    assert git(repo, "show", f"{ref}:normal.py") == "normal = True"
    assert git(repo, "show", f"{ref}:ignored.py") == "ignored = True"
    assert subprocess.run(["git", "cat-file", "-e", f"{ref}:src/deleted.py"], cwd=repo, check=False).returncode != 0
    assert subprocess.run(["git", "cat-file", "-e", f"{ref}:src/rename_me.py"], cwd=repo, check=False).returncode != 0
    assert git(repo, "write-tree") == index_before
    assert git(repo, "branch", "--show-current") == branch_before
    assert subprocess.check_output(["git", "status", "--porcelain=v1", "--ignored"], cwd=repo) == status_before


def test_replay_uses_snapshot_bytes_and_cleanup_removes_preserved_resources(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    (repo / "snapshot_value.txt").write_text("immutable\n")
    created = run_snapshot_create(
        repo,
        "replay_feature",
        "pre_red",
        roles=role_receipt(repo, "replay_feature"),
    )
    assert created.returncode == 0, created.stdout + created.stderr
    ref = json.loads(created.stdout)["ref"]
    (repo / "snapshot_value.txt").write_text("mutable\n")
    command = [sys.executable, "-c", "from pathlib import Path; print(Path('snapshot_value.txt').read_text().strip())"]

    replayed = subprocess.run(
        [
            sys.executable,
            str(SNAPSHOT),
            "replay",
            "--ref",
            ref,
            "--feature",
            "replay_feature",
            "--test-id",
            "tests/test_phase.py::test_red",
            "--failure-classification",
            "expected_red_failure",
            "--preserve-worktree",
            "--",
            *command,
        ],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )

    assert replayed.returncode == 0, replayed.stdout + replayed.stderr
    replay_payload = json.loads(replayed.stdout)
    preserved = Path(str(replay_payload["worktree"]))
    assert replay_payload["stdout"].strip() == "immutable"
    assert replay_payload["test_id"] == "tests/test_phase.py::test_red"
    assert replay_payload["failure_classification"] == "expected_red_failure"
    assert preserved.exists()
    assert str(preserved) in git(repo, "worktree", "list", "--porcelain")

    cleaned = subprocess.run(
        [sys.executable, str(SNAPSHOT), "cleanup", "--feature", "replay_feature"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )

    assert cleaned.returncode == 0, cleaned.stdout + cleaned.stderr
    cleanup_payload = json.loads(cleaned.stdout)
    assert ref in cleanup_payload["removed_refs"]
    assert str(preserved) in cleanup_payload["removed_worktrees"]
    assert not preserved.exists()
    assert subprocess.run(["git", "show-ref", "--verify", ref], cwd=repo, check=False).returncode != 0


def test_failing_replay_can_preserve_blocked_run_worktree(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    created = run_snapshot_create(repo, "blocked", "pre_red", roles=role_receipt(repo, "blocked"))
    assert created.returncode == 0, created.stdout + created.stderr
    ref = json.loads(created.stdout)["ref"]

    replayed = subprocess.run(
        [
            sys.executable,
            str(SNAPSHOT),
            "replay",
            "--ref",
            ref,
            "--feature",
            "blocked",
            "--preserve-worktree",
            "--",
            sys.executable,
            "-c",
            "raise SystemExit(7)",
        ],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )

    assert replayed.returncode == 7
    payload = json.loads(replayed.stdout)
    preserved = Path(str(payload["worktree"]))
    assert payload["failure_classification"] == "nonzero_exit"
    assert payload["preserved"] is True
    assert preserved.exists()
    assert str(preserved) in git(repo, "worktree", "list", "--porcelain")

    cleanup = subprocess.run(
        [sys.executable, str(SNAPSHOT), "cleanup", "--feature", "blocked"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )
    assert cleanup.returncode == 0, cleanup.stdout + cleanup.stderr
    assert not preserved.exists()


def test_cleanup_removes_all_phase_refs_for_feature(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    refs: list[str] = []
    roles = role_receipt(repo, "multi")
    for phase in ("pre_red", "pre_green"):
        created = run_snapshot_create(repo, "multi", phase, roles=roles)
        assert created.returncode == 0, created.stdout + created.stderr
        refs.append(str(json.loads(created.stdout)["ref"]))

    cleaned = subprocess.run(
        [sys.executable, str(SNAPSHOT), "cleanup", "--feature", "multi"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )

    assert cleaned.returncode == 0, cleaned.stdout + cleaned.stderr
    payload = json.loads(cleaned.stdout)
    assert set(payload["removed_refs"]) == set(refs)
    for ref in refs:
        assert subprocess.run(["git", "show-ref", "--verify", ref], cwd=repo, check=False).returncode != 0


def test_snapshot_create_requires_role_receipt_without_publishing_ref(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)

    result = run_snapshot_create(repo, "missing_roles", "pre_red")

    assert result.returncode != 0
    assert subprocess.run(
        ["git", "show-ref", "--verify", "refs/tdd/missing_roles/pre_red"],
        cwd=repo,
        check=False,
    ).returncode != 0


def test_snapshot_accepts_backend_neutral_monitor_provenance(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)

    result = run_snapshot_create(
        repo,
        "portable_monitor",
        "pre_red",
        roles=portable_role_receipt(repo, "portable_monitor", include_reviewers=False),
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["ref"] == "refs/tdd/portable_monitor/pre_red"


def test_snapshot_accepts_backend_neutral_distinct_reviewer_provenance(
    tmp_path: Path,
) -> None:
    repo = init_repo(tmp_path)

    result = run_snapshot_create(
        repo,
        "portable_reviewers",
        "pre_green",
        roles=portable_role_receipt(repo, "portable_reviewers", include_reviewers=True),
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["ref"] == "refs/tdd/portable_reviewers/pre_green"


def test_post_red_snapshot_requires_current_provenance_without_publishing_ref(
    tmp_path: Path,
) -> None:
    repo = init_repo(tmp_path)
    roles = portable_role_receipt(repo, "bound_reviewers", include_reviewers=True)
    provenance = provenance_receipt(repo, "bound_reviewers", roles)
    payload = json.loads(provenance.read_text())
    Path(payload["reviewers"][1]["audit_path"]).write_text("replaced after provenance\n")

    stale = run_snapshot_create(
        repo,
        "bound_reviewers",
        "pre_green",
        roles=roles,
        auto_provenance=False,
        provenance=provenance,
    )

    assert stale.returncode != 0
    assert "audit_sha256" in stale.stdout
    assert subprocess.run(
        ["git", "show-ref", "--verify", "refs/tdd/bound_reviewers/pre_green"],
        cwd=repo,
        check=False,
    ).returncode != 0


def test_post_red_snapshot_accepts_current_receipt_bound_provenance(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    roles = portable_role_receipt(repo, "current_reviewers", include_reviewers=True)
    provenance = provenance_receipt(repo, "current_reviewers", roles)

    result = run_snapshot_create(
        repo,
        "current_reviewers",
        "pre_green",
        roles=roles,
        auto_provenance=False,
        provenance=provenance,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["ref"] == "refs/tdd/current_reviewers/pre_green"


def test_post_red_snapshot_rejects_missing_provenance(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    roles = portable_role_receipt(repo, "missing_provenance", include_reviewers=True)

    result = run_snapshot_create(
        repo,
        "missing_provenance",
        "pre_green",
        roles=roles,
        auto_provenance=False,
    )

    assert result.returncode != 0
    assert "post-Red snapshots require --provenance" in result.stdout


def test_post_red_snapshot_rejects_mismatched_review_iteration(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    roles = portable_role_receipt(repo, "stale_iteration", include_reviewers=True)
    provenance = provenance_receipt(repo, "stale_iteration", roles, iteration=1)

    result = run_snapshot_create(
        repo,
        "stale_iteration",
        "pre_green",
        roles=roles,
        auto_provenance=False,
        provenance=provenance,
        review_iteration=2,
    )

    assert result.returncode != 0
    assert "review iteration" in result.stdout


def test_numbered_red_snapshot_requires_previous_review_iteration(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    roles = portable_role_receipt(repo, "round_iteration", include_reviewers=True)
    provenance = provenance_receipt(repo, "round_iteration", roles, iteration=1)

    result = run_snapshot_create(
        repo,
        "round_iteration",
        "pre_red",
        roles=roles,
        round_number=3,
        auto_provenance=False,
        provenance=provenance,
        review_iteration=1,
    )

    assert result.returncode != 0
    assert "round 3 requires review iteration 2" in result.stdout


def test_pre_green_snapshot_accepts_focused_iteration_provenance(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    roles = portable_role_receipt(repo, "focused_review", include_reviewers=True)
    initial_provenance = provenance_receipt(repo, "focused_review", roles, iteration=1)
    focused_provenance = focused_provenance_receipt(repo, "focused_review", roles)

    result = run_snapshot_create(
        repo,
        "focused_review",
        "pre_green",
        roles=roles,
        auto_provenance=False,
        provenance=initial_provenance,
        review_iteration=2,
        focused_provenance=focused_provenance,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["ref"] == "refs/tdd/focused_review/pre_green"


def test_pre_green_snapshot_rejects_stale_focused_audit(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    roles = portable_role_receipt(repo, "stale_focused", include_reviewers=True)
    initial_provenance = provenance_receipt(repo, "stale_focused", roles, iteration=1)
    focused_provenance = focused_provenance_receipt(repo, "stale_focused", roles)
    focused_payload = json.loads(focused_provenance.read_text())
    Path(focused_payload["focused_audit_path"]).write_text("changed after focused gate\n")

    result = run_snapshot_create(
        repo,
        "stale_focused",
        "pre_green",
        roles=roles,
        auto_provenance=False,
        provenance=initial_provenance,
        review_iteration=2,
        focused_provenance=focused_provenance,
    )

    assert result.returncode != 0
    assert "focused provenance focused_audit_sha256 is stale" in result.stdout


def test_start_gate_role_receipt_contract_matches_snapshot_validator(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    roles, documented_payload = documented_pre_red_role_receipt(repo, "documented_roles")

    accepted = run_snapshot_create(repo, "documented_roles", "pre_red", roles=roles)

    assert accepted.returncode == 0, accepted.stdout + accepted.stderr
    assert json.loads(accepted.stdout)["ref"] == "refs/tdd/documented_roles/pre_red"

    documented_payload["feature"] = "monitor_alias"
    documented_payload["monitor"] = documented_payload.pop("monitor_agent_id")
    roles.write_text(json.dumps(documented_payload))
    rejected = run_snapshot_create(repo, "monitor_alias", "pre_red", roles=roles)

    assert rejected.returncode == 1
    assert "monitor_agent_id" in json.loads(rejected.stdout)["error"]


@pytest.mark.parametrize(
    "receipt_override",
    [
        {"schema": 1},
        {"feature": "different_feature"},
        {"route": "automatic"},
        {"monitor_agent_id": ""},
        {"monitor_source": "  "},
    ],
)
def test_snapshot_create_rejects_invalid_monitor_receipt_without_publishing_ref(
    tmp_path: Path,
    receipt_override: dict[str, object],
) -> None:
    repo = init_repo(tmp_path)
    roles = role_receipt(repo, "receipt_check", **receipt_override)

    result = run_snapshot_create(repo, "receipt_check", "pre_red", roles=roles)

    assert result.returncode == 1
    assert json.loads(result.stdout)["status"] == "fail"
    assert subprocess.run(
        ["git", "show-ref", "--verify", "refs/tdd/receipt_check/pre_red"],
        cwd=repo,
        check=False,
    ).returncode != 0


@pytest.mark.parametrize(
    "receipt_override",
    [
        {"red_reviewer_agent_ids": []},
        {"red_reviewer_agent_ids": ["agent:reviewer", "agent:reviewer"]},
        {"red_reviewer_agent_ids": ["agent:monitor", "agent:reviewer-2"]},
        {"red_reviewer_agent_ids": [""]},
        {"reviewer_source": ""},
    ],
)
def test_pre_green_snapshot_requires_delegated_distinct_red_reviewers(
    tmp_path: Path,
    receipt_override: dict[str, object],
) -> None:
    repo = init_repo(tmp_path)
    roles = role_receipt(repo, "reviewer_check", **receipt_override)

    result = run_snapshot_create(repo, "reviewer_check", "pre_green", roles=roles)

    assert result.returncode == 1
    assert json.loads(result.stdout)["status"] == "fail"
    assert subprocess.run(
        ["git", "show-ref", "--verify", "refs/tdd/reviewer_check/pre_green"],
        cwd=repo,
        check=False,
    ).returncode != 0


def test_snapshot_create_accepts_valid_pre_green_role_receipt(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)

    result = run_snapshot_create(
        repo,
        "valid_roles",
        "pre_green",
        roles=role_receipt(repo, "valid_roles", route="full"),
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["ref"] == "refs/tdd/valid_roles/pre_green"


def test_subsequent_pre_red_round_is_authenticated_and_append_only(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    roles = role_receipt(repo, "red_round")
    first = run_snapshot_create(repo, "red_round", "pre_red", roles=roles, round_number=1)
    assert first.returncode == 0, first.stdout + first.stderr
    first_payload = json.loads(first.stdout)
    assert first_payload["ref"] == "refs/tdd/red_round/pre_red"

    (repo / "src" / "app.py").write_text("value = 2\n")
    second = run_snapshot_create(repo, "red_round", "pre_red", roles=roles, round_number=2)
    assert second.returncode == 0, second.stdout + second.stderr
    second_payload = json.loads(second.stdout)
    assert second_payload["ref"] == "refs/tdd/red_round/pre_red_round_2"
    assert git(repo, "show", f"{first_payload['ref']}:src/app.py") == "value = 1"
    assert git(repo, "show", f"{second_payload['ref']}:src/app.py") == "value = 2"

    original_round_two_oid = git(repo, "rev-parse", second_payload["ref"])
    (repo / "src" / "app.py").write_text("value = 3\n")
    repeated = run_snapshot_create(repo, "red_round", "pre_red", roles=roles, round_number=2)

    assert repeated.returncode == 1
    assert "exists" in repeated.stdout.lower()
    assert git(repo, "rev-parse", second_payload["ref"]) == original_round_two_oid


@pytest.mark.parametrize("round_number", [0, -1])
def test_pre_red_snapshot_rejects_invalid_round_number(tmp_path: Path, round_number: int) -> None:
    repo = init_repo(tmp_path)

    result = run_snapshot_create(
        repo,
        "invalid_round",
        "pre_red",
        roles=role_receipt(repo, "invalid_round"),
        round_number=round_number,
    )

    assert result.returncode == 1
    assert json.loads(result.stdout)["status"] == "fail"
    assert subprocess.run(
        ["git", "for-each-ref", "--format=%(refname)", "refs/tdd/invalid_round/"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    ).stdout == ""


@pytest.mark.parametrize(
    "receipt_override",
    [
        {"red_reviewer_agent_ids": []},
        {"red_reviewer_agent_ids": ["agent:reviewer", "agent:reviewer"]},
        {"red_reviewer_agent_ids": ["agent:monitor", "agent:reviewer-2"]},
        {"red_reviewer_agent_ids": [""]},
        {"reviewer_source": ""},
    ],
)
def test_subsequent_pre_red_round_requires_delegated_distinct_reviewers(
    tmp_path: Path,
    receipt_override: dict[str, object],
) -> None:
    repo = init_repo(tmp_path)
    roles = role_receipt(repo, "round_roles", **receipt_override)

    result = run_snapshot_create(repo, "round_roles", "pre_red", roles=roles, round_number=2)

    assert result.returncode == 1
    assert json.loads(result.stdout)["status"] == "fail"
    assert subprocess.run(
        ["git", "show-ref", "--verify", "refs/tdd/round_roles/pre_red_round_2"],
        cwd=repo,
        check=False,
    ).returncode != 0


def test_cache_neutral_run_preserves_existing_cache_paths_and_bytes(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    (repo / "sample.py").write_text("VALUE = 7\n")
    (repo / "tests" / "test_cache_neutral.py").write_text(
        "import sys\n"
        "from pathlib import Path\n"
        "from sample import VALUE\n\n"
        "ROOT = Path(__file__).resolve().parents[1]\n\n"
        "def test_value(pytestconfig):\n"
        "    assert VALUE == 7\n"
        "    assert sys.dont_write_bytecode is True\n"
        "    assert not pytestconfig.pluginmanager.hasplugin('cacheprovider')\n"
        "    cache_paths = {\n"
        "        path.relative_to(ROOT).as_posix()\n"
        "        for path in ROOT.rglob('*')\n"
        "        if path.name in {'.pytest_cache', '__pycache__'} or path.suffix == '.pyc'\n"
        "    }\n"
        "    assert cache_paths == {'.pytest_cache', '__pycache__', '__pycache__/sentinel.pyc'}\n"
    )
    pytest_sentinel = repo / ".pytest_cache" / "sentinel"
    bytecode_sentinel = repo / "__pycache__" / "sentinel.pyc"
    pytest_sentinel.parent.mkdir()
    bytecode_sentinel.parent.mkdir()
    pytest_sentinel.write_bytes(b"pytest-sentinel\n")
    bytecode_sentinel.write_bytes(b"bytecode-sentinel\n")
    cache_paths_before = {
        path.relative_to(repo).as_posix()
        for path in repo.rglob("*")
        if path.name == ".pytest_cache" or path.name == "__pycache__" or path.suffix == ".pyc"
    }
    child_env = os.environ.copy()
    child_env.pop("PYTHONDONTWRITEBYTECODE", None)
    child_env.pop("PYTEST_ADDOPTS", None)

    result = subprocess.run(
        [
            sys.executable,
            str(SNAPSHOT),
            "run",
            "--",
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/test_cache_neutral.py",
        ],
        cwd=repo,
        env=child_env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["returncode"] == 0
    assert "1 passed" in payload["stdout"]
    cache_paths_after = {
        path.relative_to(repo).as_posix()
        for path in repo.rglob("*")
        if path.name == ".pytest_cache" or path.name == "__pycache__" or path.suffix == ".pyc"
    }
    assert cache_paths_after == cache_paths_before
    assert pytest_sentinel.read_bytes() == b"pytest-sentinel\n"
    assert bytecode_sentinel.read_bytes() == b"bytecode-sentinel\n"


def test_cache_neutral_run_preserves_child_exit_status(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)

    result = subprocess.run(
        [sys.executable, str(SNAPSHOT), "run", "--", sys.executable, "-c", "raise SystemExit(7)"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 7
    assert json.loads(result.stdout)["returncode"] == 7
