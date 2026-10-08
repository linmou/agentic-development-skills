---
name: diagnose-agentic-coding
description: Diagnose agentic coding failures, degraded trajectories, and false completion using L1 functional and artifact produce-consumption graphs, with competing-explanations-causal-research for causal comparison. Use for agent trace analysis, coding-agent postmortems, model-versus-harness attribution, coordination failures, and ontology sufficiency review.
---

# Diagnose Agentic Coding

Explain an agentic coding outcome well enough to locate a supported artifact-level mechanism, trace its causal provenance, and choose a corrective intervention. The diagnostic unit is the joint system of actors, tools, environment, task, and evaluator. Rootness means the deepest evidence-supported causal mechanism within the declared investigation boundary that explains the failure and identifies recurrence conditions; it is not necessarily the earliest artifact, oldest actor, or best intervention point.

## Required references and dependency

The normative references are [diagnostic-definitions.md](references/diagnostic-definitions.md), [functional-ontology.md](references/functional-ontology.md), [artifact-flow.md](references/artifact-flow.md), [causal-interface.md](references/causal-interface.md), and [report-template.md](references/report-template.md). `references/archive/` contains historical material for provenance only; it is not an alternate ontology or workflow.

Read the diagnostic definitions, functional, and artifact references to reconstruct the graph views and apply the Node, Edge, Interaction, and three-level attribution definitions. The artifact graph decomposes the L1 functional graph as `input artifacts → (actor, action) → output artifacts → (consumer, action)`. L1 functions classify actions; use IDs 1–6 for diagnosis. Treat System State (SYS) as a first-class external state entity alongside the six semantic artifacts; it is not a seventh L1 function or mandatory document.

Read the causal interface before invoking the dependency and the report template when writing the result.

Every causal diagnosis invokes the `competing-explanations-causal-research` skill, including cases supported entirely by local traces. That skill owns evidence assessment, rival-model construction, symmetric testing, ranking, execution and evidence statuses, and stopping. This host owns artifact reconstruction, L1 mapping, and presentation of the returned attribution. The causal interface and the dependency's versioned call contract define the boundary.

If the dependency cannot be found or loaded, report the missing dependency and retain the descriptive graph with its unknowns. A causal ruling requires the dependency.

## Inputs

Obtain or infer the task, intended outcome, success conditions, action boundary, observed deviation, analysis unit, attempt/time boundary, evidence cutoff, development method, and available traces, repository states, patches, test results, configurations, and human reports. Ask one minimal question when the target or a material boundary is unknowable. Preserve method-dependent consumption evidence and method uncertainty when they materially affect the diagnosis.

## Workflow

### 1. Freeze the target

Record `analysis unit + intended outcome + observed deviation + attempt/time + evidence cutoff + intended decision`. Distinguish the outcome from candidate intermediate mechanisms.

Done when the outcome and available evidence boundary are explicit.

### 2. Reconstruct functions through artifacts

Inspect material events in time order. Reconstruct concrete SYS versions and transitions where evidence permits, then map all six L1 functions to actors, input instances, actions, output instances, and downstream consumers using [artifact-flow.md](references/artifact-flow.md). Keep SYS (what the target system actually is), SM (the agent's representation), and ER (what actions were recorded) separate. Mark each function observed, inferred, unobserved, or outside the case boundary with a reason.

Assign stable artifact IDs and versions. Version SYS with commits, hashes, snapshots, timestamps, database migrations, deployment identifiers, or other grounded evidence. Record exact source locations, production time, availability, observed consumption, and deviations from each artifact's intended meaning. Reconstruct relevant configuration artifacts (system/developer instructions, skills, project rules, tool policies, and harness settings) as versioned inputs, including provenance, temporal validity, delivery/availability, and evidence of effective consumption. Distinguish existence from delivery and use; infer effective runtime conditions from evidence, not intended settings alone. Trace defective configuration upstream through the actions and handoffs that produced or propagated it. Treat inspection results as evidence about SYS, not as SYS itself; do not infer complete SYS from a partial inspection. Link the functional view to the corresponding artifact → (actor, action) → artifact paths and SYS transitions. Record method-dependent edge evidence when the development method or its source materially affects the diagnosis.

Done when each material action is grounded in artifacts or an explicit evidence gap, and feedback edges resolve to concrete instances at the appropriate time.

### 3a. Trace provenance and transferability

Apply the three levels in [diagnostic-definitions.md](references/diagnostic-definitions.md): establish Level 1 error location, trace Level 2 root causal mechanism through user/request sources, model or agent behavior, harness/developer actions, and third-party or environment conditions, then state Level 3 generalization conditions. Preserve joint causes and competing explanations; do not promote a plausible hypothesis to a proven cause. Record recurrence conditions, scope limits, evidence needed to test transfer beyond this case, and the intervention target separately from causal origin. A single trace ordinarily supports a case-specific mechanism or transferable hypothesis, not a stable cross-task capability claim.

### 3. Submit the causal-research request

Execute the dependency's workflow in the current agent context using the Request defined in [causal-interface.md](references/causal-interface.md). Provide accessible sources or excerpts, with artifact IDs as case evidence in the existing fields. The dependency can challenge the graph and consider explanations outside it.

Invoke the dependency's complete causal comparison for this target. Local-only access is a source constraint, not a reason to bypass the dependency.

Done when a standard Response is available or a missing-dependency/access blocker is recorded.

For a completed investigation, map the returned comparison to artifact paths and preserve the contract's evidence assessment and unresolved links. For clarification, obtain the missing boundary and resubmit. For blocking, report errors and descriptive findings. A malformed response or unsupported version requires a valid dependency response before a causal ruling. If no candidate is sufficiently supported, report root cause undetermined; several proposed explanations do not establish a cause.

### 4. Ground the returned attribution

Render the returned comparison with L1, artifact instance, and SYS version/transition references. For each leading mechanism, identify the producer/action, affected artifact or SYS version, downstream consumer/action, supported deviation, outcome path, and intervention target.

Check whether the response supports production failure, handoff failure, consumption failure, or an interaction. Preserve unresolved alternatives and missing links. Actor attribution requires evidence about the responsible action and inputs available then.

If the comparison lacks a material artifact link, proposes a new mechanism, or new evidence changes the case, send an updated Request to the dependency. The host adds graph references and presentation; causal revisions return to the dependency.

Done when every reported attribution is traceable to a returned causal claim and a concrete artifact path, with the dependency's evidence assessment preserved.

### 5. Assess representation sufficiency

Ask whether the L1 plus artifact graph can express the returned mechanism and distinguish the intended intervention. First refine artifact identity, version, content, actor, or handoff where that resolves the ambiguity.

If a residual remains, propose the smallest case-local factor, relation, or configuration extension. Send it back as a seed for renewed causal comparison before recommending it. Show the residual, overlap with existing concepts, discriminating prediction, and intervention difference. Core ontology promotion requires human review.

Done when coverage and resolution are assessed and any adaptation is grounded in the dependency's comparison.

### 6. Report

Use the report template. Preserve the dependency's ruling, status, limitations, errors, next discriminating evidence, and stop reason. Include the artifact graph and specific attribution path even in a concise report. If further evidence is needed and authorized, collect it and re-invoke the dependency.

Persist the request, response, graph, and source references alongside the report when a saved diagnosis is requested; otherwise retain them in working notes. Keep observations, inferences, and unknowns explicit.
