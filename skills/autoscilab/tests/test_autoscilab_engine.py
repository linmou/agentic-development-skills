# Tests the domain-agnostic AutoSciLab engine against a toy environment in tests/fixtures.
# Requires numpy and scipy. Run: python -m unittest discover -s skills/autoscilab/tests -v

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
ENGINE = TESTS.parent / "scripts" / "autoscilab_engine.py"
FIXTURES = TESTS / "fixtures"


def toy_env(**overrides):
    env = json.loads((FIXTURES / "toy_environment.json").read_text())
    env["oracle"]["command"] = f"{sys.executable} {FIXTURES / 'toy_oracle.py'}"
    env.update(overrides)
    return env


class EngineTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.workdir = self.tmp / "run"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_engine(self, *args, expect=0):
        proc = subprocess.run([sys.executable, str(ENGINE), *args], capture_output=True, text=True)
        self.assertEqual(proc.returncode, expect, msg=proc.stdout + proc.stderr)
        return json.loads(proc.stdout)

    def init(self, env=None):
        return self.run_engine("init", "--workdir", str(self.workdir), "--spec-json", json.dumps(env or toy_env()))

    def copy_models(self, *names):
        for n in names:
            shutil.copy(FIXTURES / "models" / f"{n}.py", self.workdir / "models" / f"{n}.py")

    def observe(self, points, expect=0):
        return self.run_engine("observe", "--workdir", str(self.workdir), "--experiments-json", json.dumps(points),
                               expect=expect)

    def screening(self):
        pts = [{"x1": x, "x2": 0.0, "mode": m} for x in (0.02, 0.1, 0.5, 2.0, 8.0) for m in ("a", "b")]
        pts.append({"x1": 0.5, "x2": 0.9, "mode": "a"})
        return self.observe(pts)


class EnvironmentSpecTests(EngineTestCase):
    def test_valid_toy_spec(self):
        out = self.run_engine("validate-env", "--spec-json", json.dumps(toy_env()))
        self.assertTrue(out["valid"], out)

    def test_rejects_bad_specs(self):
        bad = toy_env(budget=0)
        bad["inputs"].append({"name": "x1", "bounds": [1, 0]})
        bad["target"] = {"representation": "equation"}
        out = self.run_engine("validate-env", "--spec-json", json.dumps(bad), expect=1)
        joined = " ".join(out["errors"])
        for fragment in ("budget", "duplicate input", "bounds", "output_format"):
            self.assertIn(fragment, joined)

    def test_log_scale_needs_positive_bounds(self):
        bad = toy_env()
        bad["inputs"][1]["scale"] = "log"
        out = self.run_engine("validate-env", "--spec-json", json.dumps(bad), expect=1)
        self.assertTrue(any("log scale" in e for e in out["errors"]))


class ObserveTests(EngineTestCase):
    def test_oracle_records_and_budget(self):
        self.init()
        out = self.observe([{"x1": 1.0, "x2": 0.0, "mode": "b"}])
        self.assertAlmostEqual(out["recorded"][0]["observables"]["y"], 6.0 / 1.5)
        self.assertEqual(out["budget_remaining"], 19)

    def test_batch_over_budget_queries_nothing(self):
        self.init(toy_env(budget=2))
        out = self.observe([{"x1": 1.0, "x2": 0.0, "mode": "a"}] * 3, expect=2)
        self.assertEqual(out["budget_remaining"], 2)
        status = self.run_engine("status", "--workdir", str(self.workdir))
        self.assertEqual(status["queries_used"], 0)

    def test_rejects_out_of_domain_inputs(self):
        self.init()
        self.observe([{"x1": 50.0, "x2": 0.0, "mode": "a"}], expect=1)
        self.observe([{"x1": 1.0, "x2": 0.0, "mode": "c"}], expect=1)
        self.observe([{"x1": 1.0, "mode": "a"}], expect=1)

    def test_manual_records_only_without_oracle(self):
        env = toy_env()
        del env["oracle"]
        self.init(env)
        out = self.observe([{"inputs": {"x1": 1.0, "x2": 0.0, "mode": "a"}, "observables": {"y": 2.0}}])
        self.assertEqual(out["recorded"][0]["source"], "manual")

    def test_contrasts_are_one_factor_pairs(self):
        self.init()
        self.screening()
        status = self.run_engine("status", "--workdir", str(self.workdir))
        inputs = {c["input"] for c in status["one_factor_contrasts"]}
        self.assertTrue({"x1", "x2", "mode"} <= inputs)


class FitAndLoopTests(EngineTestCase):
    def test_correct_structure_wins_and_gate_reports_confidence(self):
        self.init()
        self.screening()
        self.copy_models("saturating", "power", "linear")
        out = self.run_engine("fit", "--workdir", str(self.workdir), "--models", "saturating,power,linear",
                              "--loss", "log_mse", "--n-boot", "10")
        self.assertEqual(out["ranking"][0], "saturating")
        self.assertAlmostEqual(out["hypotheses"]["saturating"]["params"]["K"], 0.5, places=3)
        self.assertGreaterEqual(out["confidence"], 0.9)
        self.assertEqual(out["acquisition_mode"], "refine")

    def test_single_hypothesis_stays_in_disambiguate(self):
        self.init()
        self.screening()
        self.copy_models("saturating")
        out = self.run_engine("fit", "--workdir", str(self.workdir), "--models", "saturating", "--loss", "mse")
        self.assertIsNone(out["confidence"])
        self.assertEqual(out["acquisition_mode"], "disambiguate")
        self.assertTrue(out["warnings"])

    def test_broken_model_is_reported(self):
        self.init()
        self.screening()
        self.copy_models("broken")
        out = self.run_engine("fit", "--workdir", str(self.workdir), "--models", "broken", "--loss", "mse", expect=1)
        self.assertIn("predict", out["error"])

    def test_log_loss_needs_positive_data(self):
        env = toy_env()
        del env["oracle"]
        self.init(env)
        self.observe([{"inputs": {"x1": 1.0, "x2": 0.0, "mode": "a"}, "observables": {"y": -1.0}}])
        self.copy_models("linear")
        self.run_engine("fit", "--workdir", str(self.workdir), "--models", "linear", "--loss", "log_mse", expect=1)

    def test_full_loop_passes_audit(self):
        self.init()
        self.screening()
        self.copy_models("saturating", "power")
        self.run_engine("fit", "--workdir", str(self.workdir), "--models", "saturating,power", "--loss", "log_mse",
                        "--n-boot", "5")
        acq = self.run_engine("acquire", "--workdir", str(self.workdir), "--mode", "disambiguate",
                              "--n-experiments", "3", "--regions-json",
                              json.dumps([{"bounds": {"x1": [0.01, 0.05]}, "fixed": {"x2": 0.0},
                                           "rationale": "low-x1 tail separates saturation from power law"}]))
        self.assertEqual(len(acq["selected"]), 3)
        for s in acq["selected"]:
            self.assertLessEqual(s["inputs"]["x1"], 0.05)
            self.assertEqual(s["inputs"]["x2"], 0.0)
            self.assertEqual(set(s["predictions_by_hypothesis"]), {"saturating", "power"})
        obs = self.observe([s["inputs"] for s in acq["selected"]])
        self.assertEqual(len(obs["prediction_checks"]), 3)
        self.run_engine("memory", "--workdir", str(self.workdir), "--memory-json",
                        json.dumps({"falsified_hypotheses": [{"hypothesis": "power", "evidence": "low-x1 checks"}],
                                    "inactive_inputs": ["x2"]}))
        fin = self.run_engine("finalize", "--workdir", str(self.workdir), "--selection-json", json.dumps(
            {"model": "saturating", "mechanism": {"expression": "vmax[mode] * x1 / (K + x1)"},
             "rationale": "lowest BIC and survived the low-x1 test"}))
        self.assertEqual(fin["status"], "completed", fin)
        result = json.loads((self.workdir / "final_result.json").read_text())
        self.assertTrue(result["audit"]["passed"])
        self.assertIn("def predict", result["model"]["source"])

    def test_audit_fails_without_acquire_or_memory(self):
        self.init()
        self.screening()
        self.copy_models("saturating", "power")
        self.run_engine("fit", "--workdir", str(self.workdir), "--models", "saturating,power", "--loss", "mse",
                        "--n-boot", "0")
        fin = self.run_engine("finalize", "--workdir", str(self.workdir), "--selection-json", json.dumps(
            {"model": "saturating", "mechanism": "x", "rationale": "r"}), expect=1)
        failed = {c["check"] for c in fin["audit"]["checks"] if not c["passed"]}
        self.assertEqual(failed, {"multiple_observe_rounds", "hypothesis_conditioned_experiments", "memory_updated"})

    def test_audit_detects_edited_observations(self):
        self.init()
        self.screening()
        path = self.workdir / "observations.json"
        data = json.loads(path.read_text())
        data[0]["observables"]["y"] = 123.0
        path.write_text(json.dumps(data))
        audit = self.run_engine("audit", "--workdir", str(self.workdir), expect=1)
        failed = {c["check"] for c in audit["checks"] if not c["passed"]}
        self.assertIn("ledger_matches_observations", failed)

    def test_cluster_entropy(self):
        self.init()
        out = self.run_engine("cluster", "--workdir", str(self.workdir), "--structures-json",
                              json.dumps(["a * x", "a  *\tx", "b / x", "c + x"]), "--prev-entropy", "1.45")
        self.assertEqual(out["clusters"][0]["count"], 2)
        self.assertAlmostEqual(out["entropy_bits"], 1.5, places=4)
        self.assertTrue(out["converged"])


if __name__ == "__main__":
    unittest.main()
