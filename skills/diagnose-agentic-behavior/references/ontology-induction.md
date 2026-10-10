# Ontology Induction

**Intent:** Derive the expected task ontology from the task, before the outcome is known, and control how it changes during diagnosis.

The task ontology supplies the vocabulary for one case: which artifact roles, functions, state locators, and completion evidence the task requires. It is the analyst's expectation, not ground truth. Its value is that it is fixed before outcome exposure, so it can reveal absences and resist hindsight.

## Inputs to derivation

Use only sources that existed before or independently of the run's outcome:

- Task specification, user request, and success conditions.
- Environment affordances: available tools, observable state, permissions, and limits.
- Configuration delivered to the agent: system prompt, skills, project rules, tool policies.
- The frozen foil Y from step 1.
- Domain knowledge and lenses, as prompts for coverage only.

Do not use the trace, the outcome, evaluator verdicts, or human postmortems. If any were seen before derivation, record what was seen and mark types added after exposure as `post-exposure`.

## Derivation procedure

1. **Success conditions.** State what must be true at the end for the task to succeed (or, for a success or surprise diagnosis, what must be true for Y). Make each condition checkable against World evidence.
2. **Backward chaining.** For each condition, ask what intermediate artifacts or world-state changes must exist for it to hold, who must produce them, and who must consume them. Repeat until you reach inputs the task supplies.
3. **Functions.** Name the actions that produce each required artifact. A function is a class of action defined by what it produces and consumes, not by a fixed workflow step.
4. **State locators.** For each world-state entity, define how a version is grounded in this domain (commit hash, URL plus retrieval time, database snapshot, message ID, conversation turn) and how strong that evidence is.
5. **Completion evidence.** Define what evidence would justify a completion claim, separate from the claim itself.
6. **Foil-relevant types.** Ensure the ontology can express the decision points where the paths to X and Y could diverge. The foil often demands a type a generic loop would not supply (for example, an escalation option when Y is "asked the user").
7. **Expected dependencies.** Record potential producer→consumer dependencies. These are expectations, not obligations: an unused potential dependency is not a failure without case evidence of causal relevance.

## Type record

Record each type as:

| Field | Content |
| --- | --- |
| ID | Short stable identifier |
| Kind | Artifact role, function, world-state entity, or completion evidence |
| Definition | One sentence |
| Is / Is not | Boundary examples that separate it from neighboring types |
| Derivation source | The task, configuration, or affordance it was derived from |
| Expected producers / consumers | Functions or actors |
| Locator | For world state: how versions are grounded |
| Exposure | `pre-exposure` or `post-exposure` |

## Admission rules

A type enters the ontology only if all of these hold:

1. **Grounded.** It is derived from a cited input (for `O_v0`) or a cited trace span or rival hypothesis (for revisions).
2. **Bounded.** It has an is/is-not definition that a second analyst could apply consistently.
3. **Non-redundant.** It passes the merge test: it does not overlap an existing type. If it overlaps, refine the existing type instead.
4. **Discriminating.** It separates at least two rival mechanisms or two intervention targets. A type that changes no prediction is decoration and is rejected.

Prefer, in order: refine an existing type's identity, version, or boundary; split a type; add a type. Keep the ontology as small as the case allows.

## Versioning

Freeze the derived ontology as `O_v0`. Every later change is a new version with a log entry:

`O_vN → O_vN+1 | change | trigger (residual ID, lens gap, or rival needing expression) | admission evidence | remapped events`

A revision never deletes the record of `O_v0`. Report which types were pre-exposure and which were added during diagnosis; post-exposure types are legitimate but carry less weight as evidence of what should have happened.

## Expressibility symmetry

The ontology must not decide the causal ranking. If the causal-research dependency reports that a rival cannot be stated in the current vocabulary, extend the ontology under the admission rules (the discrimination test is satisfied by that rival) and resubmit. Record which rivals forced extensions; that record is evidence about where the generic lenses fall short.

## Agent task model

The agent's own operative view of the task is not part of the expected ontology. When a rival needs it, record it in the case graph as a Belief-layer artifact (see [case-graph.md](case-graph.md)) and compare it to the expected ontology. Do not import its types into the expected ontology merely because the agent used them.
