# Ontology Induction

**Intent:** Derive the task ontology from the task without reading the trace, freeze it, and keep it fixed for the whole case.

The task ontology supplies the vocabulary for one case: which artifact roles, functions, potential Edges, locators, and completion evidence the task requires. It is the analyst's expectation, not ground truth. Its value is that it is fixed before the trace is read and never adapted to the run, so it can reveal errors of omission, resist hindsight, and stay comparable across cases.

## Taxonomy source

[meta-ontology.md](meta-ontology.md) is the only taxonomy. The task ontology supplies only the types the meta-ontology assigns to it: artifact roles and functions, and the potential Edges they type (Layer 2). All other meta-ontology terms are used as defined there.

If a needed concept fits none of these, record it as a **taxonomy gap** with the concept, the derivation source that demands it, and the closest kind considered, and stop for human review: resolving it changes the meta-ontology, which is a method change.

## Inputs to derivation (trace-blind)

Use:

- [meta-ontology.md](meta-ontology.md), as the grammar. It contains no case evidence, so supplying it does not break blinding.
- Task specification, user request, intended outcome, and success conditions.
- The frozen failure target from step 1.
- Environment affordances: available tools, observable state, permissions, and limits.
- Configuration delivered to the agent.
- Domain knowledge and lenses, as prompts for coverage only. A lens may suggest what to type, never what kind a type is.

The derivation excludes the trace, evaluator verdicts, and human postmortems. Knowing the observed deviation from the frozen target is expected; knowing how the run unfolded is exposure. When a subagent is available, derive `O_v0` in a fresh subagent given only the inputs above, which makes the blinding real rather than self-reported. When exposure has already happened, record what was seen and mark the affected types `post-exposure`.

## Derivation procedure

1. **Success conditions.** State what must be true at the end for the intended outcome. Make each condition checkable against an environment-state artifact role.
2. **Backward chaining.** For each condition, identify the artifact roles, including environment-state roles, it depends on, the functions that produce them, and the functions that consume them. Repeat until you reach artifact roles the task supplies.
3. **Functions.** Name a function for each producing or consuming action class. A function is defined by the artifact roles it consumes and produces, not by a fixed workflow position. Record its expected actor kinds and any operating conditions that govern it.
4. **Locators.** For each artifact role, especially environment-state roles, define how a version is grounded in this domain (commit hash, URL plus retrieval time, database snapshot, message ID, conversation turn) and how strong that evidence is.
5. **Completion evidence.** Define the environment-state artifact role, or the trace observation of it, that would justify a completion claim. Keep it distinct from the inherited claim role.
6. **Divergence points.** Mark the functions and potential Edges at which a run could leave the success path, with the failure each admits. A choice the agent can make (for example, whether to ask for clarification) is a function; its alternatives differ in the artifact role produced or the Edge exercised. These marks give later rivals somewhere to attach.
7. **Potential Edges.** Record each producer→consumer dependency as a potential Edge, with any operating condition that governs delivery (truncation limit, permission, routing). They are expectations: an unexercised potential Edge becomes a deviation only with case evidence of causal relevance.
8. **Lens audit.** Apply the relevant lenses ([lenses/README.md](lenses/README.md)) and add any type a gap justifies under the admission rules, using one of the three kinds.

## Type records

Artifact role:

| Field | Content |
| --- | --- |
| ID | Short stable identifier |
| Definition | One sentence |
| Is / Is not | Boundary examples that separate it from neighboring roles |
| Runtime factor | One of the [meta-ontology](meta-ontology.md) runtime factors, or none |
| Locator | How versions are grounded, and the strength of that evidence |
| Expected producers / consumers | Functions |
| Derivation source | The task, configuration, affordance, or lens it was derived from |
| Exposure | `pre-exposure` or `post-exposure` |

Function:

| Field | Content |
| --- | --- |
| ID | Short stable identifier |
| Definition | One sentence |
| Is / Is not | Boundary examples that separate it from neighboring functions |
| Inputs / outputs | Artifact roles consumed and produced |
| Expected actor kinds | From the meta-ontology's Actor kinds |
| Operating conditions | Settings that govern it without entering context, or none |
| Divergence point | No, or the failure it admits |
| Derivation source | The task, configuration, affordance, or lens it was derived from |
| Exposure | `pre-exposure` or `post-exposure` |

Potential Edge:

| ID | Producing function or source | Artifact role | Consuming function | Operating conditions | Divergence point | Derivation source | Exposure |
| --- | --- | --- | --- | --- | --- | --- | --- |

## Admission rules

A type enters the ontology only if all of these hold:

1. **Typed.** It instantiates exactly one kind from the taxonomy source. A concept that fits none is a taxonomy gap, not a type.
2. **Grounded.** It is derived from a cited input to derivation.
3. **Bounded.** It has an is/is-not definition that a second analyst could apply consistently. A potential Edge is bounded by its three components.
4. **Non-redundant.** It passes the merge test: it does not overlap an existing type of the same kind. If it overlaps, refine the existing type instead.
5. **Discriminating.** It separates the success path from at least one plausible way the task could fail. A type that changes no prediction is rejected.

Keep the ontology as small as the task allows.

## Freezing

Freeze the audited ontology as `O_v0` before the trace is read, together with any recorded taxonomy gaps. It stays fixed through annotation, causal comparison, and reporting; actions that do not fit go to the residual log, and returned links that do not fit are recorded as representation gaps. A case-specific type is never added to fit the run. The only route to a different ontology is a restart from step 2 (light-mode escalation), whose types are marked `post-exposure`, or a lens proposal for future cases.

## Expressibility check

The ontology must not decide the causal ranking. On every completed Response:

1. For each returned model, take its mechanism chain (`condition → decision/action → intermediate change → outcome`).
2. Map each link onto the annotated trace: an artifact version, a Node, an Edge, an operating condition on a Node or Edge, or an Interaction over them. A decision maps to the Node of the function marked as its divergence point.
3. A link that maps to no type is a **representation gap**. Render it with its raw trace spans, record it, and keep the model at its returned rank.
4. Record which returned models had gaps; that record is evidence for the representation verdict and for lens proposals. A gap that no task-ontology type of the three kinds could have expressed is a taxonomy gap and goes to human review.

## Agent task model

The agent's own operative view of the task is a belief-state artifact in the annotated trace ([annotated-trace.md](annotated-trace.md)), compared with the frozen ontology. Its elements never become ontology types.
