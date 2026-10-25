# Canonical Diagnostic Definitions

**Intent:** Define where a failure mechanism operates, how its cause is attributed, and how any generalization is bounded. Adapted from `diagnose-agentic-coding` and made domain-independent: functions and artifact types come from the case's task ontology, not from a fixed list.

## Failure framing

Every diagnosis explains an observed deviation from an intended outcome. A deviation is a point where the run departs from what the success conditions require.

## Node, Edge, and Interaction

These describe **where and how a mechanism operates**, not necessarily its causal origin.

### Node: action transformation

A Node is a concrete `(actor, action)` event classified by a task-ontology function. It consumes available inputs and may produce artifacts, change World, or both.

**Node deviation:** an action produces a result that departs from a supported case-specific expectation.

**Is:** incorrect interpretation or use of an available artifact; incorrect reasoning, decision, execution, or verification; incorrect artifact production or world-state change.

**Is not:** a function type without a concrete action instance; automatically responsible when its input was already defective; automatically a model failure, since actors include humans, harnesses, tools, and evaluators.

### Edge: artifact handoff

An Edge is the provision of an identifiable artifact version to a consuming action. The task ontology defines **potential** dependencies; the case graph records actual or missing handoffs.

**Edge deviation:** a causally relevant handoff is missing or defective.

**Is:** missing delivery; incorrect routing, truncation, or version; failure to make an artifact available to its consumer.

**Is not:** a mandatory workflow transition; a failure merely because a potential dependency was not exercised; misinterpretation of a correctly delivered artifact, which belongs to the consuming Node.

### Interaction: joint mechanism

An Interaction is a mechanism in which the effect of one factor depends on another. Factors may be artifacts, Nodes, Edges, world state, capabilities, or operating conditions.

**Is:** incompatible instructions and tool constraints; a model tendency that matters only under a particular harness policy; a mechanism whose outcome changes when the combination changes.

**Is not:** a third physical location in the graph; mere coexistence of several errors; a sequential chain without evidence of joint dependence.

Node and Edge are locations; Interaction is a causal relationship over locations and conditions. They may coexist. Configuration is represented as defined in [meta-ontology.md](meta-ontology.md).

## Three attribution levels

### Level 1: Location

*Where and how did the run depart from what the intended outcome required?*

Locate Node, Edge, and Interaction instances, affected artifact and world-state versions, and absences, with evidence and uncertainty. Location is not causation and not responsibility.

### Level 2: Root causal mechanism

*Why did the departure occur, and what produced or enabled it?*

Trace upstream through artifacts, actions, actors, capabilities, configuration, and environment to the deepest evidence-supported mechanism within the boundary. Consider origins in user requests, model behavior or capability, harness or developer actions, and third-party or environmental conditions. Preserve joint causes and rivals. Do not equate rootness with the earliest event, the most upstream actor, or the easiest intervention. If evidence is insufficient, report **root cause undetermined**.

### Level 3: Generalization conditions

*When would the same mechanism produce similar behavior again?*

State recurrence conditions, scope limits, testable predictions, and candidate interventions. Phrase conditions in task-independent terms, with the case types mapped to them, so another case can test the claim. One case supports a case-specific mechanism or a transferable hypothesis, not a stable capability claim.

| Level | Object | Result |
| --- | --- | --- |
| 1. Location | Node / Edge / Interaction / absence | Localized departure |
| 2. Root mechanism | Causal provenance | Why it occurred |
| 3. Generalization | Mechanism and its conditions | Where it may recur and how to prevent it |

**Example (research agent reports the wrong figure).** Level 1: an extraction action bound a claim to an adjacent table row (Node), and no verification of the claim–source binding occurred (absence). Level 2: the page's table layout plus text-only page rendering (Interaction) made row boundaries ambiguous; the agent task model treated "a figure from a cited page" as completion. Level 3: may recur when numeric claims are extracted from tabular pages without structural rendering and completion requires only citation presence. Intervention: verify claim–source bindings; this is an intervention target, not the cause.

## Cross-cutting principles

1. Potential dependencies are not obligations.
2. Location is not causation.
3. Causation need not be singular.
4. Rootness is evidence-bounded.
5. Transferability must be qualified.
6. Vocabulary must not decide the ranking: the host checks every returned model for expressibility ([ontology-induction.md](ontology-induction.md)).
7. Causal inference is delegated to `competing-explanations-causal-research`.
