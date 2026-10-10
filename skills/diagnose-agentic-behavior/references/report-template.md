# Diagnosis Report

**Intent:** Present the frozen task ontology, the evidence-grounded annotated trace, and the dependency's bounded causal comparison.

## Target and evidence boundary

Record the analysis unit, intended outcome and success conditions, observed deviation, attempt/time boundary, evidence cutoff, and intended decision. Summarize inspected sources and material gaps. Label observations, inferences, and unknowns.

## Task ontology

- `O_v0`: types with definitions, is/is-not boundaries, derivation sources, and exposure status, and whether it was derived in a blinded subagent.
- Lens audit: each applied lens and whether it was covered, gap-noted, or not applicable.
- Representation gaps: returned links that mapped to no type, with their raw spans.

## Annotated trace

Show the material path:

`input artifacts → (actor, action, function) → output artifacts → (consumer, action, function)`

Include artifact and environment-state versions with locators, times, in-context versus use evidence, and claim–environment-state disagreements. Include expected-type coverage with each evidence status. Include the residual log with every disposition. Include the agent task model if built, marked inferred.

## Returned causal comparison

Record dependency status and preserve its comparison, citations, limitations, and errors.

| Returned hypothesis/status | Annotated-trace path | Supporting evidence | Contrary evidence / missing links | Discriminating prediction |
| --- | --- | --- | --- | --- |

## Attribution

For each leading or unresolved explanation:

- **Location (Level 1):** Node, Edge, Interaction, or error of omission, with the concrete artifact, action, or environment-state transition.
- **Root mechanism (Level 2):** upstream source, producing action, capability, policy, or external condition, with path and evidence.
- **Causal status:** supported mechanisms, unresolved causes, unexcluded rivals, and gaps.
- **Generalization (Level 3):** recurrence conditions in task-independent terms with the case types mapped to them, scope limits, and evidence needed before generalizing.
- **Intervention:** target, distinguished from causal origin, with expected mechanism change and a testable prediction.
- **Stopping rationale:** why tracing stopped, and the next observation that would most change the diagnosis.

If no candidate is sufficiently supported, state **root cause undetermined** and give the next discriminating observation.

## Representation and lens proposals

State whether `O_v0` expressed the mechanism and distinguished the intervention, citing representation gaps and residuals. List each proposed lens type with its definition, the reason it is not specific to this task, and the source case, or state "none". Promotion requires human review.

## Saved and concise reports

A saved diagnosis includes the exact Request, Response, `O_v0`, the annotated trace, the residual log, and source references, with host annotations kept distinct from the returned comparison.

A concise report still includes the target, `O_v0`, the material annotated-trace path, the returned ruling with rivals, evidence gaps, and the next discriminating evidence.
