# Meta-Ontology

**Intent:** Define the fixed grammar that every case uses, so that task ontologies differ in vocabulary but remain comparable and auditable.

The meta-ontology contains no domain types. Domain types live in the task ontology ([ontology-induction.md](ontology-induction.md)) and in lenses.

## Primitives

| Primitive | Definition | Required attributes |
| --- | --- | --- |
| Actor | An entity that performs actions: model, agent instance, human, harness, tool, evaluator, or external service. | ID, kind, role in this case |
| Action | A concrete event by an actor that consumes inputs and may produce artifacts or change environment state. | Event ID, actor, time or order, function (task-ontology type), inputs, outputs |
| Artifact | An identifiable unit of meaning in a semantic role: an instruction, plan, claim, message, tool result, file, or verdict. A role, not a file; one source may hold several, and one artifact may span sources. | ID, task-ontology type, version, source span, producer action |
| Data flow | The delivery of an artifact version into a consuming action's context. | Artifact version, route, consumer action, in-context evidence, use evidence |
| Environment state | The actual state of what the agent acts on or reasons about at a grounded version or time: a repository, web page, database, document, or other agent. | Locator type (from the task ontology), version or time, evidence |
| Scaffold configuration | System prompt, skills, project rules, tool definitions and policies, and harness settings that condition actions. Represented as artifacts, operating conditions, or properties of actions and data flows; it is not a separate attribution category. | Provenance, version, temporal validity, in-context and use evidence |

## Environment state, belief state, and trace

These three follow the POMDP reading of an agent: the agent cannot see the environment state directly, acts on its belief state, and leaves a trace. Keep them distinct in every case:

- **Environment state:** what actually is. It is established only by grounded evidence (snapshots, hashes, independent inspection); partial inspection does not establish complete state.
- **Belief state:** the agent's representation of the problem and the environment. It is inferred from cited actions unless explicitly recorded, and is always marked inferred when inferred.
- **Trace:** the logged sequence of actions with their **observations** (tool returns, page contents, messages received) and **claims** (the agent's assertions, including completion claims). Observations and claims are evidence about environment state, not the state itself; a disagreement between a claim and environment state is itself a finding.

## Evidence status

Every artifact, action, data flow, and state version carries one status:

- **Observed:** directly present in a cited source span.
- **Inferred:** supported by cited evidence but not directly present; state the inference.
- **Absent:** expected by the task ontology, and the evidence boundary is complete enough to say it did not occur.
- **Unobserved:** expected, but the evidence cannot show whether it occurred (logging gap).
- **Outside boundary:** excluded by the declared scope, with a reason.

Absent and unobserved are different: a logging gap stays unobserved.

## Structural anchors

Node, Edge, and Interaction, and the three attribution levels, are defined in [diagnostic-definitions.md](diagnostic-definitions.md). They are part of the meta-ontology and do not change between cases.

## Aliases to diagnose-agentic-coding

| This skill | `diagnose-agentic-coding` |
| --- | --- |
| Environment state | System State (SYS) |
| Belief state | State Model (SM) |
| Trace (actions, observations, claims) | Execution Record (ER), plus completion status |
| Data flow | Artifact handoff (Edge) |
| In context / used | Availability / actual use |
| Claim–environment-state disagreement | ER–SYS disagreement, false completion |
| Control-loop lens functions C1–C6 | L1 functions 1–6 |

## Stability

Changes to this file are changes to the method, not to a case. They require human review and must preserve comparability with earlier case records.
