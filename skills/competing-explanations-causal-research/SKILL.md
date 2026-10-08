---
name: competing-explanations-causal-research
description: >
  Conduct open-world, evidence-led causal research by comparing rival explanations
  for an observed outcome, decision, change, or difference. Use to investigate why
  a result occurred in any domain—including companies, policy, science, products,
  operations, and institutions—when correlation, chronology, or a single success
  story is not enough. Do not use for simple factual lookup, a single metric, or
  summarising an existing report without testing its causal claims.
---

# Competing-Explanations Causal Research

## Purpose

Explain a specified outcome by comparing plausible mechanisms that could have produced it. Treat the result as a question, not proof of the preferred story. State what the evidence supports, what it weakens, and what remains unknown.

Use English unless the requester asks for another language.

## Non-negotiable gates

Before making a causal claim:

1. **Freeze the outcome.** Define the event, state, change, difference, or trajectory to explain; separate nearby but non-equivalent outcomes; set the unit, population, place, time window, and observation date.
2. **Assign evidence roles and time.** Record whether each item measures the outcome, precedes it, documents a mechanism step, observes it later, or has uncertain timing. Later observation can corroborate or reveal persistence but is not automatically an earlier cause.
3. **Build rival models.** Create at least three plausible explanations when the search space permits. Each model needs a mechanism chain, discriminating predictions, possible refuters, and boundary conditions. A list of contributing factors is not a competing-model set.
4. **Test symmetrically.** Search every material model for supporting evidence, refuting evidence, alternative explanations, and failure or anomalous cases. Count repeated reports of the same underlying material once.
5. **Compare before combining.** First compare models on timing, prediction fit, process evidence, counterfactual evidence, anomalies, scope, and source independence. Only then identify mechanisms as primary, joint, complementary, substitutive, or period-specific.
6. **Make a bounded ruling.** Name the relatively leading explanation or a tie, mechanisms that may amplify it, explanations still unexcluded, and the missing evidence most likely to change the ranking. Never claim exhaustive or uniquely proven causation from an open-world search.

If the requested outcome cannot be identified from the prompt, ask one minimal clarification before researching. If the evidence cannot meet a gate, continue only with an explicitly preliminary or evidence-limited conclusion.

## Workflow

### 1. Scope the question

Record the analysis unit, outcome, period, geography or population, intended decision, and research cutoff. Do not substitute aggregate evidence for the unit under analysis, or a related outcome for the specified one.

### 2. Form models before searching deeply

Generate models from different actors, theories, time periods, and adversarial perspectives. Include measurement artifacts, selection effects, incentives, constraints, policy or institutional conditions, competitor or substitute changes, and path dependence when plausible.

For each candidate, write the mechanism as `condition → decision/action → intermediate change → outcome`, then state observations that would distinguish it from the alternatives. Drop only candidates that are implausible, unobservable, unfalsifiable, or outside the declared scope; state why.

### 3. Build an evidence record

Prefer sources that can directly establish the relevant event or mechanism: primary records, data documentation, regulators, independent evaluations, contracts, customers, partners, and contemporaneous records. Treat interested-party narratives as evidence of their public position or relationship, not independent proof of the claimed causal effect.

Use [the evidence-ledger protocol](references/evidence-ledger.md) for a full study. Keep facts, inferences, search execution, and unknowns separate.

### 4. Test mechanisms and counterfactuals

For each material model, seek support, refutation, alternatives, and failures. Trace the required transitions in its mechanism chain. Where feasible, use before/after comparisons, comparable units, rejected or failed cases, substitutes, competitors, or other defensible counterfactuals. Mark unavailable comparisons as unavailable; do not convert them into zero effect.

### 5. Compare models and determine strength

Give strong disconfirming evidence more weight than a large count of weak confirming sources. Assess explanatory coverage, discriminating predictions, process reality, counterfactual stability, anomaly fit, boundary clarity, and source independence. A model-wide ranking does not automatically establish every causal role within its chain.

Use these status labels:

- **Relatively leading explanation**: strongest within the current candidate set; not a claim of unique cause.
- **Jointly leading explanations**: no supported basis to rank the leading mechanisms apart.
- **Complementary or amplifying mechanism**: may change the strength or reach of another mechanism without explaining the result alone.
- **Unexcluded explanation**: plausible but inadequately tested or evidenced.
- **Weakened explanation**: materially challenged in its stated scope.
- **Evidence-limited**: timing, access, coverage, or quality prevents a reliable ranking.

### 6. Report for a decision

Use [the report template](references/report-template.md) for a full report. A concise answer still includes: the frozen outcome; evidence roles; competing models with predictions and contrary evidence; the relative ruling; limitations, residuals, and the next discriminating evidence.

Explain the decision consequence without turning a provisional causal inference into a recommendation certainty.

## Evidence and writing discipline

- Cite factual claims near the claim and label material inferences and unknowns.
- Do not infer causation from correlation, sequence, a project’s existence, source count, or an interested party’s assertion.
- Distinguish `search completed with no finding` from `fact does not exist`; the former requires a defined search universe with reasonable detection opportunity.
- Reduce conclusion strength for private, early-stage, low-data, inaccessible, or poorly measured cases; do not silently change the question or method to obtain a stronger conclusion.
- Reopen the relevant model comparison when new evidence changes the outcome definition, scope, timing, model set, or material evidence role.

## Invocation contract

This skill works directly from a user request. A host skill or third-party caller may invoke it through the versioned Request/Response contract in [call-contract.md](references/call-contract.md). The contract is owned here; callers must not introduce host state names or redefine its fields.
