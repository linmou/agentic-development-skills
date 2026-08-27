#!/usr/bin/env python3
# Responsible file: dynamic phase protection and snapshot behavior tests.

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

import pytest

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "scripts" / "phase_guard.py"
SNAPSHOT = ROOT / "scripts" / "tdd_snapshot.py"


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
    missing = scope_file(repo, commit=False, baseline_ref="refs/codex/tdd/missing")
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
    result = subprocess.run(
        [sys.executable, str(SNAPSHOT), "create", "--feature", "feature", "--phase", "red"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )
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
    first = subprocess.run(
        [sys.executable, str(SNAPSHOT), "create", "--feature", "feature", "--phase", "red"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )
    assert first.returncode == 0, first.stdout + first.stderr
    ref = json.loads(first.stdout)["ref"]
    original_oid = git(repo, "rev-parse", ref)
    (repo / "src" / "app.py").write_text("value = 99\n")

    repeated = subprocess.run(
        [sys.executable, str(SNAPSHOT), "create", "--feature", "feature", "--phase", "red"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )

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
    index_before = git(repo, "write-tree")
    branch_before = git(repo, "branch", "--show-current")
    status_before = subprocess.check_output(["git", "status", "--porcelain=v1", "--ignored"], cwd=repo)

    result = subprocess.run(
        [sys.executable, str(SNAPSHOT), "create", "--feature", "complete", "--phase", "red"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )

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
    created = subprocess.run(
        [sys.executable, str(SNAPSHOT), "create", "--feature", "replay_feature", "--phase", "red"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
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
    created = subprocess.run(
        [sys.executable, str(SNAPSHOT), "create", "--feature", "blocked", "--phase", "red"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )
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
    for phase in ("red", "green"):
        created = subprocess.run(
            [sys.executable, str(SNAPSHOT), "create", "--feature", "multi", "--phase", phase],
            cwd=repo,
            text=True,
            capture_output=True,
            check=False,
        )
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
