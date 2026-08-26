# Intent

Define the smallest enforceable phase boundaries for `fast-multi-agent-tdd`.

## Before TDD

Requirement re-check, mixed-work classification, and path preflight happen before phase ownership begins.

- Classify each requirement as executable, guidance, rubric, data, research, or result work.
- Put only executable behavior under Red-Green-Refactor.
- Keep required non-code artifacts outside TDD phases; do not use TDD ordering to delay them.
- Record planned paths and semantic roles before Red.
- Resolve lexical collisions before edits. A human-approved semantic classification recorded in the requirement map overrides the default path heuristic for that exact path or bounded subtree.

## Phase Ownership

### Request Map

- Main output: requirement map, test seam choice, feature label
- Allowed edits: docs, notes, planning artifacts
- Forbidden edits: tests, production code

### Red

- Main output: the next failing test
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
- Allowed edits:
  - production code
- Forbidden edits:
  - any test file
  - any feature file
  - doc-like files such as `README.md`, `.md`, `.rst`, or `.txt`
  - new behavior disguised as cleanup

### Documentation

- Main output: documentation that matches the already-completed code change
- Allowed edits:
  - doc-like files such as `.md`, `.rst`, `.txt`, or files under `/docs/`
- Forbidden edits:
  - production code
  - any test file
  - design churn unrelated to the completed implementation

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
