# `autoscilab_engine.py` CLI reference

Run `<skill-root>/scripts/autoscilab_engine.py` with Python 3.10+ providing `numpy` and `scipy`. Every subcommand prints one JSON object. Exit codes: `0` ok, `1` error or failed check, `2` batch exceeds the remaining budget (nothing queried).

Workspace files under `<workdir>`: `environment.json`, `state.json`, `observations.json`, `models/<id>.py` (yours), `fits.json`, `memory.json`, `history.jsonl` (append-only ledger), `final_result.json`.

JSON arguments accept inline text (`--x-json '...'`) or a file (`--x-file path`).

## `validate-env` / `init`

```bash
python3 <engine> validate-env --spec-file environment.json
python3 <engine> init --workdir <dir> --spec-file environment.json [--confidence-threshold 0.9] [--force]
```

`init` validates the spec ([environment-spec.md](environment-spec.md)), creates `models/`, and resets the ledger. `--confidence-threshold` is τ for the bootstrap gate.

## `observe`

```bash
# oracle configured: list of input points
python3 <engine> observe --workdir <dir> --experiments-json '[{"length": 1.0, "amplitude": 0.2, "brake_gain": 0.0, "medium": "air"}]'
# no oracle: manual measurements
python3 <engine> observe --workdir <dir> --experiments-json '[{"inputs": {...}, "observables": {"period": 2.01}}]'
```

Checks every input against its declared kind and bounds and the batch against the remaining budget before querying. Manual records are refused when an oracle is configured. When a point matches one selected by the last `acquire`, `prediction_checks` lists each hypothesis's pre-registered prediction beside the observed value.

## `status`

```bash
python3 <engine> status --workdir <dir> [--max-rows 60]
```

Budget, rounds, mode, confidence, last fit ranking, memory, model files on disk, `one_factor_contrasts` (observation pairs differing in exactly one input, with the change in every observable), and the data table.

## `cluster`

```bash
python3 <engine> cluster --workdir <dir> --models h1,h2,h3,h4,h5 [--prev-entropy 1.37] [--k-sampled 10] [--k-max 20] [--entropy-tol 0.1]
python3 <engine> cluster --workdir <dir> --structures-json '["...", "..."]'
```

Groups proposals by `STRUCTURE` and reports Shannon entropy over the groups. `converged` is true when `|ΔH| < entropy-tol` against `--prev-entropy` or when `k-sampled ≥ k-max`.

## `fit`

```bash
python3 <engine> fit --workdir <dir> --models h1,h2,h3 --loss log_mse \
  [--noise-floor 1e-12] [--relative-floor 1e-12] [--observable-weights-json '{"period": 1.0}'] \
  [--restarts 8] [--n-boot 20] [--seed 0]
```

For each model: multi-start bounded least squares on the declared loss, `loss_value` (mean squared residual), `per_observable_loss`, `bic = n·ln(max(loss, noise_floor)) + k·ln(n)`, and `params_at_bounds` (widen those bounds or rethink the form). With ≥ 2 models, `conf_boot` is the fraction of bootstrap resamples (observations redrawn with replacement, every model refitted) in which that model has the lowest BIC. `confidence` is the top model's `conf_boot`; `acquisition_mode` is `refine` when `confidence ≥ τ`, otherwise `disambiguate`.

## `acquire`

```bash
python3 <engine> acquire --workdir <dir> --n-experiments 4 [--mode disambiguate|refine] [--models h1,h2] \
  --regions-json '[{"bounds": {"amplitude": [0.8, 1.2]}, "fixed": {"medium": "air"}, "levels": {}, "rationale": "large-amplitude regime"}]' \
  [--points-json '[{...full input point...}]'] [--n-candidates 256] [--seed 0]
```

Samples `n-candidates` points per region (inputs a region does not mention span their full declared domain; `fixed` pins values; `levels` restricts categorical choices) plus any explicit points. Scoring uses the latest fit:

- `disambiguate`: variance across hypotheses of their predictions, transformed to match the loss (log for `log_mse`/`relative`, standardized for `mse`), averaged over observables.
- `refine`: squared change in the leading model's transformed predictions per small step in each parameter.

Picks a batch greedily, damping candidates near points already picked. Returns each selected point with every hypothesis's prediction and stores them for the next `observe` to compare.

## `memory`

```bash
python3 <engine> memory --workdir <dir> --memory-json '{
  "validated_hypotheses": [{"hypothesis": "h2", "evidence": "obs 14-17 within 2% of prediction"}],
  "falsified_hypotheses": [{"hypothesis": "h1", "evidence": "predicted 3.1 at obs 15, observed 0.4"}],
  "uncertain_hypotheses": [],
  "active_inputs": ["length", "amplitude"], "inactive_inputs": [], "untested_inputs": ["medium"],
  "notes": ["loss log_mse: multiplicative noise suspected from replicate spread"]
}'
```

Replaces each given key; keys are limited to the ones above.

## `finalize` / `audit`

```bash
python3 <engine> finalize --workdir <dir> --selection-json '{"model": "h2", "mechanism": <in target.output_format>, "rationale": "..."}'
python3 <engine> audit --workdir <dir> [--final-model h2]
```

`finalize` refits the chosen model on all observations with the last fit settings, runs the audit, and writes `final_result.json` (`status` `completed` only when every audit check passes). Audit checks: budget respected, observations match the hashes logged at observe time, ≥ 2 observe rounds, a fit round comparing ≥ 2 distinct structures, an observe following an acquire, ≥ 1 memory update, and (at finalize) the chosen model appears in a fit round.
