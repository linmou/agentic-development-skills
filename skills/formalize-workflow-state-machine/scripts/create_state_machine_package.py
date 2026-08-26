#!/usr/bin/env python3
# Purpose: Generate a small documented and executable state-machine package from a workflow spec.

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from string import Template
from typing import Any


class SpecError(ValueError):
    pass


@dataclass(frozen=True)
class TransitionSpec:
    name: str
    from_state: str
    to_state: str
    actor: str
    required_evidence: tuple[str, ...]
    gate: str
    gate_enforcement: str
    source_refs: tuple[str, ...]
    semantic_change: str


@dataclass(frozen=True)
class SourceItemSpec:
    item_id: str
    kind: str
    quote: str


@dataclass(frozen=True)
class OriginalStateSpec:
    name: str
    mapped_state: str
    source_refs: tuple[str, ...]


@dataclass(frozen=True)
class InvariantSpec:
    name: str
    rule: str
    source_refs: tuple[str, ...]


@dataclass(frozen=True)
class AddedStateSpec:
    name: str
    reason: str


@dataclass(frozen=True)
class SourceSummarySpec:
    source_path: str
    source_sha256: str
    source_items: tuple[SourceItemSpec, ...]
    original_states: tuple[OriginalStateSpec, ...]
    invariants: tuple[InvariantSpec, ...]
    semantic_changes: tuple[str, ...]
    unresolved_ambiguities: tuple[str, ...]
    added_states: tuple[AddedStateSpec, ...]


@dataclass(frozen=True)
class WorkflowSpec:
    workflow_name: str
    purpose: str
    source_summary: SourceSummarySpec
    actors: tuple[str, ...]
    states: tuple[str, ...]
    initial_state: str
    terminal_states: tuple[str, ...]
    transitions: tuple[TransitionSpec, ...]


SOURCE_ITEM_KINDS = {
    "phase",
    "action",
    "gate",
    "failure_path",
    "terminal_condition",
    "invariant",
}
GATE_ENFORCEMENTS = {"none", "required_evidence_presence"}


STATE_MACHINE_TEMPLATE = Template(
    '''#!/usr/bin/env python3
# Purpose: Enforce legal state transitions for the ${workflow_name} workflow.

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


class StateMachineError(ValueError):
    pass


@dataclass(frozen=True)
class TransitionRule:
    name: str
    from_state: str
    to_state: str
    actor: str
    required_evidence: tuple[str, ...]


@dataclass(frozen=True)
class TransitionRequest:
    transition: str
    actor: str
    from_state: str
    evidence: Mapping[str, str]


@dataclass(frozen=True)
class TransitionResult:
    transition: str
    actor: str
    from_state: str
    to_state: str
    evidence: Mapping[str, str]


LEGAL_STATES = ${states_repr}
INITIAL_STATE = ${initial_state_repr}
TERMINAL_STATES = ${terminal_states_repr}
TRANSITIONS = {
${transition_rules}
}


def apply_transition(request: TransitionRequest) -> TransitionResult:
    if request.from_state not in LEGAL_STATES:
        raise StateMachineError(f"unknown source state: {request.from_state}")
    if request.from_state in TERMINAL_STATES:
        raise StateMachineError(f"cannot mutate terminal state: {request.from_state}")

    rule = TRANSITIONS.get(request.transition)
    if rule is None:
        raise StateMachineError(f"unknown transition: {request.transition}")
    if request.from_state != rule.from_state:
        raise StateMachineError(
            f"transition {request.transition} requires source state {rule.from_state}, "
            f"got {request.from_state}"
        )
    if request.actor != rule.actor:
        raise StateMachineError(
            f"transition {request.transition} requires actor {rule.actor}, got {request.actor}"
        )

    missing = [key for key in rule.required_evidence if not request.evidence.get(key)]
    if missing:
        joined = ", ".join(missing)
        raise StateMachineError(f"missing required evidence: {joined}")

    return TransitionResult(
        transition=request.transition,
        actor=request.actor,
        from_state=request.from_state,
        to_state=rule.to_state,
        evidence=request.evidence,
    )


def transition_identity(result: TransitionResult) -> tuple[str, str, str, str, tuple[tuple[str, str], ...]]:
    return (
        result.transition,
        result.actor,
        result.from_state,
        result.to_state,
        tuple(sorted(result.evidence.items())),
    )
'''
)


INIT_STATE_TEMPLATE = Template(
    '''#!/usr/bin/env python3
# Purpose: Initialize a canonical state record for the ${workflow_name} workflow.

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from state_machine import INITIAL_STATE


WORKFLOW_NAME = ${workflow_name_repr}


def main() -> int:
    args = parse_args()
    if args.state_path.exists():
        print(f"state already exists: {args.state_path}", file=sys.stderr)
        return 2

    record = {
        "workflow": WORKFLOW_NAME,
        "instance_id": args.instance_id,
        "state": INITIAL_STATE,
        "updated_by": args.updated_by,
        "updated_at": utc_now(),
        "last_transition": None,
        "evidence": {},
    }
    write_json_atomic(args.state_path, record)
    print(f"initialized {WORKFLOW_NAME} state: {args.state_path}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Initialize canonical workflow state.")
    parser.add_argument("--state-path", type=Path, required=True)
    parser.add_argument("--instance-id", required=True)
    parser.add_argument("--updated-by", required=True)
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json_atomic(path: Path, record: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.tmp")
    tmp_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\\n", encoding="utf-8")
    tmp_path.replace(path)


if __name__ == "__main__":
    raise SystemExit(main())
'''
)


APPLY_TRANSITION_TEMPLATE = Template(
    '''#!/usr/bin/env python3
# Purpose: Validate and persist an accepted transition for the ${workflow_name} workflow.

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from state_machine import (
    StateMachineError,
    TransitionRequest,
    apply_transition,
    transition_identity,
)


WORKFLOW_NAME = ${workflow_name_repr}


def main() -> int:
    args = parse_args()
    try:
        canonical_state = load_state(args.state_path)
        evidence = parse_evidence(args.evidence)
        request = TransitionRequest(
            transition=args.transition,
            actor=args.actor,
            from_state=str(canonical_state["state"]),
            evidence=evidence,
        )
        result = apply_transition(request)
    except (OSError, KeyError, json.JSONDecodeError, StateMachineError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    accepted_at = utc_now()
    log_record = {
        "workflow": WORKFLOW_NAME,
        "instance_id": canonical_state["instance_id"],
        "transition": result.transition,
        "actor": result.actor,
        "from_state": result.from_state,
        "to_state": result.to_state,
        "accepted_at": accepted_at,
        "evidence": dict(result.evidence),
        "identity": repr(transition_identity(result)),
    }
    next_state = {
        **canonical_state,
        "state": result.to_state,
        "updated_by": result.actor,
        "updated_at": accepted_at,
        "last_transition": result.transition,
        "evidence": dict(result.evidence),
    }

    append_jsonl(args.log_path, log_record)
    write_json_atomic(args.state_path, next_state)
    print(f"accepted {result.transition}: {result.from_state} -> {result.to_state}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply one validated workflow transition.")
    parser.add_argument("--state-path", type=Path, required=True)
    parser.add_argument("--log-path", type=Path, required=True)
    parser.add_argument("--transition", required=True)
    parser.add_argument("--actor", required=True)
    parser.add_argument("--evidence", action="append", default=[])
    return parser.parse_args()


def load_state(path: Path) -> dict[str, object]:
    if not path.exists():
        raise ValueError(f"state does not exist: {path}")
    record = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(record, dict):
        raise ValueError("canonical state must be a JSON object")
    if record.get("workflow") != WORKFLOW_NAME:
        raise ValueError(f"state workflow mismatch: {record.get('workflow')}")
    if "instance_id" not in record:
        raise ValueError("canonical state missing instance_id")
    if "state" not in record:
        raise ValueError("canonical state missing state")
    return record


def parse_evidence(raw_items: list[str]) -> dict[str, str]:
    evidence: dict[str, str] = {}
    for item in raw_items:
        if "=" not in item:
            raise ValueError(f"evidence must use key=value format: {item}")
        key, value = item.split("=", 1)
        if not key.strip() or not value.strip():
            raise ValueError(f"evidence key and value must be non-empty: {item}")
        evidence[key] = value
    return evidence


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_jsonl(path: Path, record: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\\n")


def write_json_atomic(path: Path, record: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.tmp")
    tmp_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\\n", encoding="utf-8")
    tmp_path.replace(path)


if __name__ == "__main__":
    raise SystemExit(main())
'''
)


TEST_TEMPLATE = Template(
    '''#!/usr/bin/env python3
# Tests scripts/state_machine.py for legal and illegal workflow state transitions.

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.state_machine import (
    LEGAL_STATES,
    StateMachineError,
    TERMINAL_STATES,
    TransitionRequest,
    apply_transition,
)


TRANSITION_CASES = ${transition_cases_repr}


def assert_rejected(request, expected_message):
    try:
        apply_transition(request)
    except StateMachineError as exc:
        assert expected_message in str(exc)
    else:
        raise AssertionError(f"transition should fail: {request}")


def test_every_legal_transition_succeeds():
    for case in TRANSITION_CASES:
        result = apply_transition(
            TransitionRequest(
                transition=case["name"],
                actor=case["actor"],
                from_state=case["from"],
                evidence=case["evidence"],
            )
        )
        assert result.to_state == case["to"]


def test_every_transition_rejects_wrong_actor_and_source():
    for case in TRANSITION_CASES:
        assert_rejected(
            TransitionRequest(
                transition=case["name"],
                actor=case["wrong_actor"],
                from_state=case["from"],
                evidence=case["evidence"],
            ),
            "actor",
        )
        assert_rejected(
            TransitionRequest(
                transition=case["name"],
                actor=case["actor"],
                from_state=case["wrong_source"],
                evidence=case["evidence"],
            ),
            case["wrong_source_message"],
        )


def test_every_evidence_gate_rejects_missing_evidence():
    for case in TRANSITION_CASES:
        if case["evidence"]:
            assert_rejected(
                TransitionRequest(
                    transition=case["name"],
                    actor=case["actor"],
                    from_state=case["from"],
                    evidence={},
                ),
                "evidence",
            )


def test_unknown_transition_and_state_are_rejected():
    first = TRANSITION_CASES[0]
    assert_rejected(
        TransitionRequest("unknown", first["actor"], first["from"], first["evidence"]),
        "unknown transition",
    )
    assert_rejected(
        TransitionRequest(first["name"], first["actor"], "__unknown_state__", first["evidence"]),
        "unknown source state",
    )


def test_every_terminal_state_rejects_mutation():
    first = TRANSITION_CASES[0]
    for terminal_state in TERMINAL_STATES:
        assert terminal_state in LEGAL_STATES
        assert_rejected(
            TransitionRequest(first["name"], first["actor"], terminal_state, first["evidence"]),
            "terminal",
        )
'''
)


RUNTIME_TEST_TEMPLATE = Template(
    '''#!/usr/bin/env python3
# Tests runtime initialization and persisted transition application for the generated state machine.

import json
import subprocess
import sys
from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parents[1]
TERMINAL_PATHS = ${terminal_paths_repr}
INITIAL_STATE = ${initial_state_repr}


def test_runtime_executes_a_path_to_every_terminal_and_preserves_terminal_state(tmp_path):
    for index, case in enumerate(TERMINAL_PATHS):
        case_dir = tmp_path / f"case-{index}"
        state_path = case_dir / "state.json"
        log_path = case_dir / "transitions.jsonl"
        first_actor = case["steps"][0]["actor"]
        subprocess.run(
            [
                sys.executable,
                str(PACKAGE_DIR / "scripts" / "init_state.py"),
                "--state-path",
                str(state_path),
                "--instance-id",
                f"case-{index}",
                "--updated-by",
                first_actor,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        assert json.loads(state_path.read_text(encoding="utf-8"))["state"] == INITIAL_STATE

        for step in case["steps"]:
            command = [
                sys.executable,
                str(PACKAGE_DIR / "scripts" / "apply_transition.py"),
                "--state-path",
                str(state_path),
                "--log-path",
                str(log_path),
                "--transition",
                step["name"],
                "--actor",
                step["actor"],
            ]
            for key, value in step["evidence"].items():
                command.extend(["--evidence", f"{key}={value}"])
            subprocess.run(command, check=True, capture_output=True, text=True)

        terminal_record = state_path.read_text(encoding="utf-8")
        assert json.loads(terminal_record)["state"] == case["terminal"]
        assert len(log_path.read_text(encoding="utf-8").strip().splitlines()) == len(case["steps"])

        reset_result = subprocess.run(
            [
                sys.executable,
                str(PACKAGE_DIR / "scripts" / "init_state.py"),
                "--state-path",
                str(state_path),
                "--instance-id",
                f"case-{index}",
                "--updated-by",
                first_actor,
                "--force",
            ],
            capture_output=True,
            text=True,
        )
        assert reset_result.returncode != 0
        assert state_path.read_text(encoding="utf-8") == terminal_record
'''
)


def main() -> int:
    args = parse_args()
    raw_spec = json.loads(args.spec.read_text(encoding="utf-8"))
    workflow = parse_workflow_spec(raw_spec)
    validate_source_provenance(workflow.source_summary, args.spec.parent)
    write_package(workflow, args.output_dir)
    print(f"generated state-machine package: {args.output_dir}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a documented workflow state-machine package."
    )
    parser.add_argument("--spec", type=Path, required=True, help="Path to workflow JSON spec.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory to create or replace with the generated package.",
    )
    return parser.parse_args()


def parse_workflow_spec(raw_spec: dict[str, Any]) -> WorkflowSpec:
    required_fields = [
        "workflow_name",
        "purpose",
        "source_summary",
        "actors",
        "states",
        "initial_state",
        "terminal_states",
        "transitions",
    ]
    for field in required_fields:
        if field not in raw_spec:
            raise SpecError(f"missing required field: {field}")

    workflow_name = require_string(raw_spec["workflow_name"], "workflow_name")
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]*", workflow_name):
        raise SpecError("workflow_name must be filesystem-safe")

    purpose = require_string(raw_spec["purpose"], "purpose")
    source_summary = parse_source_summary(raw_spec["source_summary"])
    actors = require_string_tuple(raw_spec["actors"], "actors")
    states = require_string_tuple(raw_spec["states"], "states")
    initial_state = require_string(raw_spec["initial_state"], "initial_state")
    terminal_states = require_string_tuple(raw_spec["terminal_states"], "terminal_states")

    if initial_state not in states:
        raise SpecError("initial_state must be listed in states")
    for state in terminal_states:
        if state not in states:
            raise SpecError(f"terminal state is not listed in states: {state}")
    for original_state in source_summary.original_states:
        if original_state.mapped_state not in states:
            raise SpecError(
                "source_summary original state "
                f"{original_state.name} maps to unknown state: {original_state.mapped_state}"
            )
    mapped_states = {
        original_state.mapped_state
        for original_state in source_summary.original_states
    }
    added_states = {state.name for state in source_summary.added_states}
    unknown_added_states = sorted(added_states - set(states))
    if unknown_added_states:
        raise SpecError(
            "added states are not listed in states: "
            f"{', '.join(unknown_added_states)}"
        )
    unexplained_states = sorted(set(states) - mapped_states - added_states)
    if unexplained_states:
        raise SpecError(
            "unexplained generated states: "
            f"{', '.join(unexplained_states)}"
        )

    transitions = parse_transitions(raw_spec["transitions"], actors, states)
    if not transitions:
        raise SpecError("at least one transition is required")
    validate_semantic_provenance(
        source_summary,
        states,
        terminal_states,
        transitions,
    )
    validate_workflow_graph(states, initial_state, terminal_states, transitions)

    return WorkflowSpec(
        workflow_name=workflow_name,
        purpose=purpose,
        source_summary=source_summary,
        actors=actors,
        states=states,
        initial_state=initial_state,
        terminal_states=terminal_states,
        transitions=transitions,
    )


def validate_workflow_graph(
    states: tuple[str, ...],
    initial_state: str,
    terminal_states: tuple[str, ...],
    transitions: tuple[TransitionSpec, ...],
) -> None:
    terminal_state_set = set(terminal_states)
    transitions_by_source: dict[str, list[TransitionSpec]] = {
        state: [] for state in states
    }
    for transition in transitions:
        if transition.from_state in terminal_state_set:
            raise SpecError(
                f"transition {transition.name} leaves terminal state: "
                f"{transition.from_state}"
            )
        transitions_by_source[transition.from_state].append(transition)

    reachable = {initial_state}
    pending = [initial_state]
    while pending:
        state = pending.pop()
        for transition in transitions_by_source[state]:
            if transition.to_state not in reachable:
                reachable.add(transition.to_state)
                pending.append(transition.to_state)

    unreachable = sorted(set(states) - reachable)
    if unreachable:
        raise SpecError(f"unreachable states: {', '.join(unreachable)}")

    dead_ends = sorted(
        state
        for state in states
        if state not in terminal_state_set and not transitions_by_source[state]
    )
    if dead_ends:
        raise SpecError(f"non-terminal states with no exit: {', '.join(dead_ends)}")


def parse_source_summary(raw_source_summary: Any) -> SourceSummarySpec:
    if not isinstance(raw_source_summary, dict):
        raise SpecError("source_summary must be an object")

    source_path = require_string(raw_source_summary.get("source_path"), "source_summary.source_path")
    source_sha256 = require_string(
        raw_source_summary.get("source_sha256"),
        "source_summary.source_sha256",
    ).lower()
    if not re.fullmatch(r"[0-9a-f]{64}", source_sha256):
        raise SpecError("source_summary.source_sha256 must be a SHA-256 hex digest")

    raw_source_items = raw_source_summary.get("source_items")
    if not isinstance(raw_source_items, list) or not raw_source_items:
        raise SpecError("source_summary.source_items must be a non-empty list")
    source_items: list[SourceItemSpec] = []
    source_item_ids: set[str] = set()
    for index, raw_item in enumerate(raw_source_items):
        if not isinstance(raw_item, dict):
            raise SpecError(f"source_summary.source_items[{index}] must be an object")
        item_id = require_string(
            raw_item.get("id"),
            f"source_summary.source_items[{index}].id",
        )
        kind = require_string(
            raw_item.get("kind"),
            f"source_summary.source_items[{index}].kind",
        )
        if item_id in source_item_ids:
            raise SpecError(f"duplicate source item id: {item_id}")
        if kind not in SOURCE_ITEM_KINDS:
            raise SpecError(f"unsupported source item kind: {kind}")
        source_item_ids.add(item_id)
        source_items.append(
            SourceItemSpec(
                item_id=item_id,
                kind=kind,
                quote=require_string(
                    raw_item.get("quote"),
                    f"source_summary.source_items[{index}].quote",
                ),
            )
        )

    raw_original_states = raw_source_summary.get("original_states")
    if not isinstance(raw_original_states, list) or not raw_original_states:
        raise SpecError("source_summary.original_states must be a non-empty list")

    original_states: list[OriginalStateSpec] = []
    for index, raw_state in enumerate(raw_original_states):
        if not isinstance(raw_state, dict):
            raise SpecError(f"source_summary.original_states[{index}] must be an object")
        original_states.append(
            OriginalStateSpec(
                name=require_string(
                    raw_state.get("name"),
                    f"source_summary.original_states[{index}].name",
                ),
                mapped_state=require_string(
                    raw_state.get("mapped_state"),
                    f"source_summary.original_states[{index}].mapped_state",
                ),
                source_refs=require_string_tuple(
                    raw_state.get("source_refs"),
                    f"source_summary.original_states[{index}].source_refs",
                ),
            )
        )

    raw_invariants = raw_source_summary.get("invariants")
    if not isinstance(raw_invariants, list):
        raise SpecError("source_summary.invariants must be a list")
    invariants: list[InvariantSpec] = []
    invariant_names: set[str] = set()
    for index, raw_invariant in enumerate(raw_invariants):
        if not isinstance(raw_invariant, dict):
            raise SpecError(f"source_summary.invariants[{index}] must be an object")
        name = require_string(
            raw_invariant.get("name"),
            f"source_summary.invariants[{index}].name",
        )
        if name in invariant_names:
            raise SpecError(f"duplicate invariant name: {name}")
        invariant_names.add(name)
        invariants.append(
            InvariantSpec(
                name=name,
                rule=require_string(
                    raw_invariant.get("rule"),
                    f"source_summary.invariants[{index}].rule",
                ),
                source_refs=require_string_tuple(
                    raw_invariant.get("source_refs"),
                    f"source_summary.invariants[{index}].source_refs",
                ),
            )
        )

    semantic_changes = require_string_tuple(
        raw_source_summary.get("semantic_changes"),
        "source_summary.semantic_changes",
        allow_empty=True,
    )
    raw_added_states = raw_source_summary.get("added_states")
    if not isinstance(raw_added_states, list):
        raise SpecError("source_summary.added_states must be a list")
    added_states: list[AddedStateSpec] = []
    added_state_names: set[str] = set()
    for index, raw_added_state in enumerate(raw_added_states):
        if not isinstance(raw_added_state, dict):
            raise SpecError(f"source_summary.added_states[{index}] must be an object")
        name = require_string(
            raw_added_state.get("name"),
            f"source_summary.added_states[{index}].name",
        )
        reason = require_string(
            raw_added_state.get("reason"),
            f"source_summary.added_states[{index}].reason",
        )
        if name in added_state_names:
            raise SpecError(f"duplicate added state name: {name}")
        if reason not in semantic_changes:
            raise SpecError(f"added state {name} uses undeclared semantic change: {reason}")
        added_state_names.add(name)
        added_states.append(AddedStateSpec(name=name, reason=reason))

    unresolved_ambiguities = require_string_tuple(
        raw_source_summary.get("unresolved_ambiguities"),
        "source_summary.unresolved_ambiguities",
        allow_empty=True,
    )
    if unresolved_ambiguities:
        raise SpecError("persistent generation requires all workflow ambiguities to be resolved")

    return SourceSummarySpec(
        source_path=source_path,
        source_sha256=source_sha256,
        source_items=tuple(source_items),
        original_states=tuple(original_states),
        invariants=tuple(invariants),
        semantic_changes=semantic_changes,
        unresolved_ambiguities=unresolved_ambiguities,
        added_states=tuple(added_states),
    )


def parse_transitions(
    raw_transitions: Any, actors: tuple[str, ...], states: tuple[str, ...]
) -> tuple[TransitionSpec, ...]:
    if not isinstance(raw_transitions, list):
        raise SpecError("transitions must be a list")

    transitions: list[TransitionSpec] = []
    names: set[str] = set()
    for index, raw_transition in enumerate(raw_transitions):
        if not isinstance(raw_transition, dict):
            raise SpecError(f"transition {index} must be an object")

        name = require_string(raw_transition.get("name"), f"transitions[{index}].name")
        from_state = require_string(raw_transition.get("from"), f"transitions[{index}].from")
        to_state = require_string(raw_transition.get("to"), f"transitions[{index}].to")
        actor = require_string(raw_transition.get("actor"), f"transitions[{index}].actor")
        required_evidence = require_string_tuple(
            raw_transition.get("required_evidence"),
            f"transitions[{index}].required_evidence",
            allow_empty=True,
        )
        gate = require_string(raw_transition.get("gate"), f"transitions[{index}].gate")
        gate_enforcement = require_string(
            raw_transition.get("gate_enforcement"),
            f"transitions[{index}].gate_enforcement",
        )
        source_refs = require_string_tuple(
            raw_transition.get("source_refs"),
            f"transitions[{index}].source_refs",
            allow_empty=True,
        )
        semantic_change = require_optional_string(raw_transition.get("semantic_change"), "")

        if name in names:
            raise SpecError(f"duplicate transition name: {name}")
        if from_state not in states:
            raise SpecError(f"transition {name} uses unknown from state: {from_state}")
        if to_state not in states:
            raise SpecError(f"transition {name} uses unknown to state: {to_state}")
        if actor not in actors:
            raise SpecError(f"transition {name} uses unknown actor: {actor}")
        if gate_enforcement not in GATE_ENFORCEMENTS:
            raise SpecError(f"transition {name} uses unsupported gate enforcement: {gate_enforcement}")
        if gate_enforcement == "none":
            if gate.lower() != "none" or required_evidence:
                raise SpecError(
                    f"transition {name} has a gate that the persistent runtime cannot enforce"
                )
        elif gate.lower() == "none" or not required_evidence:
            raise SpecError(
                f"transition {name} requires a described gate and required evidence"
            )

        names.add(name)
        transitions.append(
            TransitionSpec(
                name=name,
                from_state=from_state,
                to_state=to_state,
                actor=actor,
                required_evidence=required_evidence,
                gate=gate,
                gate_enforcement=gate_enforcement,
                source_refs=source_refs,
                semantic_change=semantic_change,
            )
        )

    return tuple(transitions)


def validate_source_provenance(
    source_summary: SourceSummarySpec,
    spec_directory: Path,
) -> None:
    source_path = Path(source_summary.source_path)
    resolved_source_path = source_path if source_path.is_absolute() else spec_directory / source_path
    if not resolved_source_path.is_file():
        raise SpecError(f"source workflow does not exist: {resolved_source_path}")

    source_bytes = resolved_source_path.read_bytes()
    actual_digest = hashlib.sha256(source_bytes).hexdigest()
    if actual_digest != source_summary.source_sha256:
        raise SpecError(
            "source workflow SHA-256 mismatch: "
            f"expected {source_summary.source_sha256}, got {actual_digest}"
        )

    try:
        source_text = source_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SpecError("source workflow must be UTF-8 text") from exc
    for source_item in source_summary.source_items:
        occurrence_count = source_text.count(source_item.quote)
        if occurrence_count != 1:
            raise SpecError(
                f"source item {source_item.item_id} quote must occur exactly once; "
                f"found {occurrence_count}"
            )


def validate_semantic_provenance(
    source_summary: SourceSummarySpec,
    states: tuple[str, ...],
    terminal_states: tuple[str, ...],
    transitions: tuple[TransitionSpec, ...],
) -> None:
    source_items = {item.item_id: item for item in source_summary.source_items}
    state_refs_by_state: dict[str, set[str]] = {state: set() for state in states}
    for original_state in source_summary.original_states:
        state_refs_by_state[original_state.mapped_state].update(original_state.source_refs)
    transition_refs = {ref for transition in transitions for ref in transition.source_refs}
    invariant_refs = {
        ref for invariant in source_summary.invariants for ref in invariant.source_refs
    }
    all_refs = set().union(*state_refs_by_state.values(), transition_refs, invariant_refs)
    unknown_refs = sorted(all_refs - set(source_items))
    if unknown_refs:
        raise SpecError(f"unknown source references: {', '.join(unknown_refs)}")

    for original_state in source_summary.original_states:
        if not any(source_items[ref].kind == "phase" for ref in original_state.source_refs):
            raise SpecError(
                f"original state {original_state.name} must reference a phase source item"
            )

    for invariant in source_summary.invariants:
        if not any(source_items[ref].kind == "invariant" for ref in invariant.source_refs):
            raise SpecError(f"invariant {invariant.name} must reference an invariant source item")

    for transition in transitions:
        if not transition.source_refs and not transition.semantic_change:
            raise SpecError(
                f"transition {transition.name} needs source references or a semantic change"
            )
        if transition.semantic_change and transition.semantic_change not in source_summary.semantic_changes:
            raise SpecError(
                f"transition {transition.name} uses undeclared semantic change: "
                f"{transition.semantic_change}"
            )
        if transition.gate_enforcement != "none" and transition.source_refs:
            if not any(source_items[ref].kind == "gate" for ref in transition.source_refs):
                raise SpecError(
                    f"transition {transition.name} must reference its gate source item"
                )

    added_state_names = {state.name for state in source_summary.added_states}
    incoming_refs_by_state: dict[str, set[str]] = {state: set() for state in states}
    for transition in transitions:
        incoming_refs_by_state[transition.to_state].update(transition.source_refs)
    for terminal_state in terminal_states:
        if terminal_state in added_state_names:
            continue
        terminal_refs = state_refs_by_state[terminal_state] | incoming_refs_by_state[terminal_state]
        if not any(source_items[ref].kind == "terminal_condition" for ref in terminal_refs):
            raise SpecError(
                f"terminal state {terminal_state} must reference a terminal condition"
            )

    compatible_refs = {
        "phase": set().union(*state_refs_by_state.values()),
        "action": set().union(*state_refs_by_state.values()) | transition_refs,
        "gate": transition_refs,
        "failure_path": transition_refs,
        "terminal_condition": transition_refs
        | set().union(*(state_refs_by_state[state] for state in terminal_states)),
        "invariant": invariant_refs,
    }
    unmapped_items = sorted(
        item.item_id
        for item in source_summary.source_items
        if item.item_id not in compatible_refs[item.kind]
    )
    if unmapped_items:
        raise SpecError(f"unmapped source items: {', '.join(unmapped_items)}")


def require_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SpecError(f"{field_name} must be a non-empty string")
    return value


def require_optional_string(value: Any, fallback: str) -> str:
    if value is None:
        return fallback
    if not isinstance(value, str):
        raise SpecError("optional string field must be a string")
    return value


def require_string_tuple(
    value: Any, field_name: str, *, allow_empty: bool = False
) -> tuple[str, ...]:
    if not isinstance(value, list) or (not value and not allow_empty):
        qualifier = "a list" if allow_empty else "a non-empty list"
        raise SpecError(f"{field_name} must be {qualifier}")
    result = tuple(require_string(item, f"{field_name}[]") for item in value)
    if len(set(result)) != len(result):
        raise SpecError(f"{field_name} must not contain duplicates")
    return result


def write_package(workflow: WorkflowSpec, output_dir: Path) -> None:
    if output_dir.exists():
        if not output_dir.is_dir():
            raise SpecError(f"output path is not a directory: {output_dir}")
        if any(output_dir.iterdir()):
            raise SpecError(f"output directory is non-empty: {output_dir}")

    instructions_dir = output_dir / "instructions"
    state_dir = output_dir / "state"
    logs_dir = output_dir / "logs"
    scripts_dir = output_dir / "scripts"
    tests_dir = output_dir / "tests"
    instructions_dir.mkdir(parents=True)
    state_dir.mkdir()
    logs_dir.mkdir()
    scripts_dir.mkdir()
    tests_dir.mkdir()

    write_text(instructions_dir / "state_contract.md", render_state_contract(workflow))
    write_text(
        instructions_dir / "source_workflow_reflection.md",
        render_source_workflow_reflection(workflow),
    )
    write_text(instructions_dir / "state_schema.md", render_state_schema(workflow))
    write_text(instructions_dir / "resume_protocol.md", render_resume_protocol(workflow))
    write_text(instructions_dir / "integration_contract.md", render_integration_contract(workflow))
    write_text(state_dir / ".gitkeep", "")
    write_text(logs_dir / ".gitkeep", "")
    write_text(scripts_dir / "state_machine.py", render_state_machine(workflow))
    write_text(scripts_dir / "init_state.py", render_init_state(workflow))
    write_text(scripts_dir / "apply_transition.py", render_apply_transition(workflow))
    write_text(tests_dir / "test_state_machine.py", render_tests(workflow))
    write_text(tests_dir / "test_state_runtime.py", render_runtime_tests(workflow))


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def render_state_contract(workflow: WorkflowSpec) -> str:
    actor_lines = "\n".join(f"- `{actor}`" for actor in workflow.actors)
    state_lines = "\n".join(render_state_line(workflow, state) for state in workflow.states)
    transition_rows = "\n".join(render_transition_row(transition) for transition in workflow.transitions)
    evidence_lines = "\n".join(render_evidence_lines(workflow))
    invariant_lines = "\n".join(
        f"- `{invariant.name}`: {invariant.rule} (source: {', '.join(invariant.source_refs)})"
        for invariant in workflow.source_summary.invariants
    ) or "- None declared."

    return f"""# {workflow.workflow_name} State Contract

Intent: {workflow.purpose}

Source Workflow Reflection: see `source_workflow_reflection.md` for `{workflow.source_summary.source_path}`.

## Actors

{actor_lines}

Runtime boundary: this is a single-process package. It does not provide locking, compare-and-swap, or concurrent-writer safety.

## States

{state_lines}

## Transitions

| Transition | From | To | Actor | Gate | Enforcement | Required Evidence | Source | Semantic Change |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
{transition_rows}

## Invariants

{invariant_lines}

These invariants are preserved from the source but are not automatically enforced by the bundled runtime. If an invariant controls transition legality, use a validator with an approved deterministic check instead of this persistent generator.

## Evidence

{evidence_lines}

## Invalid Moves

- Reject unknown states and unknown transitions.
- Reject transitions requested by the wrong actor.
- Reject transitions from the wrong source state.
- Reject missing required evidence.
- Reject accidental mutation of terminal states.

## Enforcement Boundary

The validator checks transition name, source state, actor, and non-empty evidence references. It does not verify that external evidence paths or records exist. Add deterministic workflow-specific checks only when they can be implemented and tested.
"""


def render_source_workflow_reflection(workflow: WorkflowSpec) -> str:
    source_item_rows = "\n".join(
        render_source_item_row(source_item)
        for source_item in workflow.source_summary.source_items
    )
    original_state_rows = "\n".join(
        render_original_state_row(original_state)
        for original_state in workflow.source_summary.original_states
    )
    invariant_lines = "\n".join(
        f"- `{invariant.name}`: {invariant.rule}; source: {', '.join(invariant.source_refs)}"
        for invariant in workflow.source_summary.invariants
    )
    semantic_change_lines = "\n".join(
        f"- {change}" for change in workflow.source_summary.semantic_changes
    )
    added_state_lines = "\n".join(
        f"- `{state.name}`: {state.reason}" for state in workflow.source_summary.added_states
    )
    if not semantic_change_lines:
        semantic_change_lines = "- None."
    if not added_state_lines:
        added_state_lines = "- None."

    return f"""# {workflow.workflow_name} Source Workflow Reflection

Intent: Record how the generated state machine was derived from the original workflow so state names, gates, and transitions are inspectable instead of invented.

## Source

- `{workflow.source_summary.source_path}`
- SHA-256: `{workflow.source_summary.source_sha256}`

## Verified Source Items

| ID | Kind | Exact Source Quote |
| --- | --- | --- |
{source_item_rows}

## Original States

| Original State | Generated State | Source References |
| --- | --- | --- |
{original_state_rows}

## Invariants

{invariant_lines or '- None.'}

## Semantic Changes

{semantic_change_lines}

## Added States

{added_state_lines}
"""


def render_original_state_row(original_state: OriginalStateSpec) -> str:
    return (
        f"| {original_state.name} | {original_state.mapped_state} | "
        f"{', '.join(original_state.source_refs)} |"
    )


def render_source_item_row(source_item: SourceItemSpec) -> str:
    quote = source_item.quote.replace("|", "\\|").replace("\n", " ")
    return f"| {source_item.item_id} | {source_item.kind} | {quote} |"


def render_state_line(workflow: WorkflowSpec, state: str) -> str:
    markers: list[str] = []
    if state == workflow.initial_state:
        markers.append("initial")
    if state in workflow.terminal_states:
        markers.append("terminal")
    suffix = f" ({', '.join(markers)})" if markers else ""
    description = render_state_description(workflow, state)
    return f"- `{state}`{suffix}: {description}"


def render_state_description(workflow: WorkflowSpec, state: str) -> str:
    source_matches = [
        original_state
        for original_state in workflow.source_summary.original_states
        if original_state.mapped_state == state
    ]
    if source_matches:
        names = ", ".join(f"`{source_state.name}`" for source_state in source_matches)
        source_refs = ", ".join(source_matches[0].source_refs)
        return f"Source state {names}; source references: {source_refs}"
    added_state = next(
        (added for added in workflow.source_summary.added_states if added.name == state),
        None,
    )
    if added_state is not None:
        return f"Added by approved semantic change: {added_state.reason}"
    if state in workflow.terminal_states:
        return "Terminal state added by formalization; see semantic changes in source_workflow_reflection.md."
    return "Generated workflow state; see source_workflow_reflection.md for derivation."


def render_transition_row(transition: TransitionSpec) -> str:
    evidence = ", ".join(transition.required_evidence) if transition.required_evidence else "none"
    source_refs = ", ".join(transition.source_refs) if transition.source_refs else "none"
    semantic_change = transition.semantic_change if transition.semantic_change else "none"
    return (
        f"| {transition.name} | {transition.from_state} | {transition.to_state} | "
        f"{transition.actor} | {transition.gate} | {transition.gate_enforcement} | "
        f"{evidence} | {source_refs} | {semantic_change} |"
    )


def render_evidence_lines(workflow: WorkflowSpec) -> list[str]:
    evidence_to_transitions: dict[str, list[str]] = {}
    for transition in workflow.transitions:
        for evidence in transition.required_evidence:
            evidence_to_transitions.setdefault(evidence, []).append(transition.name)
    evidence_keys = sorted(evidence_to_transitions)
    if not evidence_keys:
        return ["- No evidence keys are required by the current transition table."]
    return [
        render_evidence_line(key, evidence_to_transitions[key])
        for key in evidence_keys
    ]


def render_evidence_line(key: str, transition_names: list[str]) -> str:
    joined = "`, `".join(transition_names)
    return f"- `{key}`: required evidence for `{joined}`."


def render_state_schema(workflow: WorkflowSpec) -> str:
    return f"""# {workflow.workflow_name} State Schema

Intent: Define durable state records for the {workflow.workflow_name} workflow.

## Canonical State

- `workflow`: `{workflow.workflow_name}`
- `instance_id`: stable workflow instance id
- `state`: one of {', '.join(workflow.states)}
- `updated_by`: actor that applied the last accepted transition
- `updated_at`: timestamp written by the canonical state owner
- `last_transition`: last accepted transition name, or null for a new instance
- `evidence`: durable evidence map for the last accepted transition

Initialize this record with `scripts/init_state.py` before executing normal workflow steps.

## Transition Request

- `transition`: requested transition name
- `actor`: requesting actor
- `from_state`: actor's observed current state
- `evidence`: map of required evidence keys to durable values

## Write Ownership

- The process that invokes the scripts writes canonical state.
- Other actors may write transition requests or handoff records.
- Every accepted transition appends a JSONL log record during normal execution.

## Runtime Boundary

State replacement is atomic only within one process using the same filesystem. The generated runtime does not coordinate concurrent writers or guarantee crash-durable logs.
"""


def render_resume_protocol(workflow: WorkflowSpec) -> str:
    return f"""# {workflow.workflow_name} Resume Protocol

Intent: Let a fresh agent continue the workflow from durable state without conversation memory.

## Steps

1. Load the canonical state record.
2. If no canonical state exists for this workflow instance, initialize one with `scripts/init_state.py`.
3. Read pending transition requests or handoffs.
4. Validate each request through `scripts/apply_transition.py`, which calls `scripts/state_machine.py`.
5. Apply the next transition only after the prior command completes successfully.
6. Reject or quarantine invalid requests with the error message.
7. Append a durable transition log entry.

## Single-Process Boundary

Run one transition command at a time for an instance. The package does not implement duplicate-action suppression or concurrent-writer coordination.

## Stop Conditions

Stop when canonical state reaches one of these terminal states: {', '.join(workflow.terminal_states)}.
"""


def render_integration_contract(workflow: WorkflowSpec) -> str:
    return f"""# {workflow.workflow_name} Integration Contract

Intent: Make the state machine active during normal workflow execution, not only during audits or resumes.

## Required Entry Step

Before starting the workflow, load or initialize canonical state:

```bash
python workflow_state_machine/scripts/init_state.py \\
  --state-path workflow_state_machine/state/canonical_state.json \\
  --instance-id <stable-instance-id> \\
  --updated-by <actor>
```

If the state file already exists, load it and resume from its `state` value. Do not create a second active state file for the same workflow instance.

## Required Transition Step

Every lifecycle move must go through the transition runner:

```bash
python workflow_state_machine/scripts/apply_transition.py \\
  --state-path workflow_state_machine/state/canonical_state.json \\
  --log-path workflow_state_machine/logs/transitions.jsonl \\
  --transition <transition-name> \\
  --actor <actor> \\
  --evidence key=value
```

The prose workflow must not bypass canonical state. Markdown explains the lifecycle, but `state/canonical_state.json` is the single-process runtime source of truth. Do not run concurrent transition commands against the same state file.

## Final Handoff

Before final handoff, the workflow should either reach a terminal state or explicitly report the current canonical state and why it remains non-terminal.
"""


def render_state_machine(workflow: WorkflowSpec) -> str:
    transition_rules = "\n".join(render_transition_rule(transition) for transition in workflow.transitions)
    return STATE_MACHINE_TEMPLATE.substitute(
        workflow_name=workflow.workflow_name,
        states_repr=repr(workflow.states),
        initial_state_repr=repr(workflow.initial_state),
        terminal_states_repr=repr(workflow.terminal_states),
        transition_rules=transition_rules,
    )


def render_init_state(workflow: WorkflowSpec) -> str:
    return INIT_STATE_TEMPLATE.substitute(
        workflow_name=workflow.workflow_name,
        workflow_name_repr=repr(workflow.workflow_name),
    )


def render_apply_transition(workflow: WorkflowSpec) -> str:
    return APPLY_TRANSITION_TEMPLATE.substitute(
        workflow_name=workflow.workflow_name,
        workflow_name_repr=repr(workflow.workflow_name),
    )


def render_transition_rule(transition: TransitionSpec) -> str:
    return (
        f"    {transition.name!r}: TransitionRule("
        f"name={transition.name!r}, "
        f"from_state={transition.from_state!r}, "
        f"to_state={transition.to_state!r}, "
        f"actor={transition.actor!r}, "
        f"required_evidence={transition.required_evidence!r}"
        f"),"
    )


def render_tests(workflow: WorkflowSpec) -> str:
    transition_cases: list[dict[str, object]] = []
    non_terminal_states = [
        state for state in workflow.states if state not in workflow.terminal_states
    ]
    for transition in workflow.transitions:
        wrong_actor = next(
            (actor for actor in workflow.actors if actor != transition.actor),
            f"not-{transition.actor}",
        )
        wrong_source = next(
            (state for state in non_terminal_states if state != transition.from_state),
            "__unknown_state__",
        )
        wrong_source_message = (
            "unknown source state"
            if wrong_source == "__unknown_state__"
            else "requires source state"
        )
        transition_cases.append(
            {
                "name": transition.name,
                "actor": transition.actor,
                "wrong_actor": wrong_actor,
                "from": transition.from_state,
                "wrong_source": wrong_source,
                "wrong_source_message": wrong_source_message,
                "to": transition.to_state,
                "evidence": test_evidence(transition.required_evidence),
            }
        )
    return TEST_TEMPLATE.substitute(
        transition_cases_repr=repr(transition_cases),
    )


def render_runtime_tests(workflow: WorkflowSpec) -> str:
    terminal_paths = []
    for terminal_state, path in find_terminal_paths(workflow).items():
        terminal_paths.append(
            {
                "terminal": terminal_state,
                "steps": [
                    {
                        "name": transition.name,
                        "actor": transition.actor,
                        "evidence": test_evidence(transition.required_evidence),
                    }
                    for transition in path
                ],
            }
        )
    return RUNTIME_TEST_TEMPLATE.substitute(
        initial_state_repr=repr(workflow.initial_state),
        terminal_paths_repr=repr(terminal_paths),
    )


def test_evidence(required_evidence: tuple[str, ...]) -> dict[str, str]:
    return {key: f"evidence/{key}.txt" for key in required_evidence}


def find_terminal_paths(
    workflow: WorkflowSpec,
) -> dict[str, tuple[TransitionSpec, ...]]:
    transitions_by_source: dict[str, list[TransitionSpec]] = {
        state: [] for state in workflow.states
    }
    for transition in workflow.transitions:
        transitions_by_source[transition.from_state].append(transition)

    paths: dict[str, tuple[TransitionSpec, ...]] = {}
    for terminal_state in workflow.terminal_states:
        pending: list[tuple[str, tuple[TransitionSpec, ...]]] = [
            (workflow.initial_state, ())
        ]
        visited: set[str] = set()
        while pending:
            state, path = pending.pop(0)
            if state == terminal_state:
                paths[terminal_state] = path
                break
            if state in visited:
                continue
            visited.add(state)
            for transition in transitions_by_source[state]:
                pending.append((transition.to_state, path + (transition,)))
    return paths


if __name__ == "__main__":
    raise SystemExit(main())
