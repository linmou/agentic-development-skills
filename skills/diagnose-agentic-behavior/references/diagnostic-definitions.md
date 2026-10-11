# Canonical Diagnostic Definitions

**Intent:** Define how a failure is framed, how its cause is attributed, and how any generalization is bounded. Adapted from `diagnose-agentic-coding` and made domain-independent: functions and artifact types come from the case's task ontology, not from a fixed list.

## Failure framing

Every diagnosis explains an observed deviation from an intended outcome. A deviation is a point where the run departs from what the success conditions require.

## Deviations on the ontology graph

Node, Edge, and Interaction ([meta-ontology.md](meta-ontology.md)) locate where a mechanism operates, not its causal origin.

- **Node deviation:** the action's output departs from a supported case-specific expectation, given the inputs in its context. A Node is not responsible by default when its input was already defective, and not a model failure by default, since actors include humans, harnesses, tools, and evaluators.
- **Edge deviation:** a causally relevant Edge is missing, misrouted, truncated, or delivers the wrong version. A potential Edge the run did not exercise is a deviation only with evidence of causal relevance. Misuse of an artifact that was in context is a deviation of the consuming Node, not of the Edge.
- **Interaction deviation:** the members jointly produce a departure that none produces alone. It is located by its members.
- **Error of omission:** an expected type with status `absent`, never `unobserved`.
- **Claim–environment disagreement:** a claim contradicted by grounded environment state is a finding.

## Three attribution levels

### Level 1: Location

*Where and how did the run depart from what the intended outcome required?*

Locate Node, Edge, and Interaction instances, affected artifact versions, and errors of omission, with evidence and uncertainty. Location is not causation and not responsibility.

### Level 2: Root causal mechanism

*Why did the departure occur, and what produced or enabled it?*

Trace upstream through artifacts, actions, actors, capabilities, configuration, and environment to the deepest evidence-supported mechanism within the boundary. Consider origins in user requests, model behavior or capability, harness or developer actions, and third-party or environmental conditions. Preserve joint causes and rivals. Do not equate rootness with the earliest event, the most upstream actor, or the easiest intervention. If evidence is insufficient, report **root cause undetermined**.

### Level 3: Generalization conditions

*When would the same mechanism produce similar behavior again?*

State recurrence conditions, scope limits, testable predictions, and candidate interventions. Phrase conditions in task-independent terms, with the case types mapped to them, so another case can test the claim. One case supports a case-specific mechanism or a transferable hypothesis, not a stable capability claim.

| Level | Object | Result |
| --- | --- | --- |
| 1. Location | Node / Edge / Interaction / error of omission | Localized departure |
| 2. Root mechanism | Causal provenance | Why it occurred |
| 3. Generalization | Mechanism and its conditions | Where it may recur and how to prevent it |

**Example (research agent reports the wrong figure).** Level 1: an extraction action bound a claim to an adjacent table row (Node, error of commission), and no verification of the claim–source binding occurred (error of omission). Level 2: the page's table layout plus text-only page rendering (Interaction) made row boundaries ambiguous, and the harness's completion check required only that a figure be cited. Level 3: may recur when numeric claims are extracted from tabular pages without structural rendering and completion requires only citation presence. Intervention: verify claim–source bindings; this is an intervention target, not the cause.

## Cross-cutting principles

1. Potential dependencies are not obligations.
2. Location is not causation.
3. Causation need not be singular.
4. Rootness is evidence-bounded.
5. Transferability must be qualified.
6. Vocabulary must not decide the ranking: the host checks every returned model for expressibility ([ontology-induction.md](ontology-induction.md)).
7. Causal inference is delegated to `competing-explanations-causal-research`.
