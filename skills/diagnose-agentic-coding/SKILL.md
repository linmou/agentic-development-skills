---
name: diagnose-agentic-coding
description: Diagnose root causes of failed, degraded, unsafe, inefficient, or falsely completed agentic coding runs using a hierarchical functional ontology and competing causal explanations. Use for agent trace or trajectory diagnosis, benchmark failure analysis, coding-agent postmortems, model-versus-harness attribution, tool-use and coordination failures, verifier or completion errors, recurring agentic coding failure patterns, and proposals to refine an insufficient ontology. Do not use for ordinary debugging when only the code defect—not the behavior of the coding agent or its surrounding system—is under analysis.
---

# Diagnose Agentic Coding

## Purpose

Explain why an agentic coding outcome occurred well enough to choose a corrective intervention. Treat the ontology as a structured hypothesis generator, not a list of labels and not proof of causation. Diagnose failures in the joint system of model, harness, tools, environment, task, evaluator, and their interactions.

Keep localization optional and skip it by default. Traverse the compact L1/L2 hierarchy directly unless the evidence volume makes localization useful.

Read:

- [functional-ontology.md](references/functional-ontology.md) before mapping hypotheses.
- [diagnostic-protocol.md](references/diagnostic-protocol.md) for evidence roles, candidate construction, tests, ranking, stopping, and ontology adaptation.
- [report-template.md](references/report-template.md) before reporting a diagnosis.

## Required inputs

Obtain or infer:

- the task, intended goal, success conditions, constraints, and authorized action boundary;
- the observed outcome to explain, distinguished from nearby symptoms;
- the analysis unit and evidence cutoff;
- available task specifications, conversation/tool traces, patches, repository state, test or verifier output, environment/configuration, and human reports.

Ask one minimal question only when the outcome or a boundary that materially changes the diagnosis is unknowable. Otherwise proceed, label missing evidence, and reduce conclusion strength.

Treat every supplied diagnosis, evaluator label, and user theory as an evidence seed rather than accepted truth.

## Workflow

### 1. Freeze the diagnostic target

Write a one-sentence explanandum containing:

`analysis unit + intended outcome + observed deviation + relevant time/attempt + evidence cutoff`

Separate the terminal outcome from manifestations. For example, “tests failed” may be the outcome to explain; “the agent edited the wrong module” is a candidate intermediate mechanism, not automatically the root cause.

### 2. Reconstruct the evidence record

Order material observations by time. Mark each as one of:

- outcome measurement;
- antecedent condition;
- mechanism/process evidence;
- later corroboration;
- human report;
- inference;
- unknown timing.

Record source independence and reliability. Do not treat repeated summaries of the same log event as independent evidence. Distinguish absence of evidence from a search with a credible opportunity to detect the event.

Use safe read-only inspection and non-destructive tests when available. Do not implement a fix unless the user asks for one.

### 3. Traverse the functional ontology

Start at all six L1 functions and inspect relevant L2 functions and causal handoffs. Expand only branches that could discriminate among live explanations.

Generate candidates from four representational forms:

1. **Node deviation** — a required function was not performed adequately.
2. **Edge deviation** — individually plausible functions failed to pass the needed information, constraint, plan, observation, or evidence.
3. **Configuration deviation** — an interaction among factors failed although no factor alone is sufficient.
4. **Residual explanation** — evidence suggests a factor, relation, or configuration not represented in the current ontology.

Do not equate the last observed failure with the originating cause. Trace upstream until reaching a mechanism whose removal would plausibly prevent or materially reduce the outcome within the declared boundary.

### 4. Build rival causal models

Create at least three materially distinct hypotheses when the search space permits. Include plausible alternatives across model behavior, harness/tooling, task/evaluation, environment, and interaction effects. Include measurement artifact or evaluator misalignment when plausible.

For every hypothesis, specify:

`condition -> functional breakdown -> intermediate trace -> observed outcome`

Also state its ontology anchor and type, discriminating predictions, possible refuters, boundary conditions, and corrective implication. A factor list is not a model set.

Keep `H_other` visible when coverage is uncertain, but do not use it as an untestable catch-all.

### 5. Run iterative competing-explanation analysis

Test all material hypotheses symmetrically against support, contradiction, missing mechanism links, anomalies, and counterfactual evidence. Prefer discriminating process evidence over source count or narrative plausibility.

When evidence cannot distinguish candidates:

1. identify the observation or safe test most likely to change their relative ranking;
2. estimate its diagnostic value, cost, delay, and risk;
3. obtain it when authorized and worthwhile;
4. update and rerank all affected candidates, not only the favored one.

Use qualitative causal statuses from [diagnostic-protocol.md](references/diagnostic-protocol.md). Do not manufacture precise probabilities from sparse evidence.

### 6. Invoke open-world causal research conditionally

Invoke `$competing-explanations-causal-research` when a material candidate depends on external evidence not contained in the case artifacts—for example, version-specific tool behavior, known harness limitations, benchmark/evaluator properties, model API behavior, or comparative failure cases. Do not invoke it merely to restate local logs.

Use its version 1 Request/Response contract exactly:

```json
{
  "contract_version": 1,
  "outcome": "<the frozen outcome to explain>",
  "scope": "<analysis unit, environment, versions, period, intended decision>",
  "evidence_seeds": ["<relevant artifacts, links, records, or claims>"],
  "constraints": "<research cutoff, source/access limits, required comparisons>",
  "detail": "brief|standard|full",
  "output_language": "<requester language>",
  "caller_tag": "agentic-coding-diagnosis"
}
```

Do not add caller phases or redefine fields. Treat the returned report as an external-evidence subanalysis, preserve its limitations, and integrate it by updating the relevant hypotheses. If it returns `needs_clarification`, ask only for the missing material boundary. If it returns `evidence_limited` or `blocked`, do not silently replace it with unsupported causal claims.

### 7. Evaluate ontology sufficiency

Call the ontology sufficient only when it can represent the leading mechanism at the resolution needed for the intended intervention. Mere ability to attach a broad label is not sufficient.

If it is insufficient, propose exactly the smallest justified adaptation:

- **vertical refinement** — decompose a coarse existing factor;
- **horizontal expansion** — add a missing factor;
- **relation revision** — add or revise a causal handoff;
- **configuration revision** — add or revise an interaction pattern.

Rerun the live hypothesis comparison with the proposed extension before recommending it. Show motivating residuals, overlap with existing concepts, predicted observations, and improvement in explanatory discrimination.

Never update the core ontology automatically. Present the proposal for human choice: reject, revise, retain case-locally, or promote to the core ontology.

### 8. Stop and report

Stop when one of these holds:

- the leading explanation set is stable enough to choose the next consequential action and more evidence is unlikely to change that action;
- the expected diagnostic value of the next evidence is no greater than its cost, delay, or risk;
- the ontology is demonstrably insufficient and a bounded adaptation proposal is ready for human review;
- access limits prevent further discrimination.

Do not use “root cause” as a certainty label. Report a relatively leading, jointly leading, unexcluded, weakened, or evidence-limited explanation and state what could change the ruling.

## Non-negotiable safeguards

- Preserve the distinction among observation, inference, and causal conclusion.
- Compare hypotheses before combining them into a multi-cause account.
- Do not infer model failure from an agent failure; test harness, tool, evaluator, and interaction explanations.
- Do not infer causation from chronology, correlation, salience, or ontology membership.
- Do not claim exhaustive coverage from an open-world diagnosis.
- Keep active evidence collection and rediagnosis inside the competing-explanation loop.
- Keep temporary traversal of existing hierarchy separate from genuine ontology learning.
- Keep diagnosis separate from remediation unless remediation is explicitly requested.
