# Responsible files: references, evals, and agents/openai.yaml
# Purpose: ensure non-SKILL configuration artifacts retain their expected workflow guidance.

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPENAI_YAML = (ROOT / "agents" / "openai.yaml").read_text()
PHASE_AUDITS = (ROOT / "references" / "phase_audits.md").read_text()
EVAL_RUBRIC = (ROOT / "references" / "eval_rubric.md").read_text()
EVALS = json.loads((ROOT / "evals" / "evals.json").read_text())


def test_ui_metadata_does_not_advertise_parallel_agents() -> None:
    assert "parallel agents" not in OPENAI_YAML
    assert "monitor agent" in OPENAI_YAML


def test_evals_do_not_reward_parallel_orchestration() -> None:
    serialized = json.dumps(EVALS)
    assert "parallel agents" not in serialized
    assert "minimum sidecars" not in serialized
    assert "duplicate implementers" not in serialized


def test_green_uses_gate_and_refactor_uses_cumulative_audit() -> None:
    serialized_evals = json.dumps(EVALS)

    assert "Cumulative Refactor Claim" in PHASE_AUDITS
    assert "Do not run `$review-with-multi-debate` for Green by default" in PHASE_AUDITS
    assert "Green uses a deterministic gate instead of a debate by default" in EVAL_RUBRIC
    assert "Green uses a deterministic gate" in serialized_evals
    assert "audits each phase" not in serialized_evals


def test_test_refactor_is_a_scoped_audited_stage() -> None:
    skill = (ROOT / "SKILL.md").read_text()

    assert "### 6. Test Refactor" in skill
    assert "references/test_refactor.md" in skill
    assert "only test-like paths" in skill
    assert "targeted and full suites" in skill
    assert "mandatory Test Refactor debate" in skill
    assert "Test Refactor Claim" in PHASE_AUDITS
