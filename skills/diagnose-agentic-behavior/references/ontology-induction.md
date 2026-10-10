# Ontology Induction

**Intent:** Derive the task ontology from the task without reading the trace, freeze it, and keep it fixed for the whole case.

The task ontology supplies the vocabulary for one case: which artifact roles, functions, environment-state locators, and completion evidence the task requires. It is the analyst's expectation, not ground truth. Its value is that it is fixed before the trace is read and never adapted to the run, so it can reveal errors of omission, resist hindsight, and stay comparable across cases.

## Inputs to derivation (trace-blind)

Use:

- Task specification, user request, intended outcome, and success conditions.
- The frozen failure target from step 1.
- Environment affordances: available tools, observable state, permissions, and limits.
- Scaffold configuration delivered to the agent.
- Domain knowledge and lenses, as prompts for coverage only.

The derivation excludes the trace, evaluator verdicts, and human postmortems. Knowing the observed deviation from the frozen target is expected; knowing how the run unfolded is exposure. When a subagent is available, derive `O_v0` in a fresh subagent given only the inputs above, which makes the blinding real rather than self-reported. When exposure has already happened, record what was seen and mark the affected types `post-exposure`.

## Derivation procedure

1. **Success conditions.** State what must be true at the end for the intended outcome. Make each condition checkable against environment-state evidence.
2. **Backward chaining.** For each condition, identify the intermediate artifacts or environment-state changes it depends on, who produces them, and who consumes them. Repeat until you reach inputs the task supplies.
3. **Functions.** Name the actions that produce each required artifact. A function is a class of action defined by what it produces and consumes, not by a fixed workflow position.
4. **Environment-state locators.** For each environment-state entity, define how a version is grounded in this domain (commit hash, URL plus retrieval time, database snapshot, message ID, conversation turn) and how strong that evidence is.
5. **Completion evidence.** Define what evidence would justify a completion claim, separate from the claim itself.
6. **Decision points.** Make explicit the decisions, inputs, and checks where a run could leave the success path. These give later rivals somewhere to attach.
7. **Expected dependencies.** Record potential producer→consumer data flows. They are expectations: an unexercised potential dependency becomes a deviation only with case evidence of causal relevance.
8. **Lens audit.** Apply the relevant lenses ([lenses/README.md](lenses/README.md)) and add any type a gap justifies under the admission rules.

## Type record

| Field | Content |
| --- | --- |
| ID | Short stable identifier |
| Kind | Artifact role, function, environment-state entity, decision point, or completion evidence |
| Definition | One sentence |
| Is / Is not | Boundary examples that separate it from neighboring types |
| Derivation source | The task, configuration, affordance, or lens it was derived from |
| Expected producers / consumers | Functions or actors |
| Locator | For environment state: how versions are grounded |
| Exposure | `pre-exposure` or `post-exposure` |

## Admission rules

A type enters the ontology only if all of these hold:

1. **Grounded.** It is derived from a cited input to derivation.
2. **Bounded.** It has an is/is-not definition that a second analyst could apply consistently.
3. **Non-redundant.** It passes the merge test: it does not overlap an existing type. If it overlaps, refine the existing type instead.
4. **Discriminating.** It separates the success path from at least one plausible way the task could fail. A type that changes no prediction is rejected.

Keep the ontology as small as the task allows.

## Freezing

Freeze the audited ontology as `O_v0` before the trace is read. It stays fixed through annotation, causal comparison, and reporting; actions that do not fit go to the residual log, and returned links that do not fit are recorded as representation gaps. A case-specific type is never added to fit the run. The only route to a different ontology is a restart from step 2 (light-mode escalation), whose types are marked `post-exposure`, or a lens proposal for future cases.

## Expressibility check

The ontology must not decide the causal ranking. On every completed Response:

1. For each returned model, take its mechanism chain (`condition → decision/action → intermediate change → outcome`).
2. Map each link onto the annotated trace: an artifact, action, data flow, environment-state transition, or decision point.
3. A link that maps to no type is a **representation gap**. Render it with its raw trace spans, record it, and keep the model at its returned rank.
4. Record which returned models had gaps; that record is evidence for the representation verdict and for lens proposals.
