# Lenses

**Intent:** Provide coverage checklists that prompt questions about the task ontology. A lens is never a required schema, traversal, or attribution code.

## How to apply a lens

Apply a lens to the **task ontology**, not the trace. For each lens function, ask whether some task-ontology type plays that role.

| Lens function | Task-ontology type(s) playing the role | Result |
| --- | --- | --- |

Results: `covered`, `gap-noted` (record a question), or `not applicable` (with a reason). A gap becomes an ontology revision only through the admission rules in [../ontology-induction.md](../ontology-induction.md).

## Available lenses

- [control-loop.md](control-loop.md): generic objective → understanding → solution → execution → monitoring → verification loop. Default for light mode.
- [coding.md](coding.md): repository and software-change specifics, adapted from `diagnose-agentic-coding`.
- [research-browsing.md](research-browsing.md): information seeking, sources, and claims.
- [multi-agent.md](multi-agent.md): delegation, messages, and shared state between agents.

## Promotion

A type proposed for a lens must recur across cases with a stated alignment between case types, and must pass human review. Record the source cases with each promoted entry.
