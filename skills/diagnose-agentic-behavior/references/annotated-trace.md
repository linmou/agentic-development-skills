# Annotated Trace

**Intent:** Annotate trace evidence against the frozen task ontology, record what does not fit, and nominate candidate deviations.

The annotated trace is the single schema for a case: trace spans labeled as instances of task-ontology types, linked into a produce/consume graph. Primitives, environment state, belief state, trace, and evidence statuses are defined in [meta-ontology.md](meta-ontology.md).

## General form

`input artifacts → (actor, action, function) → output artifacts → (consumer, action, function)`

with environment-state transitions `S_t → (actor, action) → observation + S_{t+1}` wherever the resulting state can be grounded. When `S_{t+1}` is unknown, record the gap and leave the transition open.

## Annotation procedure

1. Scan the trace in time order. Assign event IDs; repeated actions get distinct IDs.
2. For each material action, identify the actor, the action, its function (a task-ontology type), the inputs in context at that time, and its outputs.
3. Assign each output an artifact ID and version. Establish what was in context at a time only from versions that existed then.
4. For each data flow, record **in-context** evidence (delivered into the consumer's context, file present, message sent) and **use** evidence (explicit reference, argument, resulting action) as separate fields. Delivery establishes in context; only references or resulting actions establish use. Logging gaps leave either uncertain.
5. Ground environment-state versions with the locators defined in the task ontology.
6. After the scan, walk the task ontology and assign every expected type an evidence status. This is how errors of omission are found.
7. Complete the annotation before nominating candidate deviations, so coverage extends past the first salient anomaly.

## Records

Artifact and state record:

| Artifact or state ID/version | Type | Concrete content (span) | Source locator | Time | Producer action, or state transition | Status |
| --- | --- | --- | --- | --- | --- | --- |

Data-flow record:

| Input ID/version | Consumer action, function, time | Expected use | In-context evidence | Use evidence | Output ID/version | Deviation or gap |
| --- | --- | --- | --- | --- | --- | --- |

Expected-type coverage:

| Type | Status | Instances or reason |
| --- | --- | --- |

## Residual log

A residual is a material action or span that does not map cleanly onto the frozen ontology. The ontology does not change in response; residuals are evidence.

| Residual ID | Span | Why it does not fit (no type, ambiguous between types, crosses a type boundary) | Disposition |
| --- | --- | --- | --- |

Dispositions: **carried** (passed to the dependency as raw evidence and kept as an explicit gap) or **immaterial** (with a reason). Residuals also inform the representation verdict and lens proposals in step 6.

## Candidate deviations

After annotation, list candidate deviations as unranked leads for the causal dependency:

| Candidate | Distinguishing evidence | Intervention target if supported |
| --- | --- | --- |
| Bad input | Input content at action time compared with the task requirement or environment state | Upstream production or refresh |
| Error of commission | Adequate inputs in context, incorrect reasoning or execution, incorrect output | Producing action |
| Error of omission | Expected type with status `absent` | Whatever should have produced it |
| Context delivery failure | Correct output exists; delivery, truncation, routing, or access evidence | Data flow into the consumer |
| Context misuse | Correct version in context; use ignores or contradicts it | Consuming action |
| Stale context | Version and timing evidence show an outdated version was used | Version selection or synchronization |
| Task-model divergence | Agent task model differs from the task ontology in a way the record links to the observed deviation | Objective delivery, instruction, or model behavior |
| False success claim | A claim, tool return, or completion claim contradicted by environment-state evidence | Verification or reporting action |
| Interaction effect | Multiple conditions jointly change an action or data flow | The supported combination |

The dependency decides which the evidence supports.

## Agent task model

The agent task model is the belief-state artifact describing what the agent appears to have treated as the task. Build it in step 3 when a task-model divergence is among the candidate deviations, or in step 5 when a returned model depends on it.

| Element | Inferred content | Supporting spans | Contrary spans | Task-ontology counterpart | Divergence |
| --- | --- | --- | --- | --- | --- |

Elements typically include the operative goal, deliverables, constraints honored, and completion criterion. Every element is marked inferred and cites actions. A divergence counts as a candidate only when the record states how it leads to the observed deviation. The agent task model is compared with the frozen task ontology and stays outside it.

## Scaffold configuration

Scaffold configuration is represented as defined in [meta-ontology.md](meta-ontology.md). Record its delivery and use through annotation step 4. Infer effective runtime conditions from evidence; intended settings alone establish only intent.

| Configuration mechanism | Anchor | Required trace |
| --- | --- | --- |
| Defective instruction or rule | Node | Authoring action → artifact → faithful consuming action |
| Correct artifact delivered stale, truncated, or misrouted | Edge | Artifact version → delivery action → consumer |
| Individually acceptable constraints incompatible together | Interaction | Contributing artifacts → combined mechanism → changed action |
