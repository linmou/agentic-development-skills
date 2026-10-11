# Meta-Ontology

**Intent:** Define the fixed grammar every case uses, so that task ontologies differ in vocabulary but remain comparable. It contains no domain types; those live in the task ontology ([ontology-induction.md](ontology-induction.md)). Changing this file changes the method, not a case, and requires human review.

## Layer 1: Primitives

| Primitive | Is | Is not |
| --- | --- | --- |
| Actor | An entity that performs actions, identified by ID and kind: model, agent instance, human, harness, tool, evaluator, or external service. | A role or permission; those are artifacts. |
| Action | One concrete event by one actor, classified by a task-ontology function, that consumes artifacts and may produce new artifacts or new artifact versions. | A function (the type it instantiates), or a planned step that never ran. |
| Artifact | A versioned unit of content in a task-ontology role: an instruction, plan, message, tool result, claim, file, verdict, configuration content, or the state of a repository, page, or database. Versions are grounded by a task-ontology locator. | A file or source as such: one source may hold several artifacts, and one artifact may span sources. |

**Operating condition:** a setting that acts without entering any context, such as a truncation limit, permission, or timeout. It is a property of the Node or Edge it governs, not an artifact. Configuration that does enter context (system prompt, skill, project rule, tool definition) is an artifact.

## Layer 2: Node, Edge, and Interaction

Node and Edge are composed of primitives and form a directed graph. An Interaction is a hyperedge over that graph. Node and Edge are typed by the task ontology (function, artifact role); Interaction has no task-ontology type.

| Structure | Composed of | Is | Is not |
| --- | --- | --- | --- |
| Node | `(actor, action)` | One concrete action by one actor, classified by a task-ontology function. | A function without an action instance; the artifacts it consumes or produces, which arrive and leave on Edges. |
| Edge | `(producing Node or source, artifact version, consuming Node)` | The delivery of an artifact version into a consuming Node. Delivery establishes *in context*; only a reference or resulting action establishes *use*. | Use of the artifact, which is evidenced at the consuming Node. A mandatory workflow transition. |
| Interaction | Two or more Nodes and Edges: a hyperedge over the annotated trace | Members whose joint effect on an outcome differs from what each produces alone, such as two conflicting instructions delivered into one Node, or a model tendency that matters only under a harness truncation limit. | A type declared before freezing; Nodes that merely coexist; a sequential chain without evidence of joint dependence. |

Capabilities and operating conditions join an Interaction through the Node or Edge that carries them.

## Runtime factors

Runtime factors add no types; they are distinctions among Layer 1 artifacts that every case keeps.

| Factor | Is | Is not |
| --- | --- | --- |
| Environment state | Artifacts that hold what actually is (a repository, page, database, document, or other agent), at versions grounded by snapshots, hashes, or independent inspection. Changing the environment produces a new version; inspecting it consumes one. | What the trace or the agent says it is; established by partial inspection. |
| Belief state | The agent's representation of the task and the environment, including the agent task model ([annotated-trace.md](annotated-trace.md)): artifacts inferred from cited actions unless the agent recorded them. | Environment state; directly observed, unless the agent recorded it. |
| Trace | The logged sequence of Nodes, carrying two artifact roles every task ontology inherits: **observations** (tool returns, page contents, messages received) and **claims** (the agent's assertions, including completion claims). | Environment state: observations and claims are evidence about it. Complete: logging gaps exist. |

## Evidence status

Each annotated instance (artifact version, Node, or Edge) is:

- **Observed:** directly present in a cited source span.
- **Inferred:** supported by cited evidence but not directly present; state the inference.

Each expected type with no instance is:

- **Absent:** the evidence boundary is complete enough to say it did not occur.
- **Unobserved:** the evidence cannot show whether it occurred (logging gap).
- **Outside boundary:** excluded by the declared scope, with a reason.
