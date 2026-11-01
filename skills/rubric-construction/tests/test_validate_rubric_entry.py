#!/usr/bin/env python3
# Tests rubric-construction/scripts/validate_rubric_entry.py (gates G1-G4, function + CLI).

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_rubric_entry.py"

_spec = importlib.util.spec_from_file_location("validate_rubric_entry", SCRIPT)
assert _spec and _spec.loader
vre = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vre)

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


def mutate(path: list[str], value: object) -> dict:
    data = copy.deepcopy(VALID)
    node: Any = data
    for key in path[:-1]:
        node = node[key]
    if value is None:
        del node[path[-1]]
    else:
        node[path[-1]] = value
    return data


class ValidateEntryTest(unittest.TestCase):
    def test_valid_entry(self) -> None:
        self.assertEqual(vre.validate_entry(VALID), [])

    def test_non_object_root(self) -> None:
        self.assertEqual(vre.validate_entry([VALID]), ["root must be object"])

    def test_missing_top_key(self) -> None:
        errors = vre.validate_entry(mutate(["lifecycle"], None))
        self.assertTrue(any("missing keys ['lifecycle']" in e for e in errors))

    def test_empty_exclude_fails_g2(self) -> None:
        errors = vre.validate_entry(mutate(["applicability", "exclude"], []))
        self.assertIn("applicability.exclude must be non-empty string list", errors)

    def test_blank_intent_ref_fails_g1(self) -> None:
        errors = vre.validate_entry(mutate(["dependencies", "intent_refs"], ["  "]))
        self.assertIn("dependencies.intent_refs must be non-empty string list", errors)

    def test_no_score_levels(self) -> None:
        errors = vre.validate_entry(mutate(["decision_rule"], {"fail_fast": "x"}))
        self.assertEqual(errors, ["decision_rule has no score_X_rule keys"])

    def test_missing_support_fails_g3(self) -> None:
        errors = vre.validate_entry(mutate(["decision_rule", "score_1_support_examples"], None))
        self.assertIn("score_1_support_examples must be non-empty string list", errors)

    def test_missing_counter_fails_g3(self) -> None:
        errors = vre.validate_entry(mutate(["decision_rule", "score_3_counter_examples"], None))
        self.assertIn("missing score_3_counter_examples", errors)

    def test_flat_counter_list_fails_g4(self) -> None:
        errors = vre.validate_entry(mutate(["decision_rule", "score_3_counter_examples"], ["a", "b"]))
        self.assertIn("score_3_counter_examples[1] must be [counter+, counter-]", errors)

    def test_triple_counter_fails_g4(self) -> None:
        errors = vre.validate_entry(mutate(["decision_rule", "score_3_counter_examples"], [["a", "b", "c"]]))
        self.assertIn("score_3_counter_examples[1] must be [counter+, counter-]", errors)

    def test_empty_counter_side_fails_g4(self) -> None:
        errors = vre.validate_entry(mutate(["decision_rule", "score_3_counter_examples"], [["a", ""]]))
        self.assertIn("score_3_counter_examples[1][1] must be non-empty string", errors)

    def test_levels_sorted_numerically(self) -> None:
        data = mutate(["decision_rule", "score_10_rule"], "")
        errors = vre.validate_entry(data)
        self.assertEqual(errors[0], "score_10_rule must be non-empty string")


class CliTest(unittest.TestCase):
    def test_cli_exit_codes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            good = Path(tmp) / "good.json"
            bad = Path(tmp) / "bad.json"
            good.write_text(json.dumps(VALID), encoding="utf-8")
            bad.write_text("{not json", encoding="utf-8")
            ok = subprocess.run([sys.executable, str(SCRIPT), str(good)], capture_output=True, text=True)
            ko = subprocess.run([sys.executable, str(SCRIPT), str(good), str(bad)], capture_output=True, text=True)
        self.assertEqual(ok.returncode, 0)
        self.assertEqual(ko.returncode, 1)
        self.assertIn("cannot load", ko.stdout)


if __name__ == "__main__":
    unittest.main()
