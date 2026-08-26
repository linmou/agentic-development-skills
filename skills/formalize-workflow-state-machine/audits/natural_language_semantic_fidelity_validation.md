# Natural-Language Semantic Fidelity Validation

Intent: Preserve the inputs, observable outcomes, environment, and limits used to verify the revised workflow formalization skill.

## Metadata

- Date: 2026-08-20
- Workspace: `/Users/admin/.codex/skills/formalize-workflow-state-machine`
- Runtime: local Python invoked through `rtk`
- Scope: generator, generated runtime/tests, skill instructions, contract/spec references, and UI metadata

## Behavioral Evidence

| Input or mutation | Expected outcome | Observed outcome |
| --- | --- | --- |
| Digest-matching source with uniquely quoted and completely mapped items | Generate documented runtime package | Passed |
| Missing source path | Reject before output creation | Passed |
| Source changed after SHA-256 capture | Reject before output creation | Passed |
| Exact source quote absent | Reject before output creation | Passed |
| Extracted failure path left unmapped | Reject as unmapped source item | Passed |
| Invented source reference | Reject as unknown source reference | Passed |
| Gate described but marked unenforced | Reject persistent generation | Passed |
| Unresolved workflow ambiguity | Reject persistent generation | Passed |
| Added state and transition with an approved semantic-change reason | Generate and document the addition | Passed |
| Three legal transitions and two terminal outcomes | Generated tests exercise every transition and a path to both terminals | Passed |
| Attempt to reinitialize a terminal instance with `--force` | Reject and preserve the terminal state bytes | Passed |
| Non-empty output directory with sentinel file | Reject and preserve the sentinel | Passed |

## Commands and Results

- Direct execution of all 12 `test_*` functions in `tests/test_create_state_machine_package.py`: passed.
- `mypy scripts/create_state_machine_package.py tests/test_create_state_machine_package.py`: passed with no issues.
- `python -m compileall -q scripts tests`: passed.
- `ruff check scripts/create_state_machine_package.py tests/test_create_state_machine_package.py`: passed with zero findings.
- `quick_validate.py /Users/admin/.codex/skills/formalize-workflow-state-machine`: `Skill is valid!`.
- `python -m pytest -q`: unavailable; the local process exits with signal 11 before producing test results. The same test functions execute successfully through the direct runner.

## Remaining Boundary

The generator verifies source identity, exact citations, typed coverage, and explicit additions. It cannot prove that a human or model attached a semantically related quote to the correct state; proposal review remains the final semantic judgment. The persistent runtime remains single-process and does not interpret evidence values, enforce prose invariants, or provide crash-durable state/log transactions.
