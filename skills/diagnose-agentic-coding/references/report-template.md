# Root-Cause Diagnosis Report Template

Use the smallest report that preserves the causal comparison. Omit empty optional sections but never omit the frozen outcome, rival models, ruling, limitations, and next discriminating evidence.

## 1. Frozen diagnostic target

- **Analysis unit:**
- **Intended outcome and success conditions:**
- **Observed deviation:**
- **Attempt/time boundary:**
- **Evidence cutoff:**
- **Decision this diagnosis informs:**

State the one-sentence explanandum.

## 2. Evidence adequacy

Summarize artifacts inspected and material gaps. State whether the diagnosis is full, preliminary, or evidence-limited.

For substantial cases, include a compact ledger:

| ID/time | Direct observation | Role | Source/reliability | Effect on hypotheses |
| --- | --- | --- | --- | --- |

## 3. Competing explanations

| Rank/status | Hypothesis and ontology anchor | Mechanism chain | Supporting evidence | Contrary/anomalous evidence | Discriminating prediction |
| --- | --- | --- | --- | --- | --- |

Include at least three materially different models when plausible. Keep residual `H_other` visible when ontology coverage is uncertain.

## 4. Bounded ruling

State:

- the relatively or jointly leading explanation(s);
- the causal chain actually supported;
- primary, complementary, substitutive, or phase-specific relationships, if supported;
- attribution across model, harness/tools, task/evaluator, environment, and interactions;
- confidence and why;
- what would most likely overturn the ruling.

Do not say “the root cause is” when the evidence only supports a relative lead.

## 5. Corrective implication

Identify the smallest intervention predicted to disrupt each leading mechanism. Separate:

- immediate containment;
- mechanism-targeted correction;
- recurrence prevention;
- verification that the intervention changed the predicted mechanism rather than merely the outcome.

Only implement changes if the user requested remediation.

## 6. Ontology sufficiency

- **Coverage:** sufficient or insufficient, with reason.
- **Resolution:** sufficient or insufficient for the intended decision.
- **Traversal performed:** existing branches expanded temporarily.
- **Adaptation proposal:** none, vertical refinement, horizontal expansion, relation revision, or configuration revision.
- **Incremental value:** new prediction or intervention distinction enabled.
- **Overlap risk:** relation to existing concepts.
- **Human decision requested:** reject, revise, retain case-locally, or promote to core.

Never silently modify the ontology.

## 7. Stop condition and next evidence

- **Why diagnosis stopped:**
- **Highest-value next discriminating evidence:**
- **Expected ranking/action change:**
- **Cost, delay, or risk:**
- **Residual unknowns and limitations:**

## Concise response form

For a small case, use:

1. Frozen outcome.
2. Three rival explanations with ontology anchors and one-line mechanisms.
3. Relative ruling with evidence for and against.
4. Highest-value next test.
5. Ontology sufficiency and any human-reviewed adaptation proposal.
