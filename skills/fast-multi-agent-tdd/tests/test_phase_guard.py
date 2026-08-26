# Responsible file: scripts/phase_guard.py
# Purpose: enforce that each TDD phase only edits the files it owns.

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "phase_guard.py"


def run_guard(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def test_red_phase_allows_only_test_and_doc_files() -> None:
    result = run_guard(
        "--phase",
        "red",
        "--changed",
        "tests/test_login.py",
        "docs/login.md",
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "pass"
    assert payload["disallowed_files"] == []


def test_green_phase_rejects_test_changes() -> None:
    result = run_guard(
        "--phase",
        "green",
        "--changed",
        "src/login.py",
        "tests/test_login.py",
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["status"] == "fail"
    assert payload["disallowed_files"] == ["tests/test_login.py"]


def test_refactor_phase_rejects_feature_files_and_reports_why() -> None:
    result = run_guard(
        "--phase",
        "refactor",
        "--changed",
        "src/login.py",
        "features/login.feature",
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["status"] == "fail"
    assert payload["disallowed_files"] == ["features/login.feature"]
    assert "tests and docs belong to other phases" in payload["reason"]


def test_refactor_phase_rejects_readme_changes() -> None:
    result = run_guard(
        "--phase",
        "refactor",
        "--changed",
        "src/login.py",
        "README.md",
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["status"] == "fail"
    assert payload["disallowed_files"] == ["README.md"]


def test_docs_phase_allows_only_doc_files() -> None:
    result = run_guard(
        "--phase",
        "docs",
        "--changed",
        "README.md",
        "docs/login.md",
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "pass"
    assert payload["disallowed_files"] == []


def test_docs_phase_rejects_production_changes() -> None:
    result = run_guard(
        "--phase",
        "docs",
        "--changed",
        "README.md",
        "src/login.py",
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["status"] == "fail"
    assert payload["disallowed_files"] == ["src/login.py"]
