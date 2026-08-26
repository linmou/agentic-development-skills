# Diagnostic Protocol

## 1. Distinguish the objects of diagnosis

| Object | Meaning | Example |
| --- | --- | --- |
| Outcome | The bounded result to explain. | Repository tests fail after the run. |
| Manifestation | An observable sign of deviation. | A null check was removed. |
| Mechanism | The process connecting conditions to the outcome. | Stale state representation caused the agent to edit an obsolete path. |
| Attribution target | The system element or interaction that realizes the mechanism. | Context manager × model attention, not “the model” alone. |
| Corrective intervention | A change predicted to disrupt the mechanism. | Refresh the dependency graph before planning. |

A diagnosis is causally useful when it identifies a mechanism and an intervention target, not merely a taxonomy code.

## 2. Minimum evidence ledger

For each material item record:

| Field | Meaning |
| --- | --- |
| ID and time | Stable reference and temporal position. |
| Observation | What the source directly establishes. |
| Source | Trace, file, diff, test, verifier, environment, report, or external record. |
| Evidence role | Outcome, antecedent, process/mechanism, later corroboration, or uncertain. |
| Reliability | High, medium, low, with one-line reason. |
| Independence | Independent, partially dependent, or duplicate. |
| Hypothesis effect | Supports, weakens, or does not discriminate among named hypotheses. |

Never put an inferred mental state in the observation column. “The agent ignored feedback” is an inference unless the trace shows receipt, interpretation opportunity, and non-response.

## 3. Candidate model record

For each hypothesis specify:

| Field | Required content |
| --- | --- |
| Hypothesis | One falsifiable causal claim. |
| Ontology anchor | L1/L2 node, edge, configuration, or residual. |
| Mechanism chain | Condition -> breakdown -> intermediate trace -> outcome. |
| Predictions | Observations expected if this model is materially correct. |
| Refuters | Evidence that would materially weaken it. |
| Boundary conditions | Versions, task types, environments, or phases where it applies. |
| Support and contradiction | Evidence-ledger IDs, not narrative repetition. |
| Corrective implication | Intervention that follows if the model leads. |

Generate candidates before searching deeply enough to create confirmation bias. Maintain at least one plausible non-model explanation when the system includes a harness, evaluator, tool, or environment.

## 4. Evidence tests

Compare each live model on:

1. **Temporal fit** — required causes precede the outcome and the mechanism steps occur in a feasible order.
2. **Prediction fit** — distinctive predictions appear, not merely observations shared by all models.
3. **Process reality** — the required node or handoff failure is directly observed or strongly traced.
4. **Counterfactual leverage** — controlled replay, ablation, alternative tool/model/prompt, prior successful run, or comparable case changes the outcome as predicted.
5. **Anomaly fit** — the model explains contrary and residual observations rather than hiding them.
6. **Boundary clarity** — the scope in which the mechanism should and should not occur is explicit.
7. **Source independence** — support comes from genuinely distinct observations.

Use strong disconfirmation to outweigh multiple weak confirmations. A model-wide lead does not prove every link in its chain.

## 5. Safe discriminating evidence

Prefer evidence that distinguishes leading rivals:

- inspect the exact instruction state available immediately before the decisive action;
- compare intended versus actual tool arguments and tool-return handling;
- replay a minimal failing step with one factor changed;
- run the narrowest relevant test or verifier check;
- compare pre-run, intermediate, and final repository state;
- inspect whether feedback entered the context and changed the next action;
- compare successful and failed runs with matched task conditions;
- check evaluator sensitivity with a known-good and known-bad artifact;
- verify version-specific behavior from primary documentation or controlled reproduction.

Avoid broad evidence collection that would support every explanation equally. Do not mutate the user’s artifact or production environment during diagnosis unless authorized.

## 6. Ranking vocabulary

Use these bounded statuses:

- **Relatively leading explanation** — strongest in the current candidate set; not uniquely proven.
- **Jointly leading explanations** — current evidence cannot separate two or more leading mechanisms.
- **Complementary or amplifying mechanism** — modifies the effect of another mechanism but does not explain the outcome alone.
- **Unexcluded explanation** — plausible but inadequately tested.
- **Weakened explanation** — materially challenged in its stated scope.
- **Evidence-limited** — access, timing, coverage, or reliability prevents a dependable ranking.

Optionally state high, moderate, or low confidence with explicit reasons. Do not convert an ordinal assessment into numerical probabilities without a calibrated probabilistic model and defensible priors.

## 7. Causal composition

Compare models separately before composing them. Then label relationships among supported mechanisms:

- **primary** — explains the largest consequential portion within scope;
- **jointly necessary** — outcome requires the conjunction;
- **complementary/amplifying** — changes strength or reach;
- **substitutive** — either mechanism can produce a similar outcome;
- **period- or phase-specific** — different mechanisms dominate different segments.

Do not call every upstream condition a root cause. Prefer intervention-relevant causes that are sufficiently proximal to test yet sufficiently upstream to prevent recurrence.

## 8. Adaptive ontology traversal

Expand an existing branch temporarily when a coarse node remains relevant but cannot discriminate actions. This is traversal, not ontology change.

Evaluate ontology insufficiency using two tests:

1. **Coverage test** — can any current node, edge, or configuration express the required mechanism without distorting it?
2. **Resolution test** — does that representation distinguish materially different interventions?

If either fails, classify the smallest adaptation:

| Adaptation | Test | Example form |
| --- | --- | --- |
| Vertical refinement | The parent is correct but intervention-relevant mechanisms remain conflated. | Feedback -> detection, interpretation, actionability, revision opportunity. |
| Horizontal expansion | A causally relevant construct has no defensible parent representation. | Add a version-compatibility or epistemic-trust factor. |
| Relation revision | Nodes exist but the missing or incorrect handoff explains the residual. | Objective priority is not propagated into solution selection. |
| Configuration revision | Individual functions are adequate except under a specific interaction. | Parallelism × ambiguous ownership -> inconsistent integration. |

Before proposing promotion, rerun the candidate comparison with the extension and ask:

- Does it predict evidence not already predicted by existing concepts?
- Does it improve discrimination among corrective actions?
- Does it overlap with or duplicate an existing node?
- Is it general enough for a core ontology, or only case-local?
- What observation would refute the extension?

Core-ontology changes require human review.

## 9. Stopping rule

Estimate the expected value of the next evidence qualitatively:

`value of changed ranking or action × chance the evidence changes it - cost/delay/risk`

Stop when this value is non-positive, when the action is robust across the leading set, when the ontology adaptation question is ready for human review, or when access is blocked. State which condition stopped the diagnosis.

Do not stop merely because one explanation sounds plausible or the first fix worked; a fix may mask the mechanism or affect several rivals at once.
