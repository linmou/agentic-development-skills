# Evidence Ledger Protocol

**Intent:** Keep an auditable distinction between observation, inference, and incomplete search when comparing causal explanations.

Use this protocol for standard or full studies. Keep it in working notes or an appendix; do not expose identifiers or internal audit detail unless useful to the requester.

## 1. Outcome record

| Field | Record |
|---|---|
| Outcome | The exact event, change, state, or difference to explain |
| Unit and population | Who or what the outcome concerns |
| Scope | Time, geography, setting, and included/excluded cases |
| Measurement | Definition, source, denominator, and known limitations |
| Decision | The user decision this research is meant to inform |
| Cutoff | Latest evidence date considered |

Keep correlated outcomes in separate records. Update the record rather than silently broadening it.

## 2. Model register

| Model | Mechanism chain | Discriminating predictions | Potential refuter | Boundaries | Initial plausibility |
|---|---|---|---|---|---|
| M1 | condition → action → intermediate → outcome | | | | |

Each model must be capable of being wrong. State why any reasonable alternative was excluded from the register.

## 3. Evidence record

| Item | Source and control relationship | Event time / publication time | Direct claim supported | Role | Model links | Reliability and scope limits |
|---|---|---|---|---|---|---|
| E1 | | | | antecedent / process / outcome measure / later observation / time uncertain | M1… | |

Use the narrowest claim directly entailed by a source. A source controlled by the analysed actor may prove its own statement, not the effect it attributes to itself.

## 4. Symmetric search record

For every material model, record all four arms:

| Model | Arm | Search target and sources | Period and scope | Depth / detection opportunity | Search-arm status | Result and limitation |
|---|---|---|---|---|---|---|
| M1 | support | | | | found / none found / limited / not run | |
| M1 | refutation | | | | | |
| M1 | alternative | | | | | |
| M1 | failure or anomaly | | | | | |

`None found` reports only a completed search with a defined, sufficiently observable source set. It is otherwise `limited` or `not run`, and the fact remains unknown.

## 5. Process and comparison record

| Model | Required transition | Observed evidence | Missing link | Comparator or counterfactual | Confounds / transport limit | Assessment |
|---|---|---|---|---|---|---|
| M1 | action → adoption | | | | | complete / partial / unavailable |

Separate a complete-looking story from evidence that the transition actually occurred. State why a comparison is comparable before treating it as causal evidence.

## 6. Comparison and stop record

| Model | Coverage | Prediction fit | Refutation / anomaly fit | Process evidence | Counterfactual evidence | Source independence | Current model-ruling status | Residual / next test |
|---|---|---|---|---|---|---|---|---|
| M1 | | | | | | | | |

Stop only at the stated cutoff and with a disclosed reason: adequate current coverage, public-evidence saturation, or a preliminary stop. A new material source, changed outcome definition, or unresolved anomaly reopens the affected row.
