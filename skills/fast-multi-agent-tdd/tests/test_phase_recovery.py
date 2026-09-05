#!/usr/bin/env python3
# Responsible file: scripts/phase_recovery.py; purpose: verify bounded authenticated phase recovery.

from __future__ import annotations

import base64
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RECOVERY = ROOT / "scripts" / "phase_recovery.py"


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()


def init_repo(tmp_path: Path, *, extra_files: dict[str, str] | None = None) -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "user.name", "Test")
    files = {
        "src/app.py": "value = 1\n",
        "tests/test_app.py": "def test_app(): pass\n",
    }
    files.update(extra_files or {})
    for relative, content in files.items():
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    scope = repo / "scope.json"
    scope.write_text(
        json.dumps(
            {
                "schema": 1,
                "feature": "phase_recovery",
                "phase": "green",
                "baseline_ref": "HEAD",
                "protected": ["tests/**", "audits/**"],
                "editable": [],
                "semantic_overrides": {},
            }
        )
    )
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "baseline")
    return repo, scope


def mutate_command(path: str, content: str, *, exit_code: int = 0) -> list[str]:
    source = (
        "from pathlib import Path; "
        f"Path({path!r}).write_text({content!r}); "
        f"raise SystemExit({exit_code})"
    )
    return [sys.executable, "-c", source]


def run_recovery(
    repo: Path,
    scope: Path,
    receipt: Path,
    command: list[str],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(RECOVERY),
            "--phase",
            "green",
            "--scope",
            str(scope),
            "--receipt",
            str(receipt),
            "--cause",
            "accidental_phase_write",
            "--",
            *command,
        ],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )


def test_cli_recovers_command_caused_tracked_test_change_and_preserves_receipt(
    tmp_path: Path,
) -> None:
    repo, scope = init_repo(tmp_path)
    receipt = tmp_path / "recovery.jsonl"
    violating = "def test_app(): assert False\n"

    result = run_recovery(
        repo,
        scope,
        receipt,
        mutate_command("tests/test_app.py", violating),
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload == {
        "schema": 1,
        "status": "recovered",
        "recovered": True,
        "child_returncode": 0,
        "guard_status": "pass",
        "receipt": str(receipt),
        "restored_paths": ["tests/test_app.py"],
    }
    assert (repo / "tests/test_app.py").read_text() == "def test_app(): pass\n"
    events = [json.loads(line) for line in receipt.read_text().splitlines()]
    assert [event["event"] for event in events] == ["recovery_planned", "recovery_completed"]
    planned = events[0]
    assert planned["baseline_commit"] == git(repo, "rev-parse", "HEAD")
    assert planned["paths"][0]["path"] == "tests/test_app.py"
    encoded = planned["paths"][0]["violating"]["content_base64"]
    assert base64.b64decode(encoded).decode() == violating
    archived = git(repo, "show", f"{planned['post_worktree_tree']}:tests/test_app.py")
    assert archived + "\n" == violating
    assert events[1]["final_guard_status"] == "pass"


def test_cli_refuses_preexisting_phase_violation_without_running_command(tmp_path: Path) -> None:
    repo, scope = init_repo(tmp_path)
    receipt = tmp_path / "recovery.jsonl"
    (repo / "tests/test_app.py").write_text("preexisting = True\n")

    result = run_recovery(
        repo,
        scope,
        receipt,
        mutate_command("src/marker.py", "ran = True\n"),
    )

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["status"] == "non_recoverable"
    assert "already invalid" in payload["reason"]
    assert not (repo / "src/marker.py").exists()
    assert not receipt.exists()


@pytest.mark.parametrize(
    ("path", "extra_files", "reason"),
    [
        ("tests/new_test.py", None, "untracked or renamed"),
        ("audits/reviewer.json", {"audits/reviewer.json": "original\n"}, "never auto-recoverable"),
    ],
    ids=["untracked", "reviewer-owned"],
)
def test_cli_refuses_untracked_and_reviewer_owned_changes(
    tmp_path: Path,
    path: str,
    extra_files: dict[str, str] | None,
    reason: str,
) -> None:
    repo, scope = init_repo(tmp_path, extra_files=extra_files)
    receipt = tmp_path / "recovery.jsonl"

    result = run_recovery(repo, scope, receipt, mutate_command(path, "violating\n"))

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["status"] == "non_recoverable"
    assert reason in payload["reason"]
    assert (repo / path).read_text() == "violating\n"
    assert not receipt.exists()


def test_cli_refuses_real_index_drift_and_does_not_restore(tmp_path: Path) -> None:
    repo, scope = init_repo(tmp_path)
    receipt = tmp_path / "recovery.jsonl"
    command = mutate_command("tests/test_app.py", "violating\n")
    command[2] = command[2].removesuffix("raise SystemExit(0)") + (
        "import subprocess; subprocess.run(['git', 'add', 'tests/test_app.py'], check=True)"
    )

    result = run_recovery(repo, scope, receipt, command)

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert "real Git index" in payload["reason"]
    assert (repo / "tests/test_app.py").read_text() == "violating\n"
    assert not receipt.exists()


def test_cli_refuses_ambiguous_semantic_path(tmp_path: Path) -> None:
    repo, scope = init_repo(tmp_path, extra_files={"src/tests/runtime.py": "value = 1\n"})
    receipt = tmp_path / "recovery.jsonl"

    result = run_recovery(
        repo,
        scope,
        receipt,
        mutate_command("src/tests/runtime.py", "value = 2\n"),
    )

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert "ambiguous semantic classification" in payload["reason"]
    assert (repo / "src/tests/runtime.py").read_text() == "value = 2\n"
    assert not receipt.exists()


def test_cli_recovers_state_but_propagates_failed_command_status(tmp_path: Path) -> None:
    repo, scope = init_repo(tmp_path)
    receipt = tmp_path / "recovery.jsonl"

    result = run_recovery(
        repo,
        scope,
        receipt,
        mutate_command("tests/test_app.py", "violating\n", exit_code=7),
    )

    assert result.returncode == 7
    payload = json.loads(result.stdout)
    assert payload["status"] == "recovered_command_failed"
    assert payload["guard_status"] == "pass"
    assert (repo / "tests/test_app.py").read_text() == "def test_app(): pass\n"
    assert json.loads(receipt.read_text().splitlines()[-1])["status"] == "recovered_command_failed"


def test_cli_requires_external_fresh_receipt_before_running_command(tmp_path: Path) -> None:
    repo, scope = init_repo(tmp_path)
    receipt = repo / "recovery.jsonl"

    result = run_recovery(
        repo,
        scope,
        receipt,
        mutate_command("tests/test_app.py", "violating\n"),
    )

    assert result.returncode == 2
    assert "outside the repository" in json.loads(result.stdout)["reason"]
    assert (repo / "tests/test_app.py").read_text() == "def test_app(): pass\n"
