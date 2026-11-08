# Redundant code and execution review

The monitor reports possible redundancies; it does not remove application code or tests, prove a safe deletion, or launch a second issue-generation pipeline. Use the existing `code_smell_report.md` and raw tool records. Apply this workflow across languages/frameworks only where actual evidence is available.

## 1. Dead code and production reachability

For a JavaScript/TypeScript package root, compare the same package's ordinary `knip --reporter json` and `knip --production --reporter json`. Do not delete or rewrite tests to induce a signal. The runner records both invocations, statuses, the package scope and `knip_production_only_candidates` in the normal summary. The records are exact JSON differences; they are **not** a proof that a symbol is referenced exclusively from tests. Knip's supported entrypoints/configuration, generated calls, dynamic loading, external/public API consumers and alternative reporter shapes may change the interpretation.

Inspect `raw/knip_dead_code.json`, `raw/knip_production.json`, `summary.json` coverage and the actual import/reference sites before reporting a suspected legacy implementation. If either run fails or its coverage is unclear, report an incomplete comparison instead of a zero finding.

## 2. Redundant implementations

When two *reachable* functions appear to implement the same responsibility, `knip` will not flag them. For each candidate, identify:

1. Its production entrypoint and actual callers (a static call graph or language-server references, not the import graph alone).
2. Its input parameters, state and data dependencies, output/side effects, and any common downstream operations.
3. The conditions that invoke each implementation and the documented reason for separate paths, if any.
4. Whether repo history shows a migration or superseded implementation. Old and new code coexisting is a review candidate, not proof of incorrect redundancy.

Use existing AST/call-graph/data-flow tools where available. Prefer language-appropriate analyzers over bespoke regex. Report uncertainty for dynamic invocation and unresolved imports. Do not hard-code a dependency on any named documentation architecture.

## 3. Redundant execution

Trace `trigger -> callback -> callee -> resource operation`, including language/framework semantics supported by evidence (e.g., subscription callback, lifecycle effect, request handler). Identify the same concrete resource, comparable operation and relevant key arguments, and whether triggers overlap. Avoid equating two references to the same function with simultaneous execution.

Review ordering, cancellation, retry/backoff, state transitions, idempotency, authorization and recovery conditions. Multiple reads on initialization can be necessary to close the gap between initial history and event subscription.

Diagnostic traces, profiling counters or existing tests can supply *observations* to the report if already available. Do not run behavioral correctness verification, mutate the application or claim behavior-preserving deletion.

## 4. Agent-level evaluation cases

| Case | Expected monitor outcome |
| --- | --- |
| Legacy JS/TS export used only in tests and benchmarks | Production-only Knip candidate if normal mode hides it; inspect test references; preserve tests |
| Dynamic or public export reachable outside the analyzed package | Qualified uncertainty, not "safe to delete" |
| Two reachable initializers read the same resource | Flag overlapping calls only when triggers, parameters and resource identity support it |
| History read plus missed-event recovery reconciliation | State alternative explanation; never call one a confirmed defect without evidence |
| Two uses of the same table for different users or phases | No automatic redundancy inference |
| Unresolved imports or unavailable Knip | Partial/unavailable coverage, not a clean scan |

If coverage or trigger identity is inadequate, present the missing analysis rather than constructing a behavioral claim.
