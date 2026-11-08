"""Offline regression tests for production-only Knip reporting.

Run: python3 -m unittest discover -s skills/code-smell-monitor/tests -p 'test_*.py'
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "code_smell_monitor.py"
spec = importlib.util.spec_from_file_location("code_smell_monitor_redundancy", SCRIPT)
assert spec and spec.loader
monitor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor)


class KnipProductionTests(unittest.TestCase):
    def test_runner_launches_both_knip_modes_without_mutating_tests(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            (repo / "package.json").write_text('{"name":"fixture"}')
            raw = repo / "raw"

            def fake_runner(_repo, tool, args, _install):
                return [tool, *args]

            def fake_command(command, _repo, timeout=300):
                payload = {"issues": [{"file": "src/legacy.ts", "exports": [{"name": "legacy"}]}]}
                return {"cmd": command, "exit_code": 0, "stdout": json.dumps(payload),
                        "stderr": "", "duration_seconds": 0.01, "timed_out": False}

            with patch.object(monitor, "node_runner", side_effect=fake_runner), \
                 patch.object(monitor, "run_command", side_effect=fake_command):
                results = monitor.run_js_checks(repo, ["src"], raw, True, "never")
            knip = [item for item in results if item["name"].startswith("knip_")]
            self.assertEqual({item["name"] for item in knip},
                             {"knip_dead_code", "knip_production"})
            self.assertIn("--production", next(item for item in knip if
                          item["name"] == "knip_production")["cmd"])
            self.assertNotIn("--production", next(item for item in knip if
                          item["name"] == "knip_dead_code")["cmd"])
            self.assertTrue((raw / "knip_production.json").exists())
            self.assertTrue((raw / "knip_dead_code.json").exists())

    def test_production_only_export_candidate_and_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = root / "raw"
            raw.mkdir()
            (raw / "knip_dead_code.json").write_text('{"issues":[]}')
            (raw / "knip_production.json").write_text(
                '{"issues":[{"file":"src/legacy.ts","exports":[{"name":"legacy"}]}]}')
            headings = monitor.extract_headlines(raw)
            self.assertEqual(headings["knip_production_only_candidates"], [
                {"file": "src/legacy.ts", "category": "exports", "symbol": "legacy"}])
            self.assertEqual(headings["knip_production_findings"]["exports"], 1)
            summary = {"repo": str(root), "scope": ["."], "stack": {"javascript": True},
                       "out_dir": str(root), "coverage": {"complete": True,
                       "categories": {"production_reachability": "covered"}},
                       "headlines": headings}
            monitor.write_report(root, summary, [], [])
            self.assertIn("knip_production_only_candidates",
                          (root / "code_smell_report.md").read_text())

    def test_no_candidate_without_both_valid_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory)
            (raw / "knip_production.json").write_text('{"issues":[]}')
            self.assertNotIn("knip_production_only_candidates",
                             monitor.extract_headlines(raw))

    def test_nonzero_findings_and_missing_production_tool(self):
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory)
            (raw / "knip_production.json").write_text('{"issues":[]}')
            report = {"name": "knip_production", "exit_code": 1, "timed_out": False}
            self.assertEqual(monitor.detector_status(report, raw), "findings")
            unavailable = {"name": "knip_production", "exit_code": 127, "timed_out": False}
            self.assertEqual(monitor.detector_status(unavailable, raw), "unavailable")
            covered = monitor.coverage_status([
                {"name": "knip_dead_code", "status": "clean"},
                {"name": "knip_production", "status": "unavailable"}])
            self.assertEqual(covered["categories"]["production_reachability"], "unavailable")
            self.assertFalse(covered["complete"])

    def test_comparison_does_not_mistake_shared_findings_for_test_only(self):
        data = {"issues": [{"file": "src/common.ts",
                            "exports": [{"name": "unused"}]}]}
        self.assertEqual(monitor.knip_records(data) - monitor.knip_records(data), set())


if __name__ == "__main__":
    unittest.main()
