# Lenses

**Intent:** Provide coverage checklists, grounded in published agent-failure taxonomies where one exists, that prompt questions about the task ontology before it is frozen. A lens is a checklist; the task ontology stays the schema. Light mode is the one exception, where the control-loop lens serves as `O_v0`.

## How to apply a lens

Apply a lens to the **task ontology**, not the trace, during step 2 before freezing. For each lens entry, ask whether some task-ontology type plays that role or lets that failure mode be expressed.

| Lens entry | Task-ontology type(s) playing the role | Result |
| --- | --- | --- |

Results: `covered`, `gap-noted` (record a question), or `not applicable` (with a reason). A gap adds a type only through the admission rules in [../ontology-induction.md](../ontology-induction.md), and only before freezing.

## Available lenses

- [control-loop.md](control-loop.md): generic objective → understanding → solution → execution → monitoring → verification loop, cross-referenced to AgentErrorTaxonomy modules and TRAIL categories. `O_v0` in light mode.
- [multi-agent.md](multi-agent.md): the MAST failure modes for multi-agent systems.
- [coding.md](coding.md): repository and software-change specifics, adapted from `diagnose-agentic-coding`.
- [research-browsing.md](research-browsing.md): information seeking, sources, and claims.

## Sources

- AgentErrorTaxonomy (AgentDebug): Zhu et al., "Where LLM Agents Fail and How They Can Learn From Failures," arXiv:2509.25370.
- MAST: Cemri et al., "Why Do Multi-Agent LLM Systems Fail?," arXiv:2503.13657.
- TRAIL: Patronus AI, "TRAIL: Trace Reasoning and Agentic Issue Localization," arXiv:2505.08638.

## Promotion

A diagnosis may propose a type for a lens. Each proposal states the type's definition and is/is-not boundary, the reason it is not specific to its task, and the source case. Promotion requires human review; record the source cases with each promoted entry. A promoted type affects future cases only; frozen case ontologies are not revised.
