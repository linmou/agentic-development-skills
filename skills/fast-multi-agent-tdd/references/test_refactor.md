# Intent

Define a behavior-preserving Test Refactor stage that improves test design
without weakening the specification established in Red.

## Entry Contract

Enter only after Green regression passes and the cumulative production Refactor
audit converges. Default scope is the tests changed in Red plus directly shared
test support. Broader neighboring test cleanup requires explicit scope in the
request map.

Before editing:

- snapshot production and test paths, collected test IDs, and targeted/full
  suite results
- write a behavior map for each affected test:
  `stimulus -> boundary crossed -> observable result -> important edge case`
- run `$code-smell-monitor` on the selected test scope
- preflight every planned path with `phase_guard.py --phase test_refactor --scope <scope-artifact>`

If no demonstrated test smell exists and the test diff is empty, write
`audits/<feature>_test_refactor_noop.md` recording the inspection and scope
checks. Do not manufacture churn merely because the phase exists.

## Design Principles

### Independent Oracle

Expected results must not be calculated by the production function or algorithm
being tested. Use literals, independently constructed fixtures, or an external
contract. Replacing a circular oracle with an equivalent independent oracle is
a refactor; discovering a different expected result requires a return to Red.

### Behavior Preservation

Every pre-refactor behavior must map to an equivalent post-refactor test.
Preserve behavior, not raw test count or test IDs: legitimate splitting,
renaming, consolidation, and parametrization may change both. Keep overlapping
tests when they protect different boundaries or failure modes.

### Boundary Honesty

Name and organize a test according to the boundary it actually crosses. Do not
replace a required subprocess, filesystem, network, concurrency, database, or
external-tool boundary with a mock or command-construction assertion merely to
simplify the test. Changing the required boundary returns the workflow to Red.

### Cohesive Failure

A test should have one cohesive reason to fail, not necessarily one assertion.
Integration tests may need several assertions to prove one lifecycle invariant.
Replace large branching scenario engines with declarative parametrization or
separate tests when the branches describe independent behaviors.

### Transparent Setup

Extract mechanical setup such as temporary repositories, baseline configuration,
or fake executables. Keep scenario inputs, boundary evidence, and expected
results visible in the test. Avoid fixtures or builders that silently invent
behavior-critical values.

### Pragmatic Duplication

Do not apply DRY mechanically. Extract repeated mechanics, not assertions or
behavioral differences. Tests are duplicates only when stimulus, boundary,
oracle, and protected failure mode are equivalent.

### Determinism And Isolation

Do not depend on execution order, artifacts from another test, fixed ports,
arbitrary sleeps, uncontrolled external state, or unbounded waits. Keep live
network, GPU, container, namespace, and host-tool checks in an explicit system
test category with prerequisites and timeouts.

### Diagnostics And Organization

Test names and parameter IDs should state behavior. Failures should identify the
violated contract without reverse-engineering a large fixture. Organize tests by
production responsibility and boundary level when that makes selection and
ownership clearer; do not impose a repository-wide directory rewrite during an
unrelated feature slice.

## Allowed Changes

- rename, split, consolidate, or parametrise behavior-equivalent tests
- extract simple test-only fixtures, builders, and support code
- move tests between test-like paths to reflect their real responsibility or
  boundary level
- replace a circular oracle with an independently derived equivalent oracle
- improve assertions, cleanup, bounded waits, and failure diagnostics without
  changing the specified behavior

## Forbidden Changes

- production, documentation, runtime configuration, or test-selection edits
- new behavior, new edge cases, or changed expected outcomes
- removing an assertion without an explicit behavior-map successor
- adding or broadening skips, `xfail`, retries, mocks, or environment bypasses
- weakening a real high-risk boundary into a lower-level simulation
- deleting existing tests without applicable repository or user permission
- cleanup outside the selected test scope

A newly discovered missing case, incorrect expectation, inadequate boundary, or
requirement conflict is useful evidence, but it is not Test Refactor work. Stop
and return to Red.

## Exit Gate

Before the mandatory Test Refactor debate:

1. Run the `test_refactor` phase guard on every changed path.
2. Compare pre/post collection and map every intentional rename, split,
   consolidation, or parametrization; reject silent deselection.
3. Run targeted and full suites under the same selection and resource policy.
4. Replay at least the original Red behavior against the pre-Green production
   snapshot and confirm it still fails for the original missing-behavior reason.
5. Confirm production and documentation snapshots are unchanged.
6. Re-run `$code-smell-monitor` on the same test scope and record before/after
   reports.
7. Audit the test diff, behavior map, collection comparison, boundary evidence,
   replay result, suite results, and smell reports with
   `$review-with-multi-debate`.

The stage closes only when the aggregate audit status is `converged` and every
blocking criterion passes.
