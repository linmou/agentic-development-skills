# Responsible files: SKILL.md, references, evals, and agents/openai.yaml
# Purpose: ensure skill configuration retains its workflow and orchestration contracts.

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPENAI_YAML = (ROOT / "agents" / "openai.yaml").read_text()
PHASE_AUDITS = (ROOT / "references" / "phase_audits.md").read_text()
PHASE_CONTRACTS = (ROOT / "references" / "phase_contracts.md").read_text()
SKILL = (ROOT / "SKILL.md").read_text()
WORKFLOW = (ROOT / "references" / "workflow.md").read_text()
EVAL_RUBRIC = (ROOT / "references" / "eval_rubric.md").read_text()
EVALS = json.loads((ROOT / "evals" / "evals.json").read_text())


def test_prerequisite_diagnosis_hands_off_to_strict_tdd_activation() -> None:
    activation = SKILL[SKILL.index("## Activation Boundary") :]
    composed_eval = next(case for case in EVALS["evals"] if case["id"] == 9)
    serialized_eval = json.dumps(composed_eval)

    assert "diagnose, explore, run tests, and collect evidence" in activation
    assert "account for every diagnostic-created worktree change" in activation
    assert "production files free of temporary instrumentation" in activation
    assert "outside normal test collection" in activation
    assert "does not replace the formal Red test" in activation
    assert "TDD activates when `audits/<feature>_request_map.md` is saved" in activation
    assert "before any permanent regression-test or production edit" in activation
    assert "rerun it after Green against the original symptom" in activation
    assert "finish cleanup of its retained diagnostic artifacts" in activation
    assert "monitor pass and verified `pre_red` snapshot" in activation

    assert "$diagnosing-bugs" in composed_eval["prompt"]
    assert "$fast-multi-agent-tdd" in composed_eval["prompt"]
    assert "does not become a loophole" in serialized_eval
    assert "permanent regression test is written only after" in serialized_eval
    assert "permanent test or production correction requires a new TDD activation" in serialized_eval

    stale_global_prohibitions = (
        "Test execution begins only after step 6",
        "do not edit tests or production, run tests",
        "parallel workers for implementation, exploration, or test drafting",
        "must not be reconstructed after tests exist",
    )
    combined = "\n".join((SKILL, WORKFLOW, EVAL_RUBRIC))
    assert all(rule not in combined for rule in stale_global_prohibitions)


def test_ui_metadata_does_not_advertise_parallel_agents() -> None:
    assert "parallel agents" not in OPENAI_YAML
    assert "monitor agent" in OPENAI_YAML


def test_evals_do_not_reward_parallel_orchestration() -> None:
    serialized = json.dumps(EVALS)
    assert "parallel agents" not in serialized
    assert "minimum sidecars" not in serialized
    assert "duplicate implementers" not in serialized


def test_delegation_contract_is_backend_neutral() -> None:
    controlled_documents = (SKILL, WORKFLOW, PHASE_CONTRACTS, EVAL_RUBRIC)
    for document in controlled_documents:
        assert "top-level `spawn_agent`" not in document
        assert "collaboration.spawn_agent" not in document
        assert "/root/" not in document
        assert "refs/codex/tdd" not in document

    combined = "\n".join(controlled_documents).lower()
    assert "delegation mechanism" in combined
    assert "stable" in combined
    assert "distinct" in combined
    assert "another" in combined and "mechanism" in combined

    selector_eval = next(case for case in EVALS["evals"] if case["id"] == 8)
    assert selector_eval["contract"]["delegation_contract"] == {
        "backend_specific_operation_required": False,
        "identity_requirement": "stable_nonempty",
        "source_requirement": "actual_nonempty_mechanism",
        "fallback_before_stop": True,
    }


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


def test_compact_selector_eval_requires_combined_compatible_control_behavior() -> None:
    selector_eval = next(case for case in EVALS["evals"] if case["id"] == 8)
    contract = selector_eval["contract"]
    controls = {
        item["control"]: item for item in contract["compatible_control_evidence"]
    }

    limit_evidence = controls["limit_per_benchmark"]
    assert contract["route"] == "compact"
    assert limit_evidence["fixture"] == "binding_non_neutral"
    assert set(limit_evidence["combined_assertions"]) == {
        "strict_filter_membership",
        "per_benchmark_cardinality",
    }
    assert "all_data" in contract["mutually_exclusive_strategies"]
    assert not set(controls) & set(contract["mutually_exclusive_strategies"])
    assert contract["red_reviewer_count"] == 3


def test_initial_pre_red_gate_validates_before_snapshot_publication() -> None:
    for document in (SKILL, WORKFLOW, PHASE_CONTRACTS):
        validation = document.index("<!-- initial-pre-red-monitor-validation -->")
        publication = document.index("<!-- initial-pre-red-snapshot-publication -->")

        assert validation < publication
        assert "phase_guard.py" in document[validation:publication]
        assert "resolv" in document[validation:publication]
        assert "tdd_snapshot.py create" not in document[validation:publication]

    skill_publication = SKILL.index("<!-- initial-pre-red-snapshot-publication -->")
    assert SKILL.index("tdd_snapshot.py create", skill_publication) > skill_publication


def test_numbered_pre_red_rounds_remain_post_review_and_authenticated() -> None:
    for document in (SKILL, WORKFLOW, PHASE_CONTRACTS):
        round_contract = document[document.index("<!-- post-red-numbered-rounds-only -->") :]

        assert "review" in round_contract.lower()
        assert "pre_red_round_<N>" in round_contract
        assert "reviewer" in round_contract.lower()

    assert "Red always ends with a mandatory `$review-with-multi-debate` audit" in WORKFLOW
    selector_eval = next(case for case in EVALS["evals"] if case["id"] == 8)
    assert selector_eval["contract"]["red_reviewer_count"] == 3


def test_red_debate_requires_reviewer_owned_files_and_strict_transition() -> None:
    selector_eval = next(case for case in EVALS["evals"] if case["id"] == 8)
    contract = selector_eval["contract"]["red_debate_artifacts"]

    assert contract == {
        "reviewer_writes_own_file": True,
        "reviewer_files_per_iteration": 3,
        "parent_transcription_valid": False,
        "snapshot_revalidates_provenance_hashes": True,
        "summary_source": "deterministic_aggregator",
        "required_transition_gates": ["provenance", "record_round", "advance_phase"],
        "later_round_scope": "disputed_criteria_only",
    }

    for document in (SKILL, WORKFLOW, PHASE_CONTRACTS):
        owned_contract = document[document.index("<!-- reviewer-owned-debate-artifacts -->") :]
        assert "exactly one" in owned_contract
        assert "chat-only" in owned_contract
        assert "provenance" in owned_contract
        assert "record_round" in owned_contract
        assert "counterevidence" in owned_contract
        assert "advance_phase" in owned_contract
        assert owned_contract.index("provenance") < owned_contract.index("record_round")
        assert owned_contract.index("record_round") < owned_contract.index("advance_phase")

    workflow_contract = WORKFLOW[WORKFLOW.index("<!-- reviewer-owned-debate-artifacts -->") :]
    assert "audit1_iterationM.json" in workflow_contract
    assert "audit2_iterationM.json" in workflow_contract
    assert "audit3_iterationM.json" in workflow_contract
    assert "red_review_gate.py provenance" in workflow_contract
    assert "--provenance" in workflow_contract
    assert "--review-iteration" in workflow_contract
    assert "re-hash" in workflow_contract
    assert "aggregate_audits.py" in workflow_contract
    assert "only the disputed criteria" in workflow_contract


def test_reviewer_scheduling_preserves_independence_with_one_free_slot() -> None:
    selector_eval = next(case for case in EVALS["evals"] if case["id"] == 8)
    contract = selector_eval["contract"]
    scheduling = contract["reviewer_scheduling"]

    assert scheduling == {
        "independence_requires_simultaneity": False,
        "serial_order_when_one_slot_free": ["audit1", "audit2", "audit3"],
        "distinct_child_identities": True,
        "distinct_roles_and_isolated_prompts": True,
        "capacity_error_preserves_valid_files": True,
        "capacity_retry_scope": "missing_distinct_reviewer_same_iteration",
        "restart_completed_reviewers": False,
    }
    assert len(scheduling["serial_order_when_one_slot_free"]) == contract[
        "red_reviewer_count"
    ]
    assert len(set(scheduling["serial_order_when_one_slot_free"])) == contract[
        "red_debate_artifacts"
    ]["reviewer_files_per_iteration"]

    for document in (SKILL, WORKFLOW, PHASE_CONTRACTS):
        scheduling_contract = document[
            document.index("<!-- capacity-aware-reviewer-scheduling -->") :
        ]
        assert "distinct" in scheduling_contract
        assert "does not require simultaneous" in scheduling_contract
        assert "audit1" in scheduling_contract
        assert "audit2" in scheduling_contract
        assert "audit3" in scheduling_contract
        assert "capacity" in scheduling_contract
        assert "missing" in scheduling_contract
        assert "transcri" in scheduling_contract


def test_focused_review_snapshot_binds_both_review_branches() -> None:
    selector_eval = next(case for case in EVALS["evals"] if case["id"] == 8)
    assert selector_eval["contract"]["focused_review_snapshot"] == {
        "review_iteration": 2,
        "initial_provenance_required": True,
        "focused_provenance_required": True,
        "staged_hash_revalidation": True,
    }

    for document in (SKILL, WORKFLOW, PHASE_CONTRACTS):
        focused = document[document.index("<!-- risk-scaled-focused-red-review -->") :]
        assert "--provenance" in focused
        assert "--focused-provenance" in focused
        assert "--review-iteration 2" in focused


def test_post_review_test_correction_has_an_authenticated_pre_edit_order() -> None:
    selector_eval = next(case for case in EVALS["evals"] if case["id"] == 8)
    contract = selector_eval["contract"]["post_review_correction_order"]

    assert contract == {
        "monitor_inputs": [
            "precise_correction_plan",
            "updated_map_and_scope",
            "retained_prior_reviewer_provenance",
            "current_pre_edit_test_hashes_and_status",
        ],
        "monitor_requires_corrected_test_content": False,
        "snapshot": "publish_and_verify_append_only_numbered_pre_red",
        "edit_scope": "planned_tests_only_after_snapshot",
        "post_edit_gates": [
            "genuine_red",
            "red_scope_guard",
            "three_reviewer_targeted_iteration",
        ],
        "corrected_content_verifier": "next_red_reviewer_iteration",
    }

    for document in (SKILL, WORKFLOW, PHASE_CONTRACTS):
        ordering = document[document.index("<!-- post-review-correction-order -->") :]
        plan = ordering.index("precise correction plan")
        baseline = ordering.index("current pre-edit Git hash")
        prohibition = ordering.index("must not require the corrected test content")
        snapshot = ordering.index("append-only numbered snapshot")
        edit = ordering.index("edit only the planned tests")
        red = ordering.index("genuine Red")
        review = ordering.index("three-reviewer iteration")

        assert plan < snapshot
        assert baseline < snapshot
        assert prohibition < snapshot
        assert snapshot < edit < red < review


def test_bounded_recovery_contract_is_consistent_and_does_not_weaken_red_debate() -> None:
    for document in (SKILL, WORKFLOW, PHASE_CONTRACTS):
        contract = document[document.index("<!-- bounded-phase-state-recovery -->") :]
        assert "authenticated" in contract
        assert "accidental_phase_write" in contract
        assert "audits/**" in contract
        assert "semantic" in contract
        assert "review" in contract

    assert "initial Red debate follows the loaded review skill's three-reviewer contract" in SKILL
    assert "The initial Red iteration always uses the three-reviewer workflow" in WORKFLOW
