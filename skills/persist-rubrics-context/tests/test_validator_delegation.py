#!/usr/bin/env python3
# Tests persist-rubrics-context/scripts/validate_rubric_memory.py delegates rubric-file
# checks to rubric-construction (in place and as a bootstrapped standalone copy).

import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
HOST_SCRIPT = ROOT / "scripts" / "validate_rubric_memory.py"
BOOTSTRAP = ROOT / "scripts" / "bootstrap_memory_artifacts.sh"

VALID: dict[str, Any] = {
    "id": "RUB-SHORT-COMMITS",
    "title": "Commit subject brevity",
    "applicability": {"include": ["git commit subjects"], "exclude": ["commit bodies"]},
    "decision_rule": {
        "score_3_rule": "Subject <= 50 chars.",
        "score_3_support_examples": ["Fix index path check"],
        "score_3_counter_examples": [["N/A for top (+)", "Subject of 61 chars (-)"]],
        "score_1_rule": "Subject > 50 chars.",
        "score_1_support_examples": ["A 61-char subject"],
        "score_1_counter_examples": [["A 48-char subject (+)", "N/A for bottom (-)"]],
    },
    "dependencies": {
        "context_refs": ["Reviewers scan git log --oneline."],
        "intent_refs": ["Keep history easy to scan."],
    },
    "lifecycle": {"sunset_condition": ""},
}


def with_empty(section: str, key: str) -> dict[str, Any]:
    data = copy.deepcopy(VALID)
    data[section][key] = []
    return data


def make_memory(root: Path, entry: dict[str, Any], index_id: str) -> None:
    rubrics = root / ".co-improvement" / "learnt" / "rubrics"
    (rubrics / "workflow").mkdir(parents=True)
    (root / ".co-improvement" / "learnt" / "contexts").mkdir(parents=True)
    (rubrics / "workflow" / "rub.json").write_text(json.dumps(entry), encoding="utf-8")
    row = {
        "id": index_id,
        "path": "./.co-improvement/learnt/rubrics/workflow/rub.json",
        "status": "active",
        "intent_keywords": ["scan"],
        "context_keywords": ["git"],
        "applicability_summary": "commit subjects",
    }
    (rubrics / "index.json").write_text(json.dumps([row]), encoding="utf-8")


def run_host(script: Path, root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), "--project-root", str(root)], capture_output=True, text=True
    )


class ValidatorDelegationTest(unittest.TestCase):
    def test_valid_memory_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            make_memory(Path(tmp), VALID, "RUB-SHORT-COMMITS")
            result = run_host(HOST_SCRIPT, Path(tmp))
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_entry_gate_failure_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            make_memory(Path(tmp), with_empty("applicability", "exclude"), "RUB-SHORT-COMMITS")
            result = run_host(HOST_SCRIPT, Path(tmp))
        self.assertEqual(result.returncode, 1)
        self.assertIn("applicability.exclude must be non-empty string list", result.stdout)

    def test_id_mismatch_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            make_memory(Path(tmp), VALID, "RUB-OTHER")
            result = run_host(HOST_SCRIPT, Path(tmp))
        self.assertEqual(result.returncode, 1)
        self.assertIn("id mismatch", result.stdout)

    def test_bootstrapped_copy_runs_without_skill_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "copied"
            subprocess.run(["bash", str(BOOTSTRAP), str(target)], check=True, capture_output=True)
            self.assertTrue((target / "validate_rubric_entry.py").is_file())
            isolated = Path(tmp) / "isolated"
            shutil.copytree(target, isolated)
            project = Path(tmp) / "proj"
            make_memory(project, with_empty("dependencies", "context_refs"), "RUB-SHORT-COMMITS")
            result = run_host(isolated / "validate_rubric_memory.py", project)
        self.assertEqual(result.returncode, 1)
        self.assertIn("dependencies.context_refs", result.stdout)


if __name__ == "__main__":
    unittest.main()
