import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "architecture_graph.py"
spec = importlib.util.spec_from_file_location("architecture_graph", SCRIPT)
graph = importlib.util.module_from_spec(spec)
spec.loader.exec_module(graph)


class ArchitectureTests(unittest.TestCase):
    def test_empty_graph(self):
        result = graph.analyze({"modules": [], "summary": {"violations": []}})
        self.assertEqual(result["findings"], [])
        self.assertEqual(result["graph"], {"nodes": 0, "edges": 0})

    def test_cycles_and_degree_are_structural_only(self):
        data = {"modules": [
            {"source": "a.ts", "dependencies": [{"resolved": "b.ts"}]},
            {"source": "b.ts", "dependencies": [{"resolved": "a.ts"}]},
        ], "summary": {"violations": []}}
        result = graph.analyze(data, max_degree=1)
        kinds = {item["category"] for item in result["findings"]}
        self.assertEqual(kinds, {"dependency_cycle", "high_fan_in", "high_fan_out"})
        self.assertEqual(result["enforced_violations"], 0)
        self.assertTrue(all(f["classification"] != "confirmed_contract_violation"
                            for f in result["findings"]))

    def test_duplicate_edges_not_double_counted(self):
        data = {"modules": [{"source": "a", "dependencies": [{"resolved": "b"}, {"resolved": "b"}]}]}
        self.assertEqual(graph.analyze(data)["graph"]["edges"], 1)

    def test_rule_violation_is_confirmed_only_with_rule(self):
        data = {"modules": [], "summary": {"violations": [
            {"from": "src/domain/a.ts", "to": "src/db/a.ts",
             "rule": {"name": "no-domain-to-db", "severity": "error"}}
        ]}}
        result = graph.analyze(data)
        self.assertEqual(result["enforced_violations"], 1)
        self.assertEqual(result["findings"][0]["evidence"]["rule"], "no-domain-to-db")

    def test_warning_contract_is_nonblocking(self):
        data = {"modules": [], "summary": {"violations": [
            {"from": "a", "to": "b", "rule": {"name": "advisory", "severity": "warn"}}
        ]}}
        result = graph.analyze(data)
        self.assertEqual(result["enforced_violations"], 0)
        self.assertEqual(result["findings"][0]["classification"], "confirmed_contract_violation")

    def test_invalid_graph_is_not_clean(self):
        with self.assertRaises(ValueError):
            graph.analyze({})
        with self.assertRaises(ValueError):
            graph.analyze({"modules": [{}]})
        with self.assertRaises(ValueError):
            graph.analyze({"modules": [], "summary": {"violations": [{"from": "a"}]}})

    def test_stable_identifiers(self):
        data = {"modules": [{"source": "a", "dependencies": [{"resolved": "b"}]},
                            {"source": "b", "dependencies": [{"resolved": "a"}]}]}
        self.assertEqual(graph.analyze(data)["findings"], graph.analyze(data)["findings"])

    def test_large_cycle_does_not_depend_on_python_recursion_limit(self):
        data = {'modules': [{'source': str(i), 'dependencies': [{'resolved': str((i + 1) % 2000)}]}
                            for i in range(2000)]}
        result = graph.analyze(data)
        self.assertEqual(len(result['findings']), 1)
        self.assertEqual(len(result['findings'][0]['evidence']['members']), 2000)

    def test_distinct_configured_rules_keep_distinct_ids(self):
        result = graph.analyze({'modules': [], 'summary': {'violations': [
            {'from': 'a', 'to': 'b', 'rule': {'name': 'rule-' + str(i), 'severity': 'error'}}
            for i in range(2)]}})
        self.assertEqual(len({f['id'] for f in result['findings']}), 2)
        self.assertEqual(result['enforced_violations'], 2)


if __name__ == "__main__":
    unittest.main()
