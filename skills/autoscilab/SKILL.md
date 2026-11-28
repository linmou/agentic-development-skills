---
name: autoscilab
description: >
  Closed-loop scientific mechanism discovery under a finite experiment budget: competing
  hypotheses written as fit-able models, experiments placed where rivals disagree, and a
  bootstrap confidence gate. Use when recovering a governing law, rate equation, causal
  structure or other mechanism from a queryable experimental system (simulator, instrument
  or lab assay), or when another skill needs adaptive experiment design to separate rival
  mechanisms.
---

# AutoSciLab

Recover an unknown mechanism from an experimental system you can only query, within a fixed budget. Work like a **lab notebook**: every hypothesis is written down as an executable model, every experiment is chosen to embarrass at least one of them, and every result is ledgered before you interpret it.

The split of work:

- **The environment** is whatever is being studied. You meet it only through `environment.json` and oracle responses ([references/environment-spec.md](references/environment-spec.md)). Learn about the system exclusively through those two channels; simulator code, task metadata and answer keys stay unread even when they sit on the same disk.
- **You** own the science: what to measure first, which mechanisms to write, how they are parameterized, which loss fits the noise, where to look next, and which mechanism wins.
- **The engine** (`<skill-root>/scripts/autoscilab_engine.py`, [references/cli-reference.md](references/cli-reference.md)) owns bookkeeping and numerics: budget, ledger, oracle calls, parameter fitting, BIC, bootstrap gate, disagreement scoring and the protocol audit. It holds no model of any domain.

## Setup

1. Get the environment spec. If the system already provides an `autoscilab-env/1` spec, use it. Otherwise write an adapter from the system's public interface, following "Writing an adapter" in [references/environment-spec.md](references/environment-spec.md), and keep it outside the skill folder.
2. Run `validate-env`, then `init --workdir <dir>`.
3. Read [references/model-modules.md](references/model-modules.md) before writing the first hypothesis.

**Done when:** `<workdir>/state.json` exists, `validate-env` reports `valid: true`, and you can state the target's `output_format` in one sentence.

## Discovery loop

Run steps 1–6 once, repeating steps 2–5 for 4–6 rounds of roughly 15–25 % of the budget each, until the budget is spent or one mechanism has survived discriminating experiments with `confidence ≥ τ`.

### 1. Explore

Spend about 15–30 % of the budget on an initial design you justify from the environment description: a baseline point plus variation of each input across its declared range, enough that every input's effect on every observable has at least one contrast (`status` lists one-factor contrasts).

**Done when:** every input appears in at least one contrast in `status`, or the inputs you skipped are listed in `untested_inputs` with the reason in `notes`.

### 2. Hypothesize (`GenHyp`)

Write at least three structurally distinct mechanisms as model modules in `<workdir>/models/`, each consistent with the data so far and none already recorded as falsified (unless new inputs became active). Distinct means different `STRUCTURE`, not different parameter values.

When structural uncertainty is high and subagents are available, sample proposals in batches of K = 5 from independent proposers (up to K_max = 20) and run `cluster` after each batch until entropy stabilizes (`converged: true`); keep one model per surviving cluster.

**Done when:** at least three model files with distinct `STRUCTURE` exist for this round and each one's form is justified in a sentence you can put in `memory` notes.

### 3. Fit and gate (`RefineHyp` + `ConfGate`)

Run `fit` on the current hypotheses with the loss and noise floor your noise assumptions call for (see "Choosing fit settings" in [references/model-modules.md](references/model-modules.md)). Read `bic`, `per_observable_loss`, `params_at_bounds` and `conf_boot`. A parameter pinned at a bound means the form or the bounds are wrong; fix the model and refit rather than accept it.

**Done when:** every current hypothesis has a fit with no unexplained `params_at_bounds`, and the gate has set `acquisition_mode`.

### 4. Experiment (`Acquire`)

Propose 1–4 search regions where your hypotheses predict qualitatively different behaviour (extremes, corners, interactions, regimes where one mechanism saturates and another does not), run `acquire`, then `observe` the selected points. In `refine` mode, regions should target where the leading mechanism's parameters are least constrained.

**Done when:** the selected batch is observed and you have read `prediction_checks`: which hypotheses predicted the new points and which missed.

### 5. Update the scoreboard (`UpdateMemory`)

Run `memory`: move hypotheses whose pre-registered predictions failed into `falsified_hypotheses` with the observation that refuted them; keep survivors as `validated_hypotheses` (stable, `conf_boot` high) or `uncertain_hypotheses` (fit well but unstable); update input classifications; note every modelling assumption you changed and why.

**Done when:** every hypothesis fitted this round appears in exactly one scoreboard list with evidence citing observation ids.

### 6. Finalize

When the budget is spent (or the stopping condition holds), refit the surviving candidates together once more, choose by survival of discriminating experiments, bootstrap stability and BIC, translate the winner into `target.output_format`, and run `finalize`.

**Done when:** `final_result.json` has `status: "completed"` and `audit.passed: true`. If the audit fails, the failed checks name the missing loop step; run that step (within the remaining budget) and finalize again.

## Invocation contract

Direct user requests run the workflow above. Another skill invokes `autoscilab` through [contract.json](contract.json) (`skill-contract/1`).
