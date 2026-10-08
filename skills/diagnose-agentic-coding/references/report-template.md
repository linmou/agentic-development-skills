# Artifact-Grounded Diagnosis Report

**Intent:** Present an evidence-grounded artifact attribution and the dependency's bounded causal comparison.

## Target and evidence boundary

Record the analysis unit, intended outcome and constraints, observed deviation, attempt/time boundary, cutoff, and intended decision. State the development method and source, or mark it unknown.

Summarize inspected sources and material gaps. Label observations, inferences, and unknowns.

## Functional and artifact views

Show the relevant L1 functions and the case graph:

`input artifacts → (actor, action) → output artifacts → (consumer, action)`

Use the artifact and consumption records in [artifact-flow.md](artifact-flow.md). Include concrete SYS locators and versions, artifact versions, times, and availability versus actual-use evidence. Keep SYS, SM, and ER distinct; report inspection/test results as evidence about SYS. Record applicability for each material method-dependent edge and the reason. Account for all six functions, including unobserved or out-of-boundary ones.

## Returned causal comparison

Record dependency status and preserve its comparison, citations, limitations, and errors. Use its evidence ledger for source links.

| Returned hypothesis/status | L1 actions, artifact path, and SYS transition | Supporting evidence | Contrary evidence / missing links | Discriminating prediction |
| --- | --- | --- | --- | --- |

If the returned analysis lacks a material link, resubmit that gap to the dependency before extending the causal ruling.

## Rootness, provenance, and transferability

For each leading or unresolved explanation, record:

- **Failure location:** Node, Edge, or Interaction and the concrete artifact/action or SYS transition.
- **Causal provenance:** upstream source, producing action, capability, policy, or external condition, with the path and evidence.
- **Causal status:** supported mechanism(s), plausible but unresolved causes, unexcluded rivals, and evidence gaps.
- **Transferability:** recurrence conditions, case scope limits, and evidence needed before generalizing beyond the case.
- **Intervention:** candidate corrective target, distinguished from causal origin, and a testable prediction.
- **Stopping rationale:** why causal tracing stopped at the declared boundary and which next observation would most change the diagnosis.

If no candidate explanation is sufficiently supported, state **root cause undetermined** and preserve the next discriminating observation. Do not infer a unique actor-level root from a localized artifact or from an execution record alone.

## Attribution and corrective implication

For each leading mechanism, identify the input, producing actor/action, output artifact/version, relevant SYS_t → SYS_{t+1} transition, consuming actor/action, supported deviation, and outcome path. Distinguish production, delivery, consumption, or interaction attribution according to the returned evidence. If ER and SYS disagree, state that disagreement explicitly.

State the intervention target, expected mechanism change, and evidence that would test it. Preserve uncertainty about responsibility where the records cannot locate the failure. Remediation is a separate authorized task.

## Representation sufficiency and next evidence

State whether L1 plus artifact flow covers the mechanism and distinguishes the intervention. Describe any proposed case-local extension, its incremental value, overlap, and dependency reassessment. Core promotion requires human review.

Preserve the dependency's stop reason, residuals, and next discriminating evidence. If needed, obtain those through a follow-up Request.

## Saved and concise reports

When saving a diagnosis, include the exact Request, Response, case graph, and source references alongside the report. Distinguish host annotations from the returned causal comparison.

A concise report still includes the target, development-method applicability, concrete artifact path, returned rival comparison and ruling, evidence gaps, and next discriminating evidence.
