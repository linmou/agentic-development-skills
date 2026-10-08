#!/usr/bin/env python3
# Responsible for verifying bounded review-input freezing and mutation detection.

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "review_bundle.py"


def load_module():
    spec = importlib.util.spec_from_file_location("review_bundle", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def init_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Review Test"], cwd=path, check=True)
    (path / "source.txt").write_text("source\n")
    subprocess.run(["git", "add", "source.txt"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-qm", "baseline"], cwd=path, check=True)


def write_manifest(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "schema": 1,
                "feature_name": "feature",
                "phase": "red",
                "iteration": 1,
                "criteria": [
                    {"id": "scope", "text": "Only planned paths changed.", "blocking": True}
                ],
            }
        )
    )


def test_freeze_detects_declared_input_changes_but_ignores_outputs(tmp_path: Path) -> None:
    init_repo(tmp_path)
    manifest = tmp_path / "criteria.json"
    receipt = tmp_path / "receipt.json"
    manifest_rel = "criteria.json"
    receipt.write_text("receipt\n")
    write_manifest(manifest)

    module = load_module()
    bundle_path = tmp_path / "bundle.json"
    module.freeze(
        tmp_path,
        bundle_path,
        "feature",
        "red",
        1,
        manifest,
        None,
        ["receipt.json"],
    )
    (tmp_path / "audit.json").write_text("review output\n")
    assert module.verify_bundle_file(bundle_path, tmp_path)["status"] == "accepted"

    receipt.write_text("changed receipt\n")
    result = module.verify_bundle_file(bundle_path, tmp_path)
    assert result["status"] == "rejected"
    assert "changed:receipt.json" in result["errors"]
    assert manifest_rel in json.loads(bundle_path.read_text())["files"]
