#!/usr/bin/env python3
# Tests compact_redundancy.py: candidate preservation, raw pointers and explicit malformed/missing-output handling.

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))

from compact_redundancy import build_index, indexed_knip


class CompactIndexTests(unittest.TestCase):
    def test_reporter_shapes_and_duplicate_raw_locations(self) -> None:
        grouped = {"issues": [{"file": "src/a.ts", "files": [{"name": "src/a.ts"}],
                               "exports": [{"name": "f"}, {"name": "f"}], "types": ["T"]}]}
        legacy = {"file": "src/a.ts", "files": ["src/a.ts"], "exports": ["f"], "types": ["T"]}
        normalized = indexed_knip(grouped)
        self.assertEqual(set(normalized), set(indexed_knip(legacy)))
        self.assertEqual(normalized[("src/a.ts", "exports", "f")], ["/issues/0/exports/0", "/issues/0/exports/1"])
        self.assertEqual(indexed_knip({"issues": []}), {})

    def test_unknown_or_malformed_reporter_fails_explicitly(self) -> None:
        bad_payloads: list[dict[str, Any]] = [{}, {"issues": {}}, {"issues": [None]}, {"files": "wrong"}, {"files": [7]}, {"files": [{}]}]
        for payload in bad_payloads:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                indexed_knip(payload)

    def test_missing_summary_cannot_be_a_clean_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = build_index(Path(directory))
            self.assertEqual(result["index_status"], "incomplete")
            self.assertTrue(result["errors"])

    def test_partial_tools_preserve_candidates_and_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "raw/jscpd_report").mkdir(parents=True)
            documents: dict[str, Any] = {
                "summary.json": {"repo": "/repo", "scope": ["src/a.ts"], "coverage": {"complete": False}, "results": [{"name": "knip_dead_code", "status": "findings", "exit_code": 1}],
                                 "agent_interpretation": {"private": "not tool evidence"}},
                "raw/knip_dead_code.json": {"issues": [{"file": "src/a.ts", "exports": [{"name": "f"}]}]},
                "raw/knip_production.json": {"issues": [{"file": "src/a.ts", "exports": [{"name": "f"}, {"name": "g"}]}]},
                "raw/behavioral_redundancy.json": {"status": "partial", "omissions": [{"file": "missing.ts"}], "findings": [{"type": "future_kind", "at": {"file": "src/a.ts", "line": 4}}]},
                "raw/jscpd_report/jscpd-report.json": {"duplicates": [{"firstFile": {"name": "a.ts", "start": 2}, "secondFile": {"name": "b.ts", "start": 3}, "fragment": "large source"}]},
            }
            # Synthetic tool fixtures are generated data, not edits to repository source.
            for relative, payload in documents.items():
                (root / relative).write_text(json.dumps(payload))
            result = build_index(root)
            self.assertEqual(result["index_status"], "complete")
            self.assertFalse(result["detector_coverage"]["complete"])
            self.assertEqual(len(result["knip"]), 2)
            self.assertEqual(set(result["knip"][0]["raw"]), {"normal", "production"})
            self.assertEqual(set(result["knip"][1]["raw"]), {"production"})
            self.assertEqual(result["behavioral"]["findings"][0]["candidate"], documents["raw/behavioral_redundancy.json"]["findings"][0])
            self.assertEqual(result["clones"][0]["raw"], "/duplicates/0")
            self.assertNotIn("agent_interpretation", result)
            documents["raw/knip_production.json"]["issues"].extend([
                {"file": "src/a.tsx", "exports": [{"name": "outside"}]},
                {"file": "tests/test.ts", "exports": [{"name": "fixture"}]},
                {"exports": [{"name": "unknown"}]}])
            (root / "raw/knip_production.json").write_text(json.dumps(documents["raw/knip_production.json"]))
            scoped = build_index(root, True)
            self.assertEqual(scoped["knip_scope"]["excluded"], 2)
            self.assertEqual(scoped["knip_scope"]["unknown_location_retained"], 1)
            self.assertEqual(len(scoped["knip"]), 3)
            self.assertNotIn("fragment", scoped["clones"][0])
            (root / "raw/knip_production.json").write_text("malformed")
            result = build_index(root)
            self.assertEqual(result["index_status"], "incomplete")
            self.assertFalse(result["knip_comparison_available"])
            self.assertEqual(len(result["knip"]), 1)


if __name__ == "__main__":
    unittest.main()
