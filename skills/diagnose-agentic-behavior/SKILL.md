---
name: diagnose-agentic-behavior
description: Diagnose why an agent behaved as it did in any domain (coding, browsing, research, tool use, multi-agent, conversation) by inducing a task-specific ontology before reading the outcome, mapping the trace onto it, and delegating causal comparison to competing-explanations-causal-research. Use for agent trace analysis, failure postmortems, unexpected successes, contrastive "why X rather than Y" questions, model-versus-harness attribution, and ontology sufficiency review.
---

# Diagnose Agentic Behavior

Explain an agent's behavior well enough to locate a supported mechanism, trace its causal provenance, and choose a corrective or reinforcing intervention. The diagnostic unit is the joint system of actors, tools, environment, task, and evaluator. Rootness means the deepest evidence-supported causal mechanism within the declared investigation boundary; it is not necessarily the earliest event, the oldest actor, or the best intervention point.

Unlike `diagnose-agentic-coding`, this skill has no predefined domain ontology. It keeps a fixed **meta-ontology** (the grammar) and induces a **task ontology** (the vocabulary) for each case from the task, not from the trace. The trace is evidence and is mapped onto the task ontology; it is never re-modelled as a second ontology.

## Required references and dependency

Normative references:

- [meta-ontology.md](references/meta-ontology.md): fixed grammar every case uses.
- [diagnostic-definitions.md](references/diagnostic-definitions.md): Node, Edge, Interaction, and the three attribution levels.
- [ontology-induction.md](references/ontology-induction.md): outcome-blind derivation of the expected task ontology, admission rules, and versioning.
- [case-graph.md](references/case-graph.md): mapping trace spans onto the task ontology, the residual log, and the optional agent task model.
- [causal-interface.md](references/causal-interface.md): boundary with the causal-research dependency.
- [report-template.md](references/report-template.md): report structure.
- [lenses/](references/lenses/): optional coverage audits. A lens is a checklist, never a required schema or traversal.

Every causal diagnosis invokes the `competing-explanations-causal-research` skill, including cases supported entirely by local traces. That skill owns evidence assessment, rival-model construction, symmetric testing, ranking, statuses, and stopping. This host owns target framing, ontology induction, trace mapping, and presentation of the returned attribution.

If the dependency cannot be found or loaded, report the missing dependency and retain the descriptive case graph with its unknowns. A causal ruling requires the dependency.

## Inputs

Obtain or infer: the task and its specification, the environment and its affordances, the behavior to explain, the contrast case, success conditions (if any), action boundary, analysis unit, attempt/time boundary, evidence cutoff, intended decision, and available traces, state snapshots, configurations, evaluator outputs, and human reports. Ask one minimal question when the target or a material boundary is unknowable.

## Workflow

### 1. Freeze a contrastive target

Record `analysis unit + behavior X + foil Y + attempt/time + evidence cutoff + intended decision`. The foil defines relevance: only factors that differ between the paths to X and to Y are candidate causes. A failure diagnosis is the special case where Y is the intended outcome; a success or surprise diagnosis names a plausible alternative behavior as Y. If the requester gives no foil, propose the most decision-relevant one and state it.

Done when X, Y, and the evidence boundary are explicit, and the outcome is distinguished from candidate mechanisms.

### 2. Induce the expected task ontology, outcome-blind

Following [ontology-induction.md](references/ontology-induction.md), derive the task ontology from the task specification, environment affordances, configuration, and foil, **before reading how the run went**. Backward-chain from success conditions (or from the conditions that would produce Y) to the required artifact roles, functions, producers, consumers, state locators, and completion evidence. Every type must pass the admission rules.

Freeze the result as `O_v0` with its derivation sources. If the outcome has already been seen, say so and record which types were added after exposure; they carry lower weight as unbiased expectations.

Done when `O_v0` is frozen and each type has a definition, an is/is-not boundary, and a derivation source.

### 3. Map the trace onto the ontology

Following [case-graph.md](references/case-graph.md), scan the trace in time order and annotate material events as instances of `O_v0` types: `input artifacts → (actor, action) → output artifacts → (consumer, action)`, with world-state transitions. Keep the three layers separate: **World** (what actually is), **Belief** (the agent's representation), **Record** (what was logged or claimed). Record availability and use separately.

Use the ontology for two things scanning alone cannot do: detect **absences** (expected artifacts, actions, or handoffs that never occurred) and enforce **coverage** past the first salient anomaly.

Log every material event that does not map cleanly in the **residual log**, with its span and the reason it does not fit. Do not open-code the trace into a parallel ontology.

Done when each material event is mapped or logged as a residual, each expected type is marked observed, inferred, absent, or outside the boundary, and feedback edges resolve to concrete versions.

### 4. Audit coverage with lenses

Apply each relevant lens in [lenses/](references/lenses/) as a checklist against the task ontology, not the trace. For each lens function, ask whether some task-ontology type plays that role. Record gaps as questions, not findings. A gap becomes a revision only if it passes the admission rules.

Done when each applied lens is recorded as covered, gap-noted, or not applicable.

### 5. Revise the ontology from residuals

Revise only when a residual or lens gap justifies it. Prefer refining an existing type (identity, version, boundary) over adding one. A new type must pass the admission rules, especially the **discrimination** test. Record each change as `O_vN → O_vN+1` with the triggering residual, then remap affected events.

When a rival hypothesis needs it, infer the **agent task model** (the goal, deliverables, and completion criterion the agent appears to have operated under) as a Belief-layer artifact, cited from behavior and marked inferred. Compare it with the expected ontology; divergence is a candidate mechanism, not a finding.

Done when residuals are resolved, carried as explicit gaps, or rejected with a reason.

### 6. Submit the causal-research request

Execute the dependency's workflow using the Request in [causal-interface.md](references/causal-interface.md), including the current ontology version and residual log. The dependency may challenge the graph and propose explanations outside it.

**Expressibility symmetry:** if the dependency reports that a rival cannot be stated in the current ontology, extend the ontology under the admission rules and resubmit before ranking is accepted. Do not let vocabulary decide the ranking.

Done when a standard Response is available or a missing-dependency or access blocker is recorded. If no candidate is sufficiently supported, report **root cause undetermined**.

### 7. Ground the returned attribution

Render the returned comparison on the case graph using the three levels in [diagnostic-definitions.md](references/diagnostic-definitions.md). For each leading mechanism, identify the producer and action, the affected artifact or world-state version, the downstream consumer and action, the supported deviation, the outcome path, and the intervention target. Check whether it is a production, handoff, consumption, or interaction mechanism. Actor attribution requires evidence about the action and the inputs available at that time.

If the comparison lacks a material link, proposes a new mechanism, or new evidence changes the case, send an updated Request. The host adds graph references and presentation; causal revisions return to the dependency.

Done when every reported attribution traces to a returned causal claim and a concrete path in the case graph.

### 8. Assess representation and register the case

Ask whether the final ontology expresses the returned mechanism and distinguishes the intended intervention. Then record the case ontology, its revision log, and which rivals forced extensions. Propose a type for promotion into a lens only when it recurs across cases with a stated alignment; promotion requires human review. Level 3 generalization claims must be phrased in types that recur across cases; a single case supports only a case-specific mechanism or a transferable hypothesis.

### 9. Report

Use the report template. Preserve the dependency's ruling, status, limitations, errors, next discriminating evidence, and stop reason. Include the frozen ontology, its revision log, the case-graph path, and the residual log even in a concise report.

Persist the request, response, ontology versions, case graph, and source references alongside the report when a saved diagnosis is requested. Keep observations, inferences, and unknowns explicit.

## Light mode

For a simple, low-stakes case, skip step 2's full derivation: use the control-loop lens as `O_v0`, map the trace, and keep the residual log. Escalate to full induction if residuals accumulate or rivals cannot be expressed. The dependency is still required for a causal ruling.
