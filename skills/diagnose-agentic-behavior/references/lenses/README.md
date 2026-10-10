# Lenses

**Intent:** Provide coverage checklists that prompt questions about the task ontology. A lens is a checklist; the task ontology stays the schema. Light mode is the one exception, where the control-loop lens serves as `O_v0`.

## How to apply a lens

Apply a lens to the **task ontology**, not the trace. For each lens function, ask whether some task-ontology type plays that role.

| Lens function | Task-ontology type(s) playing the role | Result |
| --- | --- | --- |

Results: `covered`, `gap-noted` (record a question), or `not applicable` (with a reason). A gap becomes an ontology revision only through the admission rules in [../ontology-induction.md](../ontology-induction.md).

## Available lenses

- [control-loop.md](control-loop.md): generic objective → understanding → solution → execution → monitoring → verification loop. `O_v0` in light mode.
- [coding.md](coding.md): repository and software-change specifics, adapted from `diagnose-agentic-coding`.
- [research-browsing.md](research-browsing.md): information seeking, sources, and claims.
- [multi-agent.md](multi-agent.md): delegation, messages, and shared state between agents.

## Promotion

A diagnosis may propose a case type for a lens. Each proposal states the type's definition and is/is-not boundary, the reason it is not specific to its task, and the source case. Promotion requires human review; record the source cases with each promoted entry.
