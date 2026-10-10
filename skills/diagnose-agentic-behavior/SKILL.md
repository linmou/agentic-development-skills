---
name: diagnose-agentic-behavior
description: Diagnose why an agent failed in any domain (coding, browsing, research, tool use, multi-agent, conversation) by inducing a task-specific ontology without reading the trace, annotating the trace against it, and delegating causal comparison to competing-explanations-causal-research. Use for agent failure postmortems, agent trace analysis, model-versus-harness attribution, and ontology sufficiency review.
---

# Diagnose Agentic Behavior

Explain an agent failure well enough to locate a supported mechanism, trace its causal provenance, and choose a corrective intervention. The diagnostic unit is the joint system of actors, tools, environment, task, and evaluator. Rootness means the deepest evidence-supported causal mechanism within the declared investigation boundary; it is not necessarily the earliest event, the oldest actor, or the best intervention point.

Unlike `diagnose-agentic-coding`, this skill has no predefined domain ontology. It keeps a fixed **meta-ontology** (the grammar) and induces a **task ontology** (the vocabulary) for each case from the task. The ontology is frozen before the trace is read and stays frozen for the whole case, so it describes what the task required rather than what this run happened to do. The trace is evidence and is annotated against that frozen ontology.

## Required references and dependency

Normative references:

- [meta-ontology.md](references/meta-ontology.md): fixed grammar, environment state, belief state, and trace, evidence statuses, and aliases to `diagnose-agentic-coding`.
- [diagnostic-definitions.md](references/diagnostic-definitions.md): Node, Edge, Interaction, and the three attribution levels.
- [ontology-induction.md](references/ontology-induction.md): trace-blind derivation of the task ontology, admission rules, freezing, and the expressibility check.
- [annotated-trace.md](references/annotated-trace.md): annotating trace spans against the ontology, the residual log, candidate deviations, and the agent task model.
- [causal-interface.md](references/causal-interface.md): boundary with the causal-research dependency.
- [report-template.md](references/report-template.md): report structure.
- [lenses/](references/lenses/README.md): coverage checklists, grounded in published agent-failure taxonomies, applied to the task ontology before it is frozen.

Every causal diagnosis invokes the `competing-explanations-causal-research` skill, including cases supported entirely by local traces. That skill owns evidence assessment, rival-model construction, symmetric testing, ranking, statuses, and stopping. This host owns target framing, ontology induction, trace annotation, the expressibility check, and presentation of the returned attribution.

If the dependency cannot be found or loaded, report the missing dependency and retain the descriptive annotated trace with its unknowns. A causal ruling requires the dependency.

## Inputs

Obtain or infer: the task and its specification, the environment and its affordances, the intended outcome and success conditions, the observed deviation, action boundary, analysis unit, attempt/time boundary, evidence cutoff, intended decision, and available traces, environment-state snapshots, scaffold configuration, evaluator outputs, and human reports. Ask one minimal question when the target or a material boundary is unknowable.

## Workflow

### 1. Freeze the failure target

Record `analysis unit + intended outcome + observed deviation + attempt/time + evidence cutoff + intended decision`. State the success conditions so each is checkable against environment-state evidence. Distinguish the observed deviation from candidate mechanisms.

Done when the intended outcome, the observed deviation, and the evidence boundary are explicit.

### 2. Induce, audit, and freeze the task ontology, trace-blind

Following [ontology-induction.md](references/ontology-induction.md), derive the task ontology from the task specification, environment affordances, configuration, and the frozen target. Backward-chain from the success conditions to the required artifact roles, functions, producers, consumers, environment-state locators, completion evidence, and the decision points where a run could leave the success path. Every type passes the admission rules.

Before freezing, apply each relevant lens as described in [lenses/README.md](references/lenses/README.md), and close any gap that passes the admission rules. Keep the trace, evaluator verdicts, and postmortems out of this step. When a subagent is available, run this step in a fresh subagent given only the task specification, configuration, affordances, and frozen target.

Freeze the result as `O_v0`. It is the ontology for the rest of the case.

Done when `O_v0` is frozen, each type has a definition, an is/is-not boundary, a derivation source, and an exposure status, and each applied lens is recorded as covered, gap-noted, or not applicable.

### 3. Annotate the trace

Following [annotated-trace.md](references/annotated-trace.md), scan the trace in time order and annotate each material action as an instance of an `O_v0` type, keeping environment state, belief state, and trace distinct as defined in [meta-ontology.md](references/meta-ontology.md). Then walk the ontology to find **errors of omission** (expected artifacts, actions, or data flows that never occurred) and complete coverage past the first salient anomaly. Log every material action that does not map cleanly in the **residual log** with a disposition, and list candidate deviations. When a task-model divergence is among them, build the **agent task model** as a belief-state artifact.

Done when each material action is annotated or logged as a residual with a disposition, each expected type carries an evidence status, data flows resolve to concrete versions, and candidate deviations are listed.

### 4. Submit the causal-research request

Execute the dependency's workflow using the Request in [causal-interface.md](references/causal-interface.md). The dependency may challenge the annotation and propose explanations outside it.

Done when a standard Response is available or a missing-dependency or access blocker is recorded.

### 5. Check expressibility and ground the attribution

Run the **expressibility check** in [ontology-induction.md](references/ontology-induction.md) on every returned model. The ontology stays frozen: a link that maps to no type is rendered with its raw trace spans and recorded as a representation gap, and the model keeps its returned rank. Build or revise the agent task model here when a returned model depends on it.

Then render the returned comparison on the annotated trace using the three levels in [diagnostic-definitions.md](references/diagnostic-definitions.md). For each leading mechanism, identify the producer and action, the affected artifact or environment-state version, the downstream consumer and action, the supported deviation, the outcome path, and the intervention target, and classify it as production, data flow, consumption, or interaction. Actor attribution requires evidence about the action and the inputs in context at that time. If no candidate is sufficiently supported, report **root cause undetermined**.

If the comparison lacks a material link, or new evidence changes the case, send an updated Request; causal revisions return to the dependency.

Done when every link of every returned model is mapped to the annotated trace or recorded as a representation gap with its raw spans, and every reported attribution traces to a returned causal claim and a concrete path.

### 6. Assess representation and propose lens types

Ask whether `O_v0` expressed the returned mechanism and distinguished the intended intervention, using the representation gaps and residual log as evidence. For any type worth adding to a lens for future cases, write a proposal with its definition, the reason it is not specific to this task, and the source case. Promotion requires human review; this case's ontology stays as frozen.

Done when the representation verdict is recorded and each lens proposal is listed with its reason, or "none" is stated.

### 7. Report

Use the report template. Preserve the dependency's ruling, status, limitations, errors, next discriminating evidence, and stop reason. When a saved diagnosis is requested, persist the request, response, `O_v0`, annotated trace, residual log, and source references alongside the report.

Done when every report-template section is present, filled or marked unknown, and requested artifacts are saved.

## Light mode

For a simple, low-stakes case, use the control-loop lens as `O_v0` instead of a full derivation, as an explicit exception to the lens rule. Annotate the trace and keep the residual log. When residuals accumulate or returned models leave many representation gaps, restart from step 2 with a full derivation, marking its types `post-exposure`. The dependency is still required for a causal ruling.
