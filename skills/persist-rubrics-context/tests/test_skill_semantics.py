#!/usr/bin/env python3
# Smoke checks for persist-rubrics-context docs (not TDD-driven skill design).

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL_MD = ROOT / "SKILL.md"
MEMORY = ROOT / "references" / "memory-protocol.md"
CONTRACT = ROOT / "references" / "call-contract.md"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class PersistRubricsContextSemanticsTest(unittest.TestCase):
    def test_frontmatter_name(self) -> None:
        text = read_text(SKILL_MD)
        self.assertIn("name: persist-rubrics-context", text)
        self.assertIn("description:", text)

    def test_call_contract_exists(self) -> None:
        self.assertTrue(CONTRACT.is_file())
        contract = read_text(CONTRACT)
        self.assertIn("Request", contract)
        self.assertIn("Response", contract)
        self.assertIn("output_profile", contract)
        self.assertIn("caller_tag", contract)

    def test_call_contract_v4_fill_paths(self) -> None:
        """v4 lean Request + full write fill-path inventory; no host FSM enums."""
        contract = read_text(CONTRACT)
        self.assertRegex(contract, r"Version:\s*\*\*4\*\*")
        self.assertIn("`intents`", contract)
        self.assertIn("`correlation_id`", contract)
        self.assertIn("Write fill paths", contract)
        self.assertIn("context_keywords", contract)
        self.assertIn("scope.include", contract)
        self.assertIn("rubric-construction", contract)
        self.assertIn("fail-closed", contract.lower())
        self.assertIn("generalize", contract.lower())
        # Request table must not list section_id as a first-class field
        self.assertNotRegex(
            contract,
            r"(?m)^\| `section_id` \| no \|",
        )
        self.assertNotIn("co-improvement-adapt", contract)
        self.assertNotIn("PERSIST_OK", contract)
        self.assertNotIn("learn-interrupt", contract)

    def test_triggers_on_rubric_and_context_feedback(self) -> None:
        text = read_text(SKILL_MD)
        self.assertRegex(text, r"(?i)rubric")
        self.assertRegex(text, r"(?i)context")
        self.assertIn("Trigger", text)

    def test_description_covers_mid_coreview_and_writing_conventions(self) -> None:
        """Regression: session miss treated genre constraints as draft-only."""
        text = read_text(SKILL_MD)
        # frontmatter description is primary invoke surface
        self.assertRegex(text, r"(?i)writing/genre conventions|writing/genre")
        self.assertRegex(text, r"(?i)mid co-review|while another writing task")
        self.assertRegex(text, r"(?i)Do not wait for section end|REVIEW_OK")
        self.assertRegex(text, r"(?i)Invocation priority|reusable constraints")

    def test_requires_human_decision_before_write(self) -> None:
        skill = read_text(SKILL_MD)
        memory = read_text(MEMORY)
        self.assertRegex(
            skill,
            r"(?i)Never write memory without an explicit human decision",
        )
        self.assertRegex(
            memory,
            r"(?i)Precondition:.*status=decided|Learning Log `status=decided`|decision_mode",
        )

    def test_learning_log_pending_and_decided(self) -> None:
        skill = read_text(SKILL_MD)
        contract = read_text(CONTRACT)
        combined = f"{skill}\n{contract}"
        self.assertIn("pending", combined)
        self.assertIn("decided", combined)
        self.assertIn("learning_log_row", contract)

    def test_skill_procedure_resolves_intents(self) -> None:
        skill = read_text(SKILL_MD)
        self.assertRegex(skill, r"(?i)Intent rule")
        self.assertRegex(skill, r"(?i)generalize to durable|durable goals")
        self.assertRegex(skill, r"(?i)Situation rule|storage-mandatory")
        self.assertIn("version: 4", skill)
        self.assertIn("Write fill paths", skill)
        self.assertNotIn("intent_seed_policy", skill)
        self.assertNotIn("context_hints", skill)
        self.assertNotIn("domain_hint", skill)

    def test_does_not_collect_persist_ok(self) -> None:
        skill = read_text(SKILL_MD)
        self.assertRegex(
            skill,
            r"(?i)do not issue host tokens|do not issue host tokens \(`PERSIST_OK`",
        )

    def test_supports_subagent_or_standalone_caller(self) -> None:
        skill = read_text(SKILL_MD)
        self.assertRegex(skill, r"(?i)subagent|standalone")
        self.assertIn("call-contract.md", skill)

    def test_no_reverse_dependency_on_co_improvement_adapt(self) -> None:
        skill = read_text(SKILL_MD)
        memory = read_text(MEMORY)
        contract = read_text(CONTRACT)
        combined = f"{skill}\n{memory}\n{contract}"
        self.assertNotIn("co-improvement-adapt", combined)
        self.assertNotIn("$co-improvement-adapt", combined)

    def test_scripts_exist(self) -> None:
        self.assertTrue((ROOT / "scripts" / "validate_rubric_memory.py").is_file())
        self.assertTrue((ROOT / "scripts" / "bootstrap_memory_artifacts.sh").is_file())


if __name__ == "__main__":
    unittest.main()
