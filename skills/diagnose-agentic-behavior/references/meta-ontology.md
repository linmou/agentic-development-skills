# Meta-Ontology

**Intent:** Define the fixed grammar that every case uses, so that task ontologies differ in vocabulary but remain comparable and auditable.

The meta-ontology contains no domain types. Domain types live in the task ontology ([ontology-induction.md](ontology-induction.md)) and in optional lenses.

## Primitives

| Primitive | Definition | Required attributes |
| --- | --- | --- |
| Actor | An entity that performs actions: model, agent instance, human, harness, tool, evaluator, or external service. | ID, kind, role in this case |
| Action | A concrete event by an actor that consumes inputs and may produce artifacts or change world state. | Event ID, actor, time or order, function (task-ontology type), inputs, outputs |
| Artifact | An identifiable unit of meaning in a semantic role: an instruction, plan, claim, message, tool result, file, record, or verdict. A role, not a file; one source may hold several, and one artifact may span sources. | ID, task-ontology type, version, source span, producer action |
| Handoff | The provision of an artifact version to a consuming action. | Artifact version, route, consumer action, availability evidence, use evidence |
| World state | The actual state of what the agent acts on or reasons about at a grounded version or time: a repository, web page, database, environment, document, or other agent. | Locator type (from the task ontology), version or time, evidence |
| Configuration | Instructions, skills, prompts, policies, and harness settings that condition actions. Represented as artifacts or operating conditions, not as a separate blame category. | Provenance, version, temporal validity, delivery and use evidence |

## Three layers

Keep these layers separate in every case:

- **World:** what actually is. Inspections, tests, and observations are evidence about World, not World itself; partial inspection does not establish complete state.
- **Belief:** the agent's representation of the problem, the world, and the task. Inferred from cited behavior unless explicitly recorded, and always marked inferred when inferred.
- **Record:** what was logged, reported, or claimed (tool returns, transcripts, completion claims). A record is not proof of world state; disagreement between Record and World is itself a finding.

For the task itself, the same split applies: the expected task ontology is the analyst's model of what the task requires; the **agent task model** is a Belief-layer artifact describing what the agent appears to have treated as the task.

## Evidence status

Every artifact, action, handoff, and state version carries one status:

- **Observed:** directly present in a cited source span.
- **Inferred:** supported by cited evidence but not directly present; state the inference.
- **Absent:** expected by the task ontology, and the evidence boundary is complete enough to say it did not occur.
- **Unobserved:** expected, but the evidence cannot show whether it occurred (logging gap).
- **Outside boundary:** excluded by the declared scope, with a reason.

Absent and unobserved are different. Do not convert a logging gap into an absence.

## Structural anchors

Node, Edge, and Interaction, and the three attribution levels, are defined in [diagnostic-definitions.md](diagnostic-definitions.md). They are part of the meta-ontology and do not change between cases.

## Stability

Changes to this file are changes to the method, not to a case. They require human review and must preserve comparability with earlier case records.
