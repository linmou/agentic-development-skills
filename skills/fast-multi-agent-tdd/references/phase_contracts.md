# Intent

Define the smallest enforceable phase boundaries for `fast-multi-agent-tdd`.

## Before TDD

Requirement re-check, mixed-work classification, and path preflight happen before phase ownership begins.

- Classify each requirement as executable, guidance, rubric, data, research, or result work.
- Put only executable behavior under Red-Green-Refactor.
- Keep required non-code artifacts outside TDD phases; do not use TDD ordering to delay them.
- Record planned paths and semantic roles before Red.
- Resolve lexical collisions before edits. A human-approved semantic classification recorded in the requirement map overrides the default path heuristic for that exact path or bounded subtree.

## Dynamic Scope Artifact

Each phase publishes the scope for the next phase under `audits/`:

```json
{
  "schema": 1,
  "feature": "stripe_webhook",
  "phase": "green",
  "baseline_ref": "refs/codex/tdd/stripe_webhook/red",
  "protected": ["tests/**", "features/**", "docs/**", "audits/**"],
  "editable": [],
  "semantic_overrides": {"src/tests/runtime.py": "prod"}
}
```

At a transition, write the next-phase artifact first, then capture the tracked
and untracked worktree into a Git snapshot so the immutable baseline contains
that artifact, and record the baseline ref and commit in the phase output.
The guard treats the baseline ref as authoritative, verifies the current scope
bytes at the same repository-relative path before parsing, and fails closed on
mutation, deletion, malformed content, missing baseline copy, symlink aliases,
or out-of-repository paths. It includes both sides of renames and deleted paths,
normal untracked files, and ignored untracked files using NUL-safe Git status.
Ignored files are enforceable changes, not a hiding place. Overlapping semantic
override patterns with different classifications are conflicts; exact paths and
terminal `/**` are the only supported pattern forms. Production phases can omit
`editable`; Test Refactor and Documentation must include it. Protected paths
always win over editable paths.

Phase refs are append-only: creating an existing `refs/codex/tdd/<feature>/<phase>`
is an error and never overwrites the prior snapshot. Replay worktrees and refs
are retained for explicitly preserved blocked runs and removed by feature
cleanup after terminal closeout.

The guard accepts exact paths and bounded terminal `/**` patterns only. It
rejects malformed paths, missing or mismatched baseline refs, invalid artifacts,
and unresolved semantic conflicts. Lexical classification is a default safety
check, not permission to guess when a path's location and filename imply
different roles.

## Phase Ownership

### Request Map

- Main output: requirement map, test seam choice, feature label
- Allowed edits: docs, notes, planning artifacts
- Forbidden edits: tests, production code

### Red

- Main output: the next failing test
- Scope policy: phase-kind checks plus the protected paths in the Red artifact
- Allowed edits:
  - files under `tests/`
  - files under `__tests__/`
  - files matching `*.test.*`
  - files matching `*.spec.*`
  - files matching `*.feature`
  - short docs or notes explaining the test seam
- Forbidden edits:
  - production code
  - config churn unrelated to making the test runnable

### Green

- Main output: the smallest production change that makes red pass
- Scope policy: phase-kind checks plus protected paths; production files remain flexible for newly discovered modules
- Allowed edits:
  - production code
  - minimal runtime wiring required by the failing test
- Forbidden edits:
  - any test file
  - any feature file
  - broad refactors

### Regression

- Main output: targeted plus full-suite test evidence
- Allowed edits: none, unless the run exposes a real issue that forces a return to red or green
- Forbidden edits:
  - silent fixes during the check itself

### Refactor

- Main output: cleaner production code with behavior held constant
- Scope policy: phase-kind checks plus protected paths; production files remain flexible for cumulative cleanup
- No-op rule: if no cleanup is needed, record that inspection in the Refactor artifact and do not invent code churn
- Allowed edits:
  - production code
- Forbidden edits:
  - any test file
  - any feature file
  - doc-like files such as `README.md`, `.md`, `.rst`, or `.txt`
  - new behavior disguised as cleanup

### Test Refactor

- Main output: clearer tests with the Red specification and execution boundaries preserved
- Scope policy: phase-kind checks, protected paths, and the explicit `editable` list of Red tests and directly shared test support
- No-op rule: record inspection and do not invent test churn when no demonstrated smell warrants change
- Allowed edits:
  - test-like paths selected in the request map
  - directly shared test support under a test-like path
- Forbidden edits:
  - production, documentation, runtime configuration, or test-selection files
  - new behavior, changed expectations, weakened assertions, silent deselection, skips, or `xfail`
  - replacing a required high-risk boundary with a lower-level mock
- Return-to-Red rule: stop when the work reveals a missing case, wrong oracle, changed boundary, or requirement conflict

### Documentation

- Main output: documentation that matches the already-completed code change
- Scope policy: documentation kind, protected paths, and the explicit `editable` documentation list
- Allowed edits:
  - doc-like files such as `.md`, `.rst`, `.txt`, or files under `/docs/`
- Forbidden edits:
  - production code
  - any test file
  - design churn unrelated to the completed implementation

### Final

- Main output: closeout that cites the Red audit, Green gate, regression check, cumulative production Refactor audit, Test Refactor audit, and docs artifact when docs were updated
- Allowed edits: none
- Forbidden edits: any test, production, or documentation changes during closeout

## File Classification Heuristics

Use these as the default monitor rules:

- test-like:
  - path contains `/tests/`
  - path contains `/__tests__/`
  - basename contains `.test.`
  - basename contains `.spec.`
  - suffix is `.feature`
- doc-like:
  - suffix is `.md`, `.rst`, or `.txt`
  - path contains `/docs/`
- everything else is treated as production-like unless a human explicitly overrides it

If a path cannot be classified confidently, the monitor should mark it ambiguous and ask for a human decision instead of guessing.

Do this preflight before Red, not after a passing Green implementation exposes the collision.
