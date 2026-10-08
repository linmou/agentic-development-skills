---
name: diagnose-agentic-coding
description: Diagnose agentic coding failures, degraded trajectories, and false completion using L1 functional and artifact produce-consumption graphs, with competing-explanations-causal-research for causal comparison. Use for agent trace analysis, coding-agent postmortems, model-versus-harness attribution, coordination failures, and ontology sufficiency review.
---

# Diagnose Agentic Coding

Explain an agentic coding outcome well enough to locate a supported artifact-level mechanism and choose a corrective intervention. The diagnostic unit is the joint system of actors, tools, environment, task, and evaluator.

## Required references and dependency

Read [functional-ontology.md](references/functional-ontology.md) and [artifact-flow.md](references/artifact-flow.md) to reconstruct the two graph views. The artifact graph decomposes the L1 functional graph as `input artifacts → (actor, action) → output artifacts → (consumer, action)`. L1 functions classify actions; use IDs 1–6 for diagnosis. L2 descriptions are illustrative background.

Read [report-template.md](references/report-template.md) for reporting.

Every causal diagnosis invokes `competing-explanations-causal-research`, including cases supported entirely by local traces. Load its [SKILL.md](../competing-explanations-causal-research/SKILL.md) and callee-owned [version 1 contract](../competing-explanations-causal-research/references/call-contract.md). The dependency owns evidence assessment, rival-model construction, symmetric testing, ranking, causal statuses, and stopping. This host owns artifact reconstruction, L1 mapping, and presentation of the returned attribution.

If the dependency cannot be found or loaded, report the missing dependency and retain the descriptive graph with its unknowns. A causal ruling requires the dependency.

## Inputs

Obtain or infer the task, intended outcome, success conditions, action boundary, observed deviation, analysis unit, attempt/time boundary, evidence cutoff, development method, and available traces, repository states, patches, test results, configurations, and human reports. Ask one minimal question when the target or a material boundary is unknowable. Preserve an unknown development method as uncertainty in method-dependent consumption.

## Workflow

### 1. Freeze the target

Record `analysis unit + intended outcome + observed deviation + attempt/time + evidence cutoff + intended decision`. Distinguish the outcome from candidate intermediate mechanisms.

Done when the outcome and available evidence boundary are explicit.

### 2. Reconstruct functions through artifacts

Inspect material events in time order. Map all six L1 functions to actors, input instances, actions, output instances, and downstream consumers using [artifact-flow.md](references/artifact-flow.md). Mark each function observed, inferred, unobserved, or outside the case boundary with a reason.

Assign stable artifact IDs and versions. Record exact source locations, production time, availability, observed consumption, and deviations from each artifact's intended meaning. Link the functional view to the corresponding artifact → (actor, action) → artifact paths. Classify method-dependent consumption edges as applicable, inapplicable, or unknown from the development method and its source.

Done when each material action is grounded in artifacts or an explicit evidence gap, and feedback edges resolve to concrete instances at the appropriate time.

### 3. Submit the causal-research request

Execute the dependency's workflow in the current agent context using its version 1 Request:

- `outcome`: frozen observed outcome; `scope`: unit, attempt/time, environment, intended outcome, and decision.
- `evidence_seeds`: source locations/excerpts, graph records, development-method evidence, gaps, candidate deviations, and supplied theories as unranked leads.
- `constraints`: cutoff, permitted sources/tests, access limits, and request for artifact-grounded mechanisms with unknown links marked.
- `detail`: `full` for an auditable ledger; `output_language`: requester language; `contract_version`: `1`. Omit `caller_tag` unless useful for correlation.

Provide accessible sources or excerpts. Artifact IDs are case evidence within the existing fields. The dependency can challenge the graph and consider explanations outside it.

Invoke the dependency's complete causal comparison for this target. Local-only access is a source constraint, not a reason to bypass the dependency.

Done when a standard Response is available or a missing-dependency/access blocker is recorded.

For `completed`, map the returned comparison to artifact paths. For `evidence_limited`, preserve provisional conclusions and unresolved links. For `needs_clarification`, obtain the missing boundary and resubmit. For `blocked`, report errors and descriptive findings. A malformed response or unsupported version requires a valid dependency response before a causal ruling.

### 4. Ground the returned attribution

Render the returned comparison with L1 and artifact instance references. For each leading mechanism, identify the producer/action, affected artifact and version, downstream consumer/action, supported deviation, outcome path, and intervention target.

Check whether the response supports production failure, handoff failure, consumption failure, or an interaction. Preserve unresolved alternatives and missing links. Actor attribution requires evidence about the responsible action and inputs available then.

If the comparison lacks a material artifact link, proposes a new mechanism, or new evidence changes the case, send an updated Request to the dependency. The host adds graph references and presentation; causal revisions return to the dependency.

Done when every reported attribution is traceable to a returned causal claim and a concrete artifact path, or is explicitly evidence-limited.

### 5. Assess representation sufficiency

Ask whether the L1 plus artifact graph can express the returned mechanism and distinguish the intended intervention. First refine artifact identity, version, content, actor, or handoff where that resolves the ambiguity.

If a residual remains, propose the smallest case-local factor, relation, or configuration extension. Send it back as a seed for renewed causal comparison before recommending it. Show the residual, overlap with existing concepts, discriminating prediction, and intervention difference. Core ontology promotion requires human review.

Done when coverage and resolution are assessed and any adaptation is grounded in the dependency's comparison.

### 6. Report

Use the report template. Preserve the dependency's ruling, status, limitations, errors, next discriminating evidence, and stop reason. Include the artifact graph and specific attribution path even in a concise report. If further evidence is needed and authorized, collect it and re-invoke the dependency.

Persist the request, response, graph, and source references alongside the report when a saved diagnosis is requested; otherwise retain them in working notes. Keep observations, inferences, and unknowns explicit.
