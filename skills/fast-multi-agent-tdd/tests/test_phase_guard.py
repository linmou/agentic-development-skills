#!/usr/bin/env python3
# Responsible file: scripts/phase_guard.py; purpose: verify phase category policy.

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from phase_guard import is_allowed, reason_for_phase

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "scripts" / "phase_guard.py"


def git(cwd: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()


def init_repo(tmp_path: Path) -> Path:
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "Test")
    for path, content in {
        "src/login.py": "enabled = False\n",
        "tests/test_login.py": "def test_login(): pass\n",
        "features/login.feature": "Feature: login\n",
        "docs/login.md": "# Login\n",
        "README.md": "# Project\n",
    }.items():
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "initial")
    return tmp_path


def write_scope(repo: Path, phase: str, *, editable: list[str] | None = None) -> Path:
    scope = repo / "scope.json"
    scope.write_text(
        json.dumps(
            {
                "schema": 1,
                "feature": "legacy_phase_rules",
                "phase": phase,
                "baseline_ref": "HEAD",
                "protected": [],
                "editable": editable or [],
                "semantic_overrides": {},
            }
        )
    )
    git(repo, "add", "scope.json")
    git(repo, "commit", "-qm", f"{phase} scope", "--", "scope.json")
    return scope


def run_guard(repo: Path, phase: str, scope: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(GUARD), "--phase", phase, "--scope", str(scope)],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )


@pytest.mark.parametrize(
    ("phase", "allowed", "denied"),
    [
        ("red", "test", "prod"),
        ("green", "prod", "test"),
        ("refactor", "prod", "doc"),
        ("test_refactor", "test", "prod"),
        ("docs", "doc", "test"),
    ],
)
def test_phase_category_rules(phase: str, allowed: str, denied: str) -> None:
    assert is_allowed(phase, allowed)
    assert not is_allowed(phase, denied)


def test_phase_reasons_describe_scope_ownership() -> None:
    assert "tests and docs" in reason_for_phase("red")
    assert "production" in reason_for_phase("green")
    assert "explicitly editable" in reason_for_phase("test_refactor")
    assert "documentation" in reason_for_phase("docs")


@pytest.mark.parametrize(
    ("phase", "path", "content", "editable"),
    [
        ("red", "tests/test_login.py", "def test_login(): assert True\n", []),
        ("red", "docs/login.md", "# Login test seam\n", []),
        ("green", "src/login.py", "enabled = True\n", []),
        ("refactor", "src/login.py", "enabled: bool = False\n", []),
        ("test_refactor", "tests/test_login.py", "def test_login():\n    assert True\n", ["tests/test_login.py"]),
        ("docs", "docs/login.md", "# Login behavior\n", ["docs/login.md"]),
    ],
)
def test_phase_cli_allows_owned_paths(
    tmp_path: Path, phase: str, path: str, content: str, editable: list[str]
) -> None:
    repo = init_repo(tmp_path)
    scope = write_scope(repo, phase, editable=editable)
    (repo / path).write_text(content)

    result = run_guard(repo, phase, scope)

    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["status"] == "pass"


@pytest.mark.parametrize(
    ("phase", "path", "content", "editable", "reason_fragment"),
    [
        ("red", "src/login.py", "enabled = True\n", [], "tests and docs"),
        ("green", "tests/test_login.py", "def test_login(): assert False\n", [], "red-phase"),
        ("refactor", "features/login.feature", "Feature: changed\n", [], "tests and docs"),
        ("refactor", "README.md", "# Changed\n", [], "tests and docs"),
        ("test_refactor", "src/login.py", "enabled = True\n", ["src/login.py"], "test refactor"),
        ("docs", "src/login.py", "enabled = True\n", ["src/login.py"], "documentation"),
    ],
)
def test_phase_cli_rejects_non_owned_paths(
    tmp_path: Path,
    phase: str,
    path: str,
    content: str,
    editable: list[str],
    reason_fragment: str,
) -> None:
    repo = init_repo(tmp_path)
    scope = write_scope(repo, phase, editable=editable)
    (repo / path).write_text(content)

    result = run_guard(repo, phase, scope)

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert path in payload["disallowed_files"]
    assert reason_fragment in payload["reason"]


def test_docs_phase_requires_an_explicit_editable_list(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    scope = repo / "scope.json"
    scope.write_text(
        json.dumps(
            {
                "schema": 1,
                "feature": "docs",
                "phase": "docs",
                "baseline_ref": "HEAD",
                "protected": [],
                "semantic_overrides": {},
            }
        )
    )
    git(repo, "add", "scope.json")
    git(repo, "commit", "-qm", "docs scope", "--", "scope.json")

    result = run_guard(repo, "docs", scope)

    assert result.returncode == 1
    assert "editable" in result.stdout
