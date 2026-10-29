"""Known-answer tests for scripts/check_contracts.py.

Intent: every mechanical verdict the skill relies on has a case that would flip if the checker regressed.
Run: python -m unittest discover -s skills/skill-contract/tests -v
"""

from __future__ import annotations

import copy
import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import check_contracts as cc  # noqa: E402

CONTRACT = {
    "contract_format": "skill-contract/1",
    "skill": "note-store",
    "version": "1.2.0",
    "capability": "Store a plain-text note and return its id.",
    "prose_contract": "SKILL.md",
    "request": {
        "type": "object",
        "required": ["text"],
        "additionalProperties": False,
        "properties": {
            "text": {"type": "string", "minLength": 1},
            "tags": {"type": "array", "items": {"type": "string"}},
            "caller_tag": {"type": "string"},
        },
    },
    "response": {
        "type": "object",
        "required": ["status"],
        "properties": {"status": {"enum": ["ok", "error"]}, "note_id": {"type": ["string", "null"]}},
    },
    "status_field": "status",
    "statuses": ["ok", "error"],
    "writes": [{"store": "notes", "location": "notes/<note_id>.json"}],
    "changes": [{"version": "1.2.0", "note": "Add tags."}],
}

CALLER_MD = """\
---
name: meeting-notes
description: >
  Run a meeting-notes session and save each summary as a note.
metadata:
  requires: {requires}
---

# Meeting Notes

1. Collect the summary.
2. Invoke `note-store`. On `ok` report the id; on `error` show the errors.
"""

EXAMPLE = {
    "case": "save summary",
    "request": {"text": "Ship the beta on Friday.", "tags": ["release"]},
    "provenance": {"text": "summary from step 1", "tags": "fixed tag in step 2"},
}


class Workspace:
    def __init__(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def close(self) -> None:
        self._tmp.cleanup()

    def skill(self, name: str, body: str | None = None) -> Path:
        folder = self.root / name
        folder.mkdir(parents=True, exist_ok=True)
        text = body if body is not None else f"---\nname: {name}\ndescription: test skill\n---\n\n# {name}\n"
        (folder / "SKILL.md").write_text(text, encoding="utf-8")
        return folder

    def callee(self, contract: dict | None = None) -> Path:
        folder = self.skill("note-store")
        (folder / "contract.json").write_text(json.dumps(contract or CONTRACT), encoding="utf-8")
        return folder

    def caller(self, requires: str = "note-store@^1.0.0", example: dict | None = EXAMPLE,
               body: str | None = None) -> Path:
        folder = self.skill("meeting-notes", body or CALLER_MD.format(requires=requires))
        if example is not None:
            calls = folder / "references" / "calls" / "note-store"
            calls.mkdir(parents=True, exist_ok=True)
            (calls / "save.json").write_text(json.dumps(example), encoding="utf-8")
        return folder


def codes(findings: list[cc.Finding], severity: str | None = None) -> set[str]:
    return {f.code for f in findings if severity is None or f.severity == severity}


class CheckContractsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.ws = Workspace()

    def tearDown(self) -> None:
        self.ws.close()

    def run_check(self, **kwargs) -> list[cc.Finding]:
        return cc.check([self.ws.root], **kwargs)

    def test_conforming_pair_passes(self) -> None:
        self.ws.callee()
        self.ws.caller()
        findings = self.run_check()
        self.assertEqual(cc.verdict(findings), "pass", cc.render(findings))
        self.assertEqual(codes(findings, "warn"), set())

    def test_version_range_excludes_contract(self) -> None:
        self.ws.callee()
        self.ws.caller(requires="note-store@~1.1.0")
        self.assertIn("version-mismatch", codes(self.run_check(), "error"))

    def test_unresolved_callee(self) -> None:
        self.ws.caller(requires="ghost-skill@^1.0.0", example=None)
        self.assertIn("requires-unresolved", codes(self.run_check(), "error"))

    def test_callee_without_contract_is_insufficient(self) -> None:
        self.ws.skill("note-store")
        self.ws.caller()
        findings = self.run_check()
        self.assertEqual(cc.verdict(findings), "insufficient_evidence")
        self.assertIn("callee-no-contract", codes(findings))

    def test_missing_example_is_insufficient(self) -> None:
        self.ws.callee()
        self.ws.caller(example=None)
        findings = self.run_check()
        self.assertEqual(cc.verdict(findings), "insufficient_evidence")
        self.assertIn("no-call-example", codes(findings))

    def test_example_failing_schema(self) -> None:
        self.ws.callee()
        bad = copy.deepcopy(EXAMPLE)
        bad["request"]["priority"] = "high"
        bad["provenance"]["priority"] = "invented"
        self.ws.caller(example=bad)
        findings = self.run_check()
        self.assertIn("example-invalid", codes(findings, "error"))

    def test_provenance_must_cover_every_field(self) -> None:
        self.ws.callee()
        partial = copy.deepcopy(EXAMPLE)
        del partial["provenance"]["tags"]
        self.ws.caller(example=partial)
        messages = [f.message for f in self.run_check() if f.code == "provenance-missing"]
        self.assertTrue(any("tags[]" in m for m in messages), messages)

    def test_provenance_prefix_covers_subtree(self) -> None:
        self.assertEqual(cc.uncovered({"entry.design.controls", "entry.kind"}, {"entry": "plan facts"}), [])
        self.assertEqual(cc.uncovered({"entry.commands[].command"}, {"entry.commands": "run records"}), [])
        self.assertEqual(cc.uncovered({"entry.kind"}, {"entry.kin": "typo"}), ["entry.kind"])

    def test_unmentioned_status_warns(self) -> None:
        self.ws.callee()
        body = CALLER_MD.format(requires="note-store@^1.0.0").replace("on `error` show the errors", "otherwise stop")
        self.ws.caller(body=body)
        findings = self.run_check()
        self.assertIn("status-unmentioned", codes(findings, "warn"))
        self.assertEqual(cc.verdict(findings), "pass")

    def test_undeclared_caller_warns(self) -> None:
        self.ws.callee()
        self.ws.skill("standup", "---\nname: standup\ndescription: x\n---\n\nSave the notes with `$note-store`.\n")
        self.assertIn("undeclared-caller", codes(self.run_check(), "warn"))

    def test_dual_writer_fails(self) -> None:
        self.ws.callee()
        other = dict(CONTRACT, skill="note-mirror", writes=[{"store": "notes", "location": "mirror/"}])
        folder = self.ws.skill("note-mirror")
        (folder / "contract.json").write_text(json.dumps(other), encoding="utf-8")
        self.assertIn("dual-writer", codes(self.run_check(), "error"))

    def test_invalid_contract_reports_problems(self) -> None:
        broken = dict(CONTRACT, version="one", statuses=["ok"])
        broken["request"] = dict(CONTRACT["request"], pattern="^x")
        self.ws.callee(broken)
        messages = " | ".join(f.message for f in self.run_check() if f.code == "contract-invalid")
        self.assertIn("not MAJOR.MINOR.PATCH", messages)
        self.assertIn("unsupported keyword 'pattern'", messages)
        self.assertIn("differ from response status enum", messages)

    def test_impact_breaking_change_without_major(self) -> None:
        self.ws.callee()
        self.ws.caller()
        proposed = copy.deepcopy(CONTRACT)
        proposed["version"] = "1.3.0"
        proposed["request"]["properties"]["tags"] = {"type": "string"}
        proposed["changes"].append({"version": "1.3.0", "note": "tags becomes a string"})
        path = self.ws.root / "proposed.json"
        path.write_text(json.dumps(proposed), encoding="utf-8")
        findings = self.run_check(proposed=path)
        self.assertIn("breaking-without-major", codes(findings, "error"))
        self.assertIn("example-invalid", codes(findings, "error"))

    def test_impact_major_bump_flags_ranges_not_semver(self) -> None:
        self.ws.callee()
        self.ws.caller()
        proposed = copy.deepcopy(CONTRACT)
        proposed["version"] = "2.0.0"
        proposed["statuses"] = ["ok", "error", "queued"]
        proposed["response"]["properties"]["status"] = {"enum": ["ok", "error", "queued"]}
        proposed["changes"].append({"version": "2.0.0", "note": "async writes"})
        path = self.ws.root / "proposed.json"
        path.write_text(json.dumps(proposed), encoding="utf-8")
        findings = self.run_check(proposed=path)
        self.assertIn("version-mismatch", codes(findings, "error"))
        self.assertNotIn("breaking-without-major", codes(findings))
        self.assertIn("status-added", codes(findings, "warn"))
        self.assertIn("status-unmentioned", codes(findings, "warn"))

    def test_symlinked_roots_are_deduplicated(self) -> None:
        self.ws.callee()
        self.ws.caller()
        links = self.ws.root / "links"
        links.mkdir()
        (links / "note-store").symlink_to(self.ws.root / "note-store")
        findings = cc.check([self.ws.root, links])
        self.assertNotIn("duplicate-skill", codes(findings))

    def test_ranges(self) -> None:
        cases = [
            ("^1.2.0", "1.9.9", True), ("^1.2.0", "2.0.0", False), ("^0.2.0", "0.3.0", False),
            ("~1.2.0", "1.2.7", True), ("~1.2.0", "1.3.0", False), (">=1.0.0 <2.0.0", "1.5.0", True),
            ("=1.2.0", "1.2.1", False), ("1.2", "1.2.0", True), ("*", "9.9.9", True),
        ]
        for rng, version, expected in cases:
            with self.subTest(rng=rng, version=version):
                self.assertEqual(cc.satisfies(cc.parse_version(version), cc.parse_range(rng)), expected)
        self.assertIsNone(cc.parse_range("^one"))

    def test_frontmatter_block_scalar_and_metadata(self) -> None:
        data = cc.parse_frontmatter(textwrap.dedent("""\
            ---
            name: a
            description: >
              long text: with a colon
            metadata:
              requires: "b@^1.0.0, c"
            ---
            """))
        self.assertEqual(data["name"], "a")
        self.assertEqual(cc.parse_requires(data["metadata"]["requires"]), [("b", "^1.0.0"), ("c", "*")])


class RepositoryContractsTest(unittest.TestCase):
    """The repository's own contracts and callers must pass the checker."""

    def test_repository_skills(self) -> None:
        skills_root = Path(__file__).resolve().parents[2]
        findings = cc.check([skills_root])
        errors = [f for f in findings if f.severity in ("error", "insufficient")]
        self.assertEqual(errors, [], cc.render(findings))


if __name__ == "__main__":
    unittest.main()
