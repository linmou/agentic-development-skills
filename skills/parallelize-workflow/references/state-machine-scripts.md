# State Machine Scripts

## Contents

- Keep the enforcement small
- Generate executable state-machine files
- Enforce transitions in code
- Test the contract

## Keep the enforcement small

Use this rule:

```text
Markdown explains the contract.
Scripts enforce the contract.
Tests prove the script rejects bad transitions.
```

Do not build a framework when a small monitor and transition validator are enough.

## Generate executable state-machine files

For runnable parallel workflows, include scripts in the generated workflow package unless the target repo already has equivalent machinery.

Use this shape by default:

```text
parallel_workflow/
  scripts/
    state_machine.py
    monitor.py
    worker_launcher.py
  tests/
    test_state_machine.py
```

`worker_launcher.py` is optional when workers are started manually or by an existing runner.

Every new script file must start with a shebang and a short purpose comment.

## Enforce transitions in code

`state_machine.py` should own:
- legal states
- legal transitions
- actor permissions
- required evidence checks
- terminal states
- retry and stale-lease rules when they are purely state-based

`monitor.py` should own:
- loading canonical state
- loading handoffs
- validating each requested transition through `state_machine.py`
- accepting, rejecting, requeuing, blocking, or reclaiming work
- writing canonical state atomically
- emitting durable logs

Keep workflow-specific acceptance checks explicit. If an acceptance check needs external tools, make the monitor call that check by name and record the evidence path.

Workers may write handoff files. Workers must not write canonical state directly.

## Test the contract

Add focused tests for:
- legal transition succeeds
- illegal transition is rejected
- missing required evidence is rejected
- worker cannot promote its own output
- stale lease can be reclaimed
- accepted terminal state is not mutated accidentally
- monitor replay does not duplicate promotion

Prefer small deterministic tests over end-to-end orchestration tests at this layer.
