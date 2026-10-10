# Diagnosis Report

**Intent:** Present the induced ontology, the evidence-grounded case graph, and the dependency's bounded causal comparison.

## Target and evidence boundary

Record the analysis unit, behavior X, foil Y, success conditions (if any), attempt/time boundary, evidence cutoff, and intended decision. Summarize inspected sources and material gaps. Label observations, inferences, and unknowns.

## Task ontology

- `O_v0`: types with definitions, is/is-not boundaries, derivation sources, and exposure status (`pre-exposure` or `post-exposure`).
- Revision log: each `O_vN → O_vN+1` with its trigger and admission evidence.
- Rivals that forced extensions.
- Lens audit: each applied lens and whether it was covered, gap-noted, or not applicable.

## Case graph

Show the material path:

`input artifacts → (actor, action, function) → output artifacts → (consumer, action, function)`

Include artifact and world-state versions with locators, times, availability versus use evidence, and Record–World disagreements. Include expected-type coverage with absences and unobserved types kept distinct. Include the residual log with every disposition. Include the agent task model if built, marked inferred.

## Returned causal comparison

Record dependency status and preserve its comparison, citations, limitations, and errors.

| Returned hypothesis/status | Case-graph path | Supporting evidence | Contrary evidence / missing links | Discriminating prediction |
| --- | --- | --- | --- | --- |

## Attribution

For each leading or unresolved explanation:

- **Location (Level 1):** Node, Edge, Interaction, or absence, with the concrete artifact, action, or world-state transition.
- **Root mechanism (Level 2):** upstream source, producing action, capability, policy, or external condition, with path and evidence.
- **Causal status:** supported mechanisms, unresolved causes, unexcluded rivals, and gaps.
- **Generalization (Level 3):** recurrence conditions in recurring types with stated alignment, scope limits, and evidence needed before generalizing.
- **Intervention:** target, distinguished from causal origin, with expected mechanism change and a testable prediction.
- **Stopping rationale:** why tracing stopped, and the next observation that would most change the diagnosis.

If no candidate is sufficiently supported, state **root cause undetermined** and give the next discriminating observation.

## Representation and registration

State whether the final ontology expresses the mechanism and distinguishes the intervention. List types proposed for lens promotion, with recurrence evidence; promotion requires human review.

## Saved and concise reports

A saved diagnosis includes the exact Request, Response, all ontology versions, the case graph, the residual log, and source references, with host annotations kept distinct from the returned comparison.

A concise report still includes the target and foil, `O_v0` and revisions, the material case-graph path, the returned ruling with rivals, evidence gaps, and the next discriminating evidence.
