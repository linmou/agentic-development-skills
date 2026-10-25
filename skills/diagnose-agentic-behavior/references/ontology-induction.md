# Ontology Induction

**Intent:** Derive the expected task ontology from the task without reading the trace, and control how it changes during diagnosis.

The task ontology supplies the vocabulary for one case: which artifact roles, functions, state locators, and completion evidence the task requires. It is the analyst's expectation, not ground truth. Its value is that it is fixed before the trace is read, so it can reveal absences and resist hindsight.

## Inputs to derivation (trace-blind)

Use:

- Task specification, user request, intended outcome, and success conditions.
- The frozen failure target from step 1.
- Environment affordances: available tools, observable state, permissions, and limits.
- Configuration delivered to the agent: system prompt, skills, project rules, tool policies.
- Domain knowledge and lenses, as prompts for coverage only.

The derivation excludes the trace, evaluator verdicts, and human postmortems. Knowing the observed deviation from the frozen target is expected; knowing how the run unfolded is exposure. When a subagent is available, derive `O_v0` in a fresh subagent given only the inputs above, which makes the blinding real rather than self-reported. When exposure has already happened, record what was seen and mark types added after it as `post-exposure`.

## Derivation procedure

1. **Success conditions.** State what must be true at the end for the intended outcome. Make each condition checkable against World evidence.
2. **Backward chaining.** For each condition, identify the intermediate artifacts or world-state changes it depends on, who produces them, and who consumes them. Repeat until you reach inputs the task supplies.
3. **Functions.** Name the actions that produce each required artifact. A function is a class of action defined by what it produces and consumes, not by a fixed workflow step.
4. **State locators.** For each world-state entity, define how a version is grounded in this domain (commit hash, URL plus retrieval time, database snapshot, message ID, conversation turn) and how strong that evidence is.
5. **Completion evidence.** Define what evidence would justify a completion claim, separate from the claim itself.
6. **Decision points.** Make explicit the decisions, inputs, and checks where a run could leave the success path. These give later rivals somewhere to attach.
7. **Expected dependencies.** Record potential producer→consumer dependencies. They are expectations: an unexercised potential dependency becomes a deviation only with case evidence of causal relevance.

## Type record

| Field | Content |
| --- | --- |
| ID | Short stable identifier |
| Kind | Artifact role, function, world-state entity, decision point, or completion evidence |
| Definition | One sentence |
| Is / Is not | Boundary examples that separate it from neighboring types |
| Derivation source | The task, configuration, or affordance it was derived from |
| Expected producers / consumers | Functions or actors |
| Locator | For world state: how versions are grounded |
| Exposure | `pre-exposure` or `post-exposure` |

## Admission rules

A type enters the ontology only if all of these hold:

1. **Grounded.** It is derived from a cited input (for `O_v0`) or a cited trace span or returned model (for revisions).
2. **Bounded.** It has an is/is-not definition that a second analyst could apply consistently.
3. **Non-redundant.** It passes the merge test: it does not overlap an existing type. If it overlaps, refine the existing type instead.
4. **Discriminating.** For `O_v0`, it separates the success path from at least one plausible way the task could fail. For a revision, it separates two rival mechanisms or two intervention targets. A type that changes no prediction is rejected.

## Revision rules

Prefer, in order: refine an existing type's identity, version, or boundary; split a type; add a type. Keep the ontology as small as the case allows.

Freeze the derived ontology as `O_v0`. Every later change is a new version with a log entry:

`O_vN → O_vN+1 | change | trigger (residual ID, lens gap, or returned model) | admission evidence | remapped events`

Revisions keep `O_v0` on record. Report which types were pre-exposure and which were added during diagnosis; post-exposure types are legitimate but carry less weight as evidence of what should have happened.

## Expressibility check

The ontology must not decide the causal ranking, and the dependency's contract has no field for reporting vocabulary gaps, so the host runs this check on every completed Response:

1. For each returned model, take its mechanism chain (`condition → decision/action → intermediate change → outcome`).
2. Map each step onto the case graph: an artifact, action, handoff, world-state transition, or decision point.
3. A step that maps to nothing is an **expressibility gap**. Extend the ontology under the admission rules (the returned model satisfies the discrimination test), remap affected events, and submit a new Request with the extended graph.
4. Accept the ranking only when every returned model maps, or its remaining gap is recorded as unresolved with a reason.

Record which returned models forced extensions; that record shows where the lenses fall short.

## Agent task model

The agent's own operative view of the task stays outside the expected ontology. It is recorded in the case graph as a Belief-layer artifact (see [case-graph.md](case-graph.md)) and compared with the expected ontology. Its types enter the expected ontology only by passing the admission rules on their own.
