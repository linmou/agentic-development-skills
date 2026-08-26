#!/usr/bin/env python3
# Tests scripts/create_state_machine_package.py for generating a reusable workflow state-machine contract package.

import importlib.util
import hashlib
import json
import subprocess
import sys
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "create_state_machine_package.py"


def run_generator(tmp_path: Path, spec: dict) -> Path:
    spec_path = tmp_path / "workflow_spec.json"
    output_dir = tmp_path / "generated"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--spec",
            str(spec_path),
            "--output-dir",
            str(output_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "generated" in result.stdout
    return output_dir


def run_rejected_generator(tmp_path: Path, spec: dict) -> tuple[subprocess.CompletedProcess[str], Path]:
    spec_path = tmp_path / "rejected_workflow_spec.json"
    output_dir = tmp_path / "rejected-output"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--spec",
            str(spec_path),
            "--output-dir",
            str(output_dir),
        ],
        capture_output=True,
        text=True,
    )
    return result, output_dir


def load_generated_state_machine(package_dir: Path):
    module_path = package_dir / "scripts" / "state_machine.py"
    spec = importlib.util.spec_from_file_location("generated_state_machine", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def minimal_spec(tmp_path: Path) -> dict:
    source_text = """Phase Drafting: the author writes the draft.
Phase Submitted: the draft waits for monitor review.
Phase Accepted: the review succeeded.
Phase Rejected: the review failed.
The author submits an artifact for review.
Submission requires an artifact reference.
The monitor accepts only with a review record.
If review fails, the monitor rejects with a review record.
The failed review record is required for rejection.
Acceptance ends the workflow successfully.
Rejection ends the workflow unsuccessfully.
Invariant: acceptance or rejection happens only after submission.
"""
    source_path = tmp_path / "workflow.md"
    source_path.write_text(source_text, encoding="utf-8")
    return {
        "workflow_name": "sample-review",
        "purpose": "Formalize a review workflow before implementation.",
        "source_summary": {
            "source_path": source_path.name,
            "source_sha256": hashlib.sha256(source_text.encode("utf-8")).hexdigest(),
            "source_items": [
                {"id": "phase-draft", "kind": "phase", "quote": "Phase Drafting: the author writes the draft."},
                {"id": "phase-submitted", "kind": "phase", "quote": "Phase Submitted: the draft waits for monitor review."},
                {"id": "phase-accepted", "kind": "phase", "quote": "Phase Accepted: the review succeeded."},
                {"id": "phase-rejected", "kind": "phase", "quote": "Phase Rejected: the review failed."},
                {"id": "action-submit", "kind": "action", "quote": "The author submits an artifact for review."},
                {"id": "gate-submit", "kind": "gate", "quote": "Submission requires an artifact reference."},
                {"id": "gate-accept", "kind": "gate", "quote": "The monitor accepts only with a review record."},
                {"id": "failure-reject", "kind": "failure_path", "quote": "If review fails, the monitor rejects with a review record."},
                {"id": "gate-reject", "kind": "gate", "quote": "The failed review record is required for rejection."},
                {"id": "terminal-accepted", "kind": "terminal_condition", "quote": "Acceptance ends the workflow successfully."},
                {"id": "terminal-rejected", "kind": "terminal_condition", "quote": "Rejection ends the workflow unsuccessfully."},
                {"id": "order-invariant", "kind": "invariant", "quote": "Invariant: acceptance or rejection happens only after submission."},
            ],
            "original_states": [
                {
                    "name": "Drafting",
                    "mapped_state": "draft",
                    "source_refs": ["phase-draft"],
                },
                {
                    "name": "Submitted",
                    "mapped_state": "submitted",
                    "source_refs": ["phase-submitted"],
                },
                {
                    "name": "Accepted",
                    "mapped_state": "accepted",
                    "source_refs": ["phase-accepted", "terminal-accepted"],
                },
                {
                    "name": "Rejected",
                    "mapped_state": "rejected",
                    "source_refs": ["phase-rejected", "terminal-rejected"],
                },
            ],
            "invariants": [
                {
                    "name": "review-after-submission",
                    "rule": "Acceptance or rejection occurs only after submission.",
                    "source_refs": ["order-invariant"],
                }
            ],
            "semantic_changes": [],
            "unresolved_ambiguities": [],
            "added_states": [],
        },
        "actors": ["author", "monitor"],
        "states": ["draft", "submitted", "accepted", "rejected"],
        "initial_state": "draft",
        "terminal_states": ["accepted", "rejected"],
        "transitions": [
            {
                "name": "submit",
                "from": "draft",
                "to": "submitted",
                "actor": "author",
                "required_evidence": ["artifact_path"],
                "gate": "An artifact reference is present.",
                "gate_enforcement": "required_evidence_presence",
                "source_refs": ["action-submit", "gate-submit"],
                "semantic_change": "",
            },
            {
                "name": "accept",
                "from": "submitted",
                "to": "accepted",
                "actor": "monitor",
                "required_evidence": ["review_log"],
                "gate": "A review record is present.",
                "gate_enforcement": "required_evidence_presence",
                "source_refs": ["gate-accept", "terminal-accepted"],
                "semantic_change": "",
            },
            {
                "name": "reject",
                "from": "submitted",
                "to": "rejected",
                "actor": "monitor",
                "required_evidence": ["review_log"],
                "gate": "A failed-review record is present.",
                "gate_enforcement": "required_evidence_presence",
                "source_refs": ["failure-reject", "gate-reject", "terminal-rejected"],
                "semantic_change": "",
            },
        ],
    }


def test_generator_creates_contract_docs_and_executable_state_machine(tmp_path):
    package_dir = run_generator(tmp_path, minimal_spec(tmp_path))

    expected_files = [
        "instructions/state_contract.md",
        "instructions/source_workflow_reflection.md",
        "instructions/state_schema.md",
        "instructions/resume_protocol.md",
        "instructions/integration_contract.md",
        "scripts/state_machine.py",
        "scripts/init_state.py",
        "scripts/apply_transition.py",
        "tests/test_state_machine.py",
        "tests/test_state_runtime.py",
    ]
    for relative_path in expected_files:
        assert (package_dir / relative_path).exists()

    assert (package_dir / "state").is_dir()
    assert (package_dir / "logs").is_dir()

    state_machine_text = (package_dir / "scripts" / "state_machine.py").read_text(
        encoding="utf-8"
    )
    assert state_machine_text.startswith("#!/usr/bin/env python3\n")
    assert "# Purpose:" in state_machine_text.splitlines()[1]
    for script_name in ["init_state.py", "apply_transition.py"]:
        script_text = (package_dir / "scripts" / script_name).read_text(encoding="utf-8")
        assert script_text.startswith("#!/usr/bin/env python3\n")
        assert "# Purpose:" in script_text.splitlines()[1]

    assert "dataclass(frozen=True)" in state_machine_text
    assert "from_state: str =" not in state_machine_text
    assert "to_state: str =" not in state_machine_text

    contract_text = (package_dir / "instructions" / "state_contract.md").read_text(
        encoding="utf-8"
    )
    assert "Intent:" in contract_text
    assert (
        "| submit | draft | submitted | author | An artifact reference is present. | "
        "required_evidence_presence | artifact_path | action-submit, gate-submit | none |"
    ) in contract_text
    assert "Source Workflow Reflection" in contract_text
    assert "workflow.md" in contract_text
    assert "define this state's meaning" not in contract_text
    assert "define the durable proof" not in contract_text
    assert "`draft` (initial): Source state `Drafting`" in contract_text
    assert "`artifact_path`: required evidence for `submit`" in contract_text

    integration_text = (
        package_dir / "instructions" / "integration_contract.md"
    ).read_text(encoding="utf-8")
    assert "load or initialize" in integration_text
    assert "must not bypass" in integration_text

    reflection_text = (
        package_dir / "instructions" / "source_workflow_reflection.md"
    ).read_text(encoding="utf-8")
    assert "Verified Source Items" in reflection_text
    assert "Original States" in reflection_text
    assert "| Drafting | draft | phase-draft |" in reflection_text
    assert "Phase Drafting: the author writes the draft." in reflection_text
    assert "review-after-submission" in reflection_text
    assert "Semantic Changes" in reflection_text


def test_generated_state_machine_accepts_legal_transition_and_rejects_bad_ones(tmp_path):
    package_dir = run_generator(tmp_path, minimal_spec(tmp_path))
    state_machine = load_generated_state_machine(package_dir)

    legal = state_machine.TransitionRequest(
        transition="submit",
        actor="author",
        from_state="draft",
        evidence={"artifact_path": "out/result.txt"},
    )
    accepted = state_machine.apply_transition(legal)
    assert accepted.to_state == "submitted"

    wrong_actor = state_machine.TransitionRequest(
        transition="submit",
        actor="monitor",
        from_state="draft",
        evidence={"artifact_path": "out/result.txt"},
    )
    try:
        state_machine.apply_transition(wrong_actor)
    except state_machine.StateMachineError as exc:
        assert "actor" in str(exc)
    else:
        raise AssertionError("wrong actor transition should fail")

    missing_evidence = state_machine.TransitionRequest(
        transition="accept",
        actor="monitor",
        from_state="submitted",
        evidence={},
    )
    try:
        state_machine.apply_transition(missing_evidence)
    except state_machine.StateMachineError as exc:
        assert "evidence" in str(exc)
    else:
        raise AssertionError("missing evidence transition should fail")

    terminal_mutation = state_machine.TransitionRequest(
        transition="accept",
        actor="monitor",
        from_state="accepted",
        evidence={"review_log": "logs/review.json"},
    )
    try:
        state_machine.apply_transition(terminal_mutation)
    except state_machine.StateMachineError as exc:
        assert "terminal" in str(exc)
    else:
        raise AssertionError("terminal state mutation should fail")


def test_generated_runtime_initializes_state_and_persists_transition(tmp_path):
    package_dir = run_generator(tmp_path, minimal_spec(tmp_path))
    state_path = tmp_path / "state" / "canonical_state.json"
    log_path = tmp_path / "logs" / "transitions.jsonl"

    init_result = subprocess.run(
        [
            sys.executable,
            str(package_dir / "scripts" / "init_state.py"),
            "--state-path",
            str(state_path),
            "--instance-id",
            "case-001",
            "--updated-by",
            "agent",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "initialized" in init_result.stdout
    canonical_state = json.loads(state_path.read_text(encoding="utf-8"))
    assert canonical_state["workflow"] == "sample-review"
    assert canonical_state["instance_id"] == "case-001"
    assert canonical_state["state"] == "draft"
    assert canonical_state["last_transition"] is None
    assert canonical_state["evidence"] == {}

    duplicate_init = subprocess.run(
        [
            sys.executable,
            str(package_dir / "scripts" / "init_state.py"),
            "--state-path",
            str(state_path),
            "--instance-id",
            "case-001",
            "--updated-by",
            "agent",
        ],
        capture_output=True,
        text=True,
    )
    assert duplicate_init.returncode != 0
    assert "already exists" in duplicate_init.stderr

    apply_result = subprocess.run(
        [
            sys.executable,
            str(package_dir / "scripts" / "apply_transition.py"),
            "--state-path",
            str(state_path),
            "--log-path",
            str(log_path),
            "--transition",
            "submit",
            "--actor",
            "author",
            "--evidence",
            "artifact_path=out/result.txt",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "accepted" in apply_result.stdout
    canonical_state = json.loads(state_path.read_text(encoding="utf-8"))
    assert canonical_state["state"] == "submitted"
    assert canonical_state["last_transition"] == "submit"
    assert canonical_state["evidence"]["artifact_path"] == "out/result.txt"

    log_lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(log_lines) == 1
    log_record = json.loads(log_lines[0])
    assert log_record["from_state"] == "draft"
    assert log_record["to_state"] == "submitted"

    duplicate_apply = subprocess.run(
        [
            sys.executable,
            str(package_dir / "scripts" / "apply_transition.py"),
            "--state-path",
            str(state_path),
            "--log-path",
            str(log_path),
            "--transition",
            "submit",
            "--actor",
            "author",
            "--evidence",
            "artifact_path=out/result.txt",
        ],
        capture_output=True,
        text=True,
    )
    assert duplicate_apply.returncode != 0
    assert "requires source state draft" in duplicate_apply.stderr


def test_generator_rejects_source_drift_and_unverifiable_quotes(tmp_path):
    spec = minimal_spec(tmp_path)
    spec["source_summary"]["source_path"] = "missing-workflow.md"
    result, output_dir = run_rejected_generator(tmp_path, spec)
    assert result.returncode != 0
    assert "source workflow does not exist" in result.stderr
    assert not output_dir.exists()

    spec = minimal_spec(tmp_path)
    source_path = tmp_path / spec["source_summary"]["source_path"]
    source_path.write_text(source_path.read_text(encoding="utf-8") + "Changed.\n", encoding="utf-8")

    result, output_dir = run_rejected_generator(tmp_path, spec)

    assert result.returncode != 0
    assert "SHA-256 mismatch" in result.stderr
    assert not output_dir.exists()

    spec = minimal_spec(tmp_path)
    spec["source_summary"]["source_items"][0]["quote"] = "A sentence absent from the source."
    result, output_dir = run_rejected_generator(tmp_path, spec)
    assert result.returncode != 0
    assert "quote must occur exactly once" in result.stderr
    assert not output_dir.exists()


def test_generator_rejects_unmapped_source_items_and_unknown_references(tmp_path):
    spec = minimal_spec(tmp_path)
    spec["transitions"][2]["source_refs"].remove("failure-reject")
    result, output_dir = run_rejected_generator(tmp_path, spec)
    assert result.returncode != 0
    assert "unmapped source items: failure-reject" in result.stderr
    assert not output_dir.exists()

    spec = minimal_spec(tmp_path)
    spec["transitions"][0]["source_refs"].append("invented-source")
    result, output_dir = run_rejected_generator(tmp_path, spec)
    assert result.returncode != 0
    assert "unknown source references: invented-source" in result.stderr
    assert not output_dir.exists()


def test_generator_rejects_unsupported_gates_and_unresolved_ambiguity(tmp_path):
    spec = minimal_spec(tmp_path)
    spec["transitions"][1]["gate_enforcement"] = "none"
    result, output_dir = run_rejected_generator(tmp_path, spec)
    assert result.returncode != 0
    assert "persistent runtime cannot enforce" in result.stderr
    assert not output_dir.exists()

    spec = minimal_spec(tmp_path)
    spec["source_summary"]["unresolved_ambiguities"] = [
        "It is unclear whether the author may withdraw after submission."
    ]
    result, output_dir = run_rejected_generator(tmp_path, spec)
    assert result.returncode != 0
    assert "ambiguities to be resolved" in result.stderr
    assert not output_dir.exists()


def test_generator_accepts_an_explicit_semantic_addition(tmp_path):
    spec = minimal_spec(tmp_path)
    change = "Add an escalated terminal outcome approved during formalization."
    spec["source_summary"]["semantic_changes"].append(change)
    spec["source_summary"]["added_states"].append(
        {"name": "escalated", "reason": change}
    )
    spec["states"].append("escalated")
    spec["terminal_states"].append("escalated")
    spec["transitions"].append(
        {
            "name": "escalate",
            "from": "submitted",
            "to": "escalated",
            "actor": "monitor",
            "required_evidence": [],
            "gate": "none",
            "gate_enforcement": "none",
            "source_refs": [],
            "semantic_change": change,
        }
    )

    package_dir = run_generator(tmp_path, spec)

    contract = (package_dir / "instructions" / "state_contract.md").read_text(
        encoding="utf-8"
    )
    assert "Added by approved semantic change" in contract
    assert change in contract


def test_generator_refuses_to_replace_a_non_empty_output_directory(tmp_path):
    output_dir = tmp_path / "generated"
    output_dir.mkdir()
    sentinel = output_dir / "keep-me.txt"
    sentinel.write_text("do not delete\n", encoding="utf-8")
    spec_path = tmp_path / "workflow_spec.json"
    spec_path.write_text(json.dumps(minimal_spec(tmp_path)), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--spec",
            str(spec_path),
            "--output-dir",
            str(output_dir),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "non-empty" in result.stderr
    assert sentinel.read_text(encoding="utf-8") == "do not delete\n"


def test_generator_rejects_a_workflow_with_an_unreachable_terminal_state(tmp_path):
    spec = minimal_spec(tmp_path)
    spec["transitions"][0]["to"] = "accepted"
    spec_path = tmp_path / "workflow_spec.json"
    output_dir = tmp_path / "generated"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--spec",
            str(spec_path),
            "--output-dir",
            str(output_dir),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "unreachable" in result.stderr
    assert not output_dir.exists()


def test_generated_tests_cover_every_transition_and_terminal_path(tmp_path):
    package_dir = run_generator(tmp_path, minimal_spec(tmp_path))

    state_machine_test_path = package_dir / "tests" / "test_state_machine.py"
    state_machine_spec = importlib.util.spec_from_file_location(
        "generated_state_machine_tests", state_machine_test_path
    )
    assert state_machine_spec is not None
    assert state_machine_spec.loader is not None
    state_machine_tests = importlib.util.module_from_spec(state_machine_spec)
    sys.modules[state_machine_spec.name] = state_machine_tests
    state_machine_spec.loader.exec_module(state_machine_tests)
    assert len(state_machine_tests.TRANSITION_CASES) == 3
    state_machine_tests.test_every_legal_transition_succeeds()
    state_machine_tests.test_every_transition_rejects_wrong_actor_and_source()
    state_machine_tests.test_every_evidence_gate_rejects_missing_evidence()
    state_machine_tests.test_unknown_transition_and_state_are_rejected()
    state_machine_tests.test_every_terminal_state_rejects_mutation()

    runtime_test_path = package_dir / "tests" / "test_state_runtime.py"
    runtime_spec = importlib.util.spec_from_file_location(
        "generated_runtime_tests", runtime_test_path
    )
    assert runtime_spec is not None
    assert runtime_spec.loader is not None
    runtime_tests = importlib.util.module_from_spec(runtime_spec)
    sys.modules[runtime_spec.name] = runtime_tests
    runtime_spec.loader.exec_module(runtime_tests)

    assert {case["terminal"] for case in runtime_tests.TERMINAL_PATHS} == {
        "accepted",
        "rejected",
    }
    runtime_tests.test_runtime_executes_a_path_to_every_terminal_and_preserves_terminal_state(
        tmp_path
    )


def test_generator_rejects_an_added_state_without_explicit_provenance(tmp_path):
    spec = minimal_spec(tmp_path)
    spec["states"].append("escalated")
    spec_path = tmp_path / "workflow_spec.json"
    output_dir = tmp_path / "generated"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--spec",
            str(spec_path),
            "--output-dir",
            str(output_dir),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "unexplained generated states" in result.stderr


def test_generated_docs_describe_the_single_process_enforcement_boundary(tmp_path):
    package_dir = run_generator(tmp_path, minimal_spec(tmp_path))

    contract = (package_dir / "instructions" / "state_contract.md").read_text(
        encoding="utf-8"
    )
    resume = (package_dir / "instructions" / "resume_protocol.md").read_text(
        encoding="utf-8"
    )
    integration = (package_dir / "instructions" / "integration_contract.md").read_text(
        encoding="utf-8"
    )
    schema = (package_dir / "instructions" / "state_schema.md").read_text(
        encoding="utf-8"
    )

    assert "single-process" in contract
    assert "define the single actor or process" not in contract
    assert "at most once" not in resume
    assert "single-process" in integration
    assert "Canonical state owner" not in schema
    assert "durable log entry" not in schema
