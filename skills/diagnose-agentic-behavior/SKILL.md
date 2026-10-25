---
name: diagnose-agentic-behavior
description: Diagnose why an agent failed in any domain (coding, browsing, research, tool use, multi-agent, conversation) by inducing a task-specific ontology without reading the trace, mapping the trace onto it, and delegating causal comparison to competing-explanations-causal-research. Use for agent failure postmortems, agent trace analysis, model-versus-harness attribution, and ontology sufficiency review.
---

# Diagnose Agentic Behavior

Explain an agent failure well enough to locate a supported mechanism, trace its causal provenance, and choose a corrective intervention. The diagnostic unit is the joint system of actors, tools, environment, task, and evaluator. Rootness means the deepest evidence-supported causal mechanism within the declared investigation boundary; it is not necessarily the earliest event, the oldest actor, or the best intervention point.

Unlike `diagnose-agentic-coding`, this skill has no predefined domain ontology. It keeps a fixed **meta-ontology** (the grammar) and induces a **task ontology** (the vocabulary) for each case from the task. The trace is evidence and is mapped onto the task ontology as the single case schema.

## Required references and dependency

Normative references:

- [meta-ontology.md](references/meta-ontology.md): fixed grammar, the World/Belief/Record layers, and evidence statuses.
- [diagnostic-definitions.md](references/diagnostic-definitions.md): Node, Edge, Interaction, and the three attribution levels.
- [ontology-induction.md](references/ontology-induction.md): trace-blind derivation of the expected task ontology, admission rules, versioning, and the expressibility check.
- [case-graph.md](references/case-graph.md): mapping trace spans onto the task ontology, the residual log, candidate deviations, and the agent task model.
- [causal-interface.md](references/causal-interface.md): boundary with the causal-research dependency.
- [report-template.md](references/report-template.md): report structure.
- [lenses/](references/lenses/README.md): coverage checklists applied to the task ontology.

Every causal diagnosis invokes the `competing-explanations-causal-research` skill, including cases supported entirely by local traces. That skill owns evidence assessment, rival-model construction, symmetric testing, ranking, statuses, and stopping. This host owns target framing, ontology induction, trace mapping, the expressibility check, and presentation of the returned attribution.

If the dependency cannot be found or loaded, report the missing dependency and retain the descriptive case graph with its unknowns. A causal ruling requires the dependency.

## Inputs

Obtain or infer: the task and its specification, the environment and its affordances, the intended outcome and success conditions, the observed deviation, action boundary, analysis unit, attempt/time boundary, evidence cutoff, intended decision, and available traces, state snapshots, configurations, evaluator outputs, and human reports. Ask one minimal question when the target or a material boundary is unknowable.

## Workflow

### 1. Freeze the failure target

Record `analysis unit + intended outcome + observed deviation + attempt/time + evidence cutoff + intended decision`. State the success conditions so each is checkable against World evidence. Distinguish the observed deviation from candidate mechanisms.

Done when the intended outcome, the observed deviation, and the evidence boundary are explicit.

### 2. Induce the expected task ontology, trace-blind

Following [ontology-induction.md](references/ontology-induction.md), derive the task ontology from the task specification, environment affordances, configuration, and the frozen target. Backward-chain from the success conditions to the required artifact roles, functions, producers, consumers, state locators, completion evidence, and the decision points where a run could leave the success path. Every type passes the admission rules.

Keep the trace, evaluator verdicts, and postmortems out of this step. When a subagent is available, derive `O_v0` in a fresh subagent given only the task specification, configuration, affordances, and frozen target. Freeze the result as `O_v0`, marking any type derived after trace exposure as `post-exposure`.

Done when `O_v0` is frozen and each type has a definition, an is/is-not boundary, a derivation source, and an exposure status.

### 3. Map the trace onto the ontology

Following [case-graph.md](references/case-graph.md), scan the trace in time order and annotate each material event as an instance of an `O_v0` type, keeping the layers defined in [meta-ontology.md](references/meta-ontology.md) separate. Then walk the ontology to find **absences** (expected artifacts, actions, or handoffs that never occurred) and complete coverage past the first salient anomaly. Log every material event that does not map cleanly in the **residual log**.

Done when each material event is mapped or logged as a residual, each expected type carries an evidence status, and feedback edges resolve to concrete versions.

### 4. Audit coverage with lenses

Apply each relevant lens as described in [lenses/README.md](references/lenses/README.md).

Done when each applied lens is recorded as covered, gap-noted, or not applicable.

### 5. Revise the ontology and list candidate deviations

Revise only when a residual or lens gap justifies it, following the revision rules in [ontology-induction.md](references/ontology-induction.md), then remap affected events. List candidate deviations from [case-graph.md](references/case-graph.md). When a task-model divergence is among them, build the **agent task model** now.

Done when every residual is resolved, carried as an explicit gap, or rejected with a reason, and candidate deviations are listed.

### 6. Submit the causal-research request

Execute the dependency's workflow using the Request in [causal-interface.md](references/causal-interface.md). The dependency may challenge the graph and propose explanations outside it.

Done when a standard Response is available or a missing-dependency or access blocker is recorded.

### 7. Check expressibility and ground the attribution

Run the **expressibility check** in [ontology-induction.md](references/ontology-induction.md) on every returned model. A gap leads to an ontology extension, a remap, and a new Request before the ranking is accepted. Build or revise the agent task model here when a returned model depends on it.

Then render the returned comparison on the case graph using the three levels in [diagnostic-definitions.md](references/diagnostic-definitions.md). For each leading mechanism, identify the producer and action, the affected artifact or world-state version, the downstream consumer and action, the supported deviation, the outcome path, and the intervention target, and classify it as production, handoff, consumption, or interaction. Actor attribution requires evidence about the action and the inputs available at that time. If no candidate is sufficiently supported, report **root cause undetermined**.

If the comparison lacks a material link, or new evidence changes the case, send an updated Request; causal revisions return to the dependency.

Done when every returned model's chain maps onto the case graph or its gap is recorded as unresolved, and every reported attribution traces to a returned causal claim and a concrete case-graph path.

### 8. Assess representation and propose lens types

Ask whether the final ontology expresses the returned mechanism and distinguishes the intended intervention. For any case type worth adding to a lens, write a proposal with its definition, the reason it is not specific to this task, and the source case. Promotion requires human review.

Done when the representation verdict is recorded and each lens proposal is listed with its reason, or "none" is stated.

### 9. Report

Use the report template. Preserve the dependency's ruling, status, limitations, errors, next discriminating evidence, and stop reason. When a saved diagnosis is requested, persist the request, response, ontology versions, case graph, residual log, and source references alongside the report.

Done when every report-template section is present, filled or marked unknown, and requested artifacts are saved.

## Light mode

For a simple, low-stakes case, use the control-loop lens as `O_v0` instead of a full derivation, as an explicit exception to the lens rule, and skip step 4. Map the trace and keep the residual log. Escalate to full induction when residuals accumulate or a returned model fails the expressibility check. The dependency is still required for a causal ruling.
