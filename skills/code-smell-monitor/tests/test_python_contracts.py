"""Offline Python architectural contract enforcement tests."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
spec = importlib.util.spec_from_file_location("python_contracts", SCRIPTS / "python_contracts.py")
contracts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contracts)


class PythonContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)

    def write(self, name, content):
        path = self.repo / name
        path.write_text(content)
        return path

    def test_missing_rules_not_inferred(self):
        self.assertEqual(contracts.discover(self.repo)["status"], "not_configured")

    def test_configured_contracts(self):
        self.write(".importlinter", "[importlinter]\nroot_package=app\n\n"
                   "[importlinter:contract:domain]\nname=Domain boundary\ntype=forbidden\n")
        conf = contracts.discover(self.repo)
        self.assertEqual(conf["status"], "configured")
        self.assertEqual(conf["contracts"][0]["id"], "domain")

    def test_broken_contract_is_evidence_not_guess(self):
        self.write(".importlinter", "[importlinter]\nroot_package=app\n\n"
                   "[importlinter:contract:domain]\nname=Domain boundary\ntype=forbidden\n")
        conf = contracts.discover(self.repo)
        result = contracts.classify({"cmd": ["lint-imports"], "exit_code": 1,
            "timed_out": False, "stdout": "Domain boundary BROKEN\n\nBroken contracts\n\nContracts: 0 kept, 1 broken\n",
            "stderr": ""}, conf)
        self.assertEqual(result["status"], "violations")
        self.assertEqual(result["enforced_violations"], 1)

    def test_malformed_output_is_not_confirmed(self):
        self.write(".importlinter", "[importlinter]\nroot_package=app\n\n"
                   "[importlinter:contract:domain]\nname=Domain boundary\ntype=forbidden\n")
        conf = contracts.discover(self.repo)
        result = contracts.classify({"cmd": ["lint-imports"], "exit_code": 1,
            "timed_out": False, "stdout": "Some imports failed", "stderr": ""}, conf)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["enforced_violations"], 0)


if __name__ == "__main__":
    unittest.main()
