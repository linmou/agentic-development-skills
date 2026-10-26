#!/usr/bin/env python3
"""Offline regression tests for code-smell-monitor process and coverage semantics."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "code_smell_monitor.py"
spec = importlib.util.spec_from_file_location("code_smell_monitor", SCRIPT)
monitor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor)


class MonitorRuntimeTests(unittest.TestCase):
    def test_missing_executable_is_reported(self):
        result = monitor.run_command(["__nonexistent_code_smell_tool__"], Path.cwd())
        self.assertEqual(result["exit_code"], 127)
        self.assertIn("No such file", result["stderr"])

    def test_timeout_bytes_are_decoded(self):
        error = subprocess.TimeoutExpired(["fake"], 1, output=b"partial ÿ", stderr=b"failed ÿ")
        with mock.patch.object(monitor.subprocess, "run", side_effect=error):
            result = monitor.run_command(["fake"], Path.cwd(), timeout=1)
        self.assertEqual(result["exit_code"], 124)
        self.assertIsInstance(result["stdout"], str)
        self.assertIsInstance(result["stderr"], str)
        self.assertTrue(result["timed_out"])

    def test_findings_are_not_execution_errors(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "ruff.json").write_text('[{"code":"F401"}]')
            self.assertEqual(monitor.detector_status(
                {"name": "ruff", "exit_code": 1, "timed_out": False}, root), "findings")
            self.assertEqual(monitor.detector_status(
                {"name": "ruff", "exit_code": 127, "timed_out": False}, root), "unavailable")
            self.assertEqual(monitor.detector_status(
                {"name": "ruff", "exit_code": 124, "timed_out": True}, root), "timed_out")
            (root / "ruff.json").write_text("not-json")
            self.assertEqual(monitor.detector_status(
                {"name": "ruff", "exit_code": 1, "timed_out": False}, root), "failed")

    def test_partial_coverage_is_not_success(self):
        results = [{"name": "ruff", "status": "clean"},
                   {"name": "radon_cc", "status": "unavailable"}]
        coverage = monitor.coverage_status(results)
        self.assertFalse(coverage["complete"])
        self.assertEqual(coverage["categories"]["complexity"], "partial")

    def test_outside_scope_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            repo = Path(folder) / "repo"
            repo.mkdir()
            (repo / "ok.py").write_text("print('hi')")
            outside = Path(folder) / "outside.py"
            outside.write_text("print('hi')")
            with mock.patch.object(sys, "argv", ["monitor", "--repo", str(repo),
                                                "--scope", str(outside), "--install", "never"]):
                self.assertEqual(monitor.main(), 2)


if __name__ == "__main__":
    unittest.main()
