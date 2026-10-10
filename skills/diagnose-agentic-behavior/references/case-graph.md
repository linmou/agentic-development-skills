# Case Graph

**Intent:** Map trace evidence onto the task ontology, record what does not fit, and keep World, Belief, and Record separate.

The case graph is the single schema for a case: trace spans annotated as instances of task-ontology types. There is no second, trace-derived ontology. The trace is evidence; the case graph is an annotation of that evidence.

## General form

`input artifacts → (actor, action, function) → output artifacts → (consumer, action, function)`

with world-state transitions `W_t → (actor, action) → Record + W_{t+1}` wherever the resulting state can be grounded. If `W_{t+1}` is unknown, keep the gap; do not substitute a tool success message or completion claim.

## Mapping procedure

1. Scan the trace in time order. Assign event IDs; repeated actions get distinct IDs.
2. For each material event, identify the actor, the action, its function (a task-ontology type), the input bundle available at that time, and its outputs.
3. Assign each output an artifact ID and version. A later version cannot establish what was available earlier.
4. For each handoff, record availability evidence (delivered into context, file present, message sent) separately from use evidence (explicit reference, argument, resulting action).
5. Ground world-state versions with the locators defined in the task ontology.
6. After the scan, walk the task ontology and mark every expected type observed, inferred, absent, unobserved, or outside boundary (see [meta-ontology.md](meta-ontology.md)). This is how absences are found; scanning alone cannot see them.
7. Do not stop at the first salient anomaly. Complete the mapping before nominating candidate deviations.

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

A residual is a material event or span that does not map cleanly onto the current ontology. Record:

| Residual ID | Span | Why it does not fit (no type, ambiguous between types, crosses a type boundary) | Candidate disposition | Outcome |
| --- | --- | --- | --- | --- |

Dispositions: refine an existing type, add a type (under the admission rules in [ontology-induction.md](ontology-induction.md)), carry as an explicit gap, or reject as immaterial with a reason. Residuals are the only trace-driven trigger for ontology revision. Every residual reaches a disposition before the report.

## Candidate deviations

After mapping, list candidate deviations as unranked leads for the causal dependency:

| Candidate | Distinguishing evidence | Intervention target if supported |
| --- | --- | --- |
| Inadequate input | Input content at action time compared with the task requirement or World | Upstream production or refresh |
| Incorrect transformation | Adequate available inputs, incorrect output | Producing action |
| Failed handoff | Correct output exists; delivery, truncation, routing, or access evidence | Transfer to the consumer |
| Incorrect consumption | Correct version available; use contradicts it | Consuming action |
| Stale version consumed | Version and timing evidence | Version selection or synchronization |
| Absence | Expected type marked absent with complete-enough evidence | Whatever should have produced it |
| Record–World disagreement | Claim or tool return contradicted by World evidence | Verification or reporting action |
| Task-model divergence | Agent task model differs from expected ontology in a way that predicts X over Y | Objective delivery, instruction, or model behavior |
| Interaction | Multiple conditions jointly change a transformation or handoff | The supported combination |

These are leads. The dependency decides which the evidence supports.

## Agent task model (optional)

Build only when a rival hypothesis depends on what the agent took the task to be. Record:

| Element | Inferred content | Supporting spans | Contrary spans | Expected-ontology counterpart | Divergence |
| --- | --- | --- | --- | --- | --- |

Elements typically include the operative goal, deliverables, constraints honored, and completion criterion. Every element is marked inferred and cites behavior. A divergence predicts X over Y only if the comparison says why; record that prediction for the dependency.

## Configuration

Treat instructions, skills, prompts, policies, and harness settings as versioned input artifacts. Presence does not prove delivery; delivery does not prove use; intended settings do not prove effective conditions.

| Configuration mechanism | Anchor | Required trace |
| --- | --- | --- |
| Defective instruction or rule | Node | Authoring action → artifact → faithful consuming action |
| Correct artifact delivered stale, truncated, or misrouted | Edge | Artifact version → delivery action → consumer |
| Individually acceptable constraints incompatible together | Interaction | Contributing artifacts → combined mechanism → changed action |
