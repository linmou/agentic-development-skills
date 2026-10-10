# Case Graph

**Intent:** Map trace evidence onto the task ontology, record what does not fit, and nominate candidate deviations.

The case graph is the single schema for a case: trace spans annotated as instances of task-ontology types. The trace is evidence; the case graph is an annotation of that evidence. Primitives, layers, and evidence statuses are defined in [meta-ontology.md](meta-ontology.md).

## General form

`input artifacts → (actor, action, function) → output artifacts → (consumer, action, function)`

with world-state transitions `W_t → (actor, action) → Record + W_{t+1}` wherever the resulting state can be grounded. When `W_{t+1}` is unknown, record the gap and leave the transition open.

## Mapping procedure

1. Scan the trace in time order. Assign event IDs; repeated actions get distinct IDs.
2. For each material event, identify the actor, the action, its function (a task-ontology type), the input bundle available at that time, and its outputs.
3. Assign each output an artifact ID and version. Establish what was available at a time only from versions that existed then.
4. For each handoff, record **availability** evidence (delivered into context, file present, message sent) and **use** evidence (explicit reference, argument, resulting action) as separate fields. Availability is established by delivery; use only by references or resulting actions. Logging gaps leave either uncertain.
5. Ground world-state versions with the locators defined in the task ontology.
6. After the scan, walk the task ontology and assign every expected type an evidence status. This is how absences are found.
7. Complete the mapping before nominating candidate deviations, so coverage extends past the first salient anomaly.

## Records

Artifact and state record:

| Artifact or state ID/version | Type | Concrete content (span) | Source locator | Time | Producer action, or state transition | Status |
| --- | --- | --- | --- | --- | --- | --- |

Consumption record:

| Input ID/version | Consumer action, function, time | Expected use | Availability evidence | Use evidence | Output ID/version | Deviation or gap |
| --- | --- | --- | --- | --- | --- | --- |

Expected-type coverage:

| Type | Status | Instances or reason |
| --- | --- | --- |

## Residual log

A residual is a material event or span that does not map cleanly onto the current ontology.

| Residual ID | Span | Why it does not fit (no type, ambiguous between types, crosses a type boundary) | Candidate disposition | Outcome |
| --- | --- | --- | --- | --- |

Dispositions: refine an existing type, add a type (under the admission rules in [ontology-induction.md](ontology-induction.md)), carry as an explicit gap, or reject as immaterial with a reason. Residuals are the only trace-driven trigger for ontology revision.

## Candidate deviations

After mapping, list candidate deviations as unranked leads for the causal dependency:

| Candidate | Distinguishing evidence | Intervention target if supported |
| --- | --- | --- |
| Inadequate input | Input content at action time compared with the task requirement or World | Upstream production or refresh |
| Incorrect transformation | Adequate available inputs, incorrect output | Producing action |
| Failed handoff | Correct output exists; delivery, truncation, routing, or access evidence | Transfer to the consumer |
| Incorrect consumption | Correct version available; use contradicts it | Consuming action |
| Stale version consumed | Version and timing evidence | Version selection or synchronization |
| Absence | Expected type with status `absent` | Whatever should have produced it |
| Record–World disagreement | Claim or tool return contradicted by World evidence | Verification or reporting action |
| Task-model divergence | Agent task model differs from the expected ontology in a way linked to the observed deviation | Objective delivery, instruction, or model behavior |
| Interaction | Multiple conditions jointly change a transformation or handoff | The supported combination |

The dependency decides which the evidence supports.

## Agent task model

Build it in step 5 when a task-model divergence is among the candidate deviations, or in step 7 when a returned model depends on it. Record:

| Element | Inferred content | Supporting spans | Contrary spans | Expected-ontology counterpart | Divergence |
| --- | --- | --- | --- | --- | --- |

Elements typically include the operative goal, deliverables, constraints honored, and completion criterion. Every element is marked inferred and cites behavior. A divergence counts as a candidate only when the record states how it leads to the observed deviation.

## Configuration

Configuration is represented as defined in [meta-ontology.md](meta-ontology.md). Record its delivery and use through mapping step 4. Infer effective runtime conditions from evidence; intended settings alone establish only intent.

| Configuration mechanism | Anchor | Required trace |
| --- | --- | --- |
| Defective instruction or rule | Node | Authoring action → artifact → faithful consuming action |
| Correct artifact delivered stale, truncated, or misrouted | Edge | Artifact version → delivery action → consumer |
| Individually acceptable constraints incompatible together | Interaction | Contributing artifacts → combined mechanism → changed action |
