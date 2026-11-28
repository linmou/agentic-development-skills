"""Domain-agnostic fitting of agent-written hypothesis models.

A hypothesis model is a Python module written by the discovery agent (see
references/model-modules.md). This module only does deterministic numerics:
load the module, fit its declared parameters to observations under the loss the
agent selected, score fit and complexity, and measure how stably the best model
wins under bootstrap resampling. It never chooses a functional form.
"""
from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import least_squares

LOSSES = ("mse", "log_mse", "relative")
_FAILED_RESIDUAL = 1e3


class ModelError(ValueError):
    """Raised when a hypothesis module violates the model-module protocol."""


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_model(path: Path, observable_names: list[str]) -> dict[str, Any]:
    """Import an agent-written model module and validate its protocol fields."""
    path = Path(path)
    if not path.is_file():
        raise ModelError(f"model file not found: {path}")
    mod_name = f"autoscilab_model_{abs(hash(str(path.resolve())))}_{path.stat().st_mtime_ns}"
    spec = importlib.util.spec_from_file_location(mod_name, path)
    if spec is None or spec.loader is None:
        raise ModelError(f"cannot import model file: {path}")
    module = importlib.util.module_from_spec(spec)
    try:
        sys.modules[mod_name] = module
        spec.loader.exec_module(module)
    except Exception as exc:  # agent code may raise anything
        raise ModelError(f"{path.name}: import failed: {exc}") from exc
    finally:
        sys.modules.pop(mod_name, None)

    structure = getattr(module, "STRUCTURE", None)
    if not isinstance(structure, str) or not structure.strip():
        raise ModelError(f"{path.name}: STRUCTURE must be a non-empty string")
    predicts = getattr(module, "PREDICTS", None)
    if not isinstance(predicts, (list, tuple)) or not predicts:
        raise ModelError(f"{path.name}: PREDICTS must be a non-empty list of observable names")
    unknown = [o for o in predicts if o not in observable_names]
    if unknown:
        raise ModelError(f"{path.name}: PREDICTS names unknown observables {unknown}")
    predict = getattr(module, "predict", None)
    if not callable(predict):
        raise ModelError(f"{path.name}: predict(inputs, params) function is required")

    raw_params = getattr(module, "PARAMETERS", {})
    if not isinstance(raw_params, dict):
        raise ModelError(f"{path.name}: PARAMETERS must be a dict")
    params: dict[str, dict[str, Any]] = {}
    for name, cfg in raw_params.items():
        if not isinstance(cfg, dict) or "bounds" not in cfg:
            raise ModelError(f"{path.name}: parameter {name!r} needs a dict with 'bounds'")
        lo, hi = (float(v) for v in cfg["bounds"])
        if not (math.isfinite(lo) and math.isfinite(hi) and lo < hi):
            raise ModelError(f"{path.name}: parameter {name!r} bounds must be finite with lo < hi")
        scale = cfg.get("scale", "linear")
        if scale not in ("linear", "log"):
            raise ModelError(f"{path.name}: parameter {name!r} scale must be 'linear' or 'log'")
        if scale == "log" and lo <= 0:
            raise ModelError(f"{path.name}: log-scale parameter {name!r} needs lo > 0")
        init = float(cfg.get("init", math.sqrt(lo * hi) if scale == "log" else 0.5 * (lo + hi)))
        init = min(max(init, lo), hi)
        params[name] = {"bounds": [lo, hi], "scale": scale, "init": init}

    return {
        "path": str(path),
        "structure": " ".join(structure.split()),
        "predicts": list(predicts),
        "parameters": params,
        "predict": predict,
        "source": path.read_text(encoding="utf-8"),
    }


# ---------------------------------------------------------------------------
# Parameter transforms
# ---------------------------------------------------------------------------

def _to_internal(model: dict[str, Any], values: dict[str, float]) -> np.ndarray:
    out = []
    for name, cfg in model["parameters"].items():
        v = float(values[name])
        out.append(math.log(v) if cfg["scale"] == "log" else v)
    return np.array(out, dtype=float)


def _from_internal(model: dict[str, Any], vec: np.ndarray) -> dict[str, float]:
    out: dict[str, float] = {}
    for (name, cfg), z in zip(model["parameters"].items(), vec):
        out[name] = float(math.exp(z)) if cfg["scale"] == "log" else float(z)
    return out


def _internal_bounds(model: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    lo, hi = [], []
    for cfg in model["parameters"].values():
        a, b = cfg["bounds"]
        if cfg["scale"] == "log":
            a, b = math.log(a), math.log(b)
        lo.append(a)
        hi.append(b)
    return np.array(lo, dtype=float), np.array(hi, dtype=float)


# ---------------------------------------------------------------------------
# Prediction and residuals
# ---------------------------------------------------------------------------

def predict(model: dict[str, Any], inputs: dict[str, np.ndarray], params: dict[str, float]) -> dict[str, np.ndarray]:
    """Call the agent model and coerce its outputs to float arrays of the batch length."""
    n = len(next(iter(inputs.values()))) if inputs else 0
    raw = model["predict"](inputs, dict(params))
    if not isinstance(raw, dict):
        raise ModelError(f"{Path(model['path']).name}: predict must return a dict of observable arrays")
    out: dict[str, np.ndarray] = {}
    for obs in model["predicts"]:
        if obs not in raw:
            raise ModelError(f"{Path(model['path']).name}: predict output is missing observable {obs!r}")
        arr = np.asarray(raw[obs], dtype=float)
        if arr.ndim == 0:
            arr = np.full(n, float(arr))
        if arr.shape != (n,):
            raise ModelError(f"{Path(model['path']).name}: prediction for {obs!r} has shape {arr.shape}, expected ({n},)")
        out[obs] = arr
    return out


def observable_scales(observations: list[dict[str, Any]], observable_names: list[str]) -> dict[str, float]:
    """Standard deviation of each observable across the data; used to make `mse` residuals unit-free."""
    scales: dict[str, float] = {}
    for obs in observable_names:
        vals = np.array([float(o["observables"][obs]) for o in observations], dtype=float)
        s = float(np.std(vals)) if len(vals) > 1 else 0.0
        scales[obs] = s if s > 0 else max(float(np.mean(np.abs(vals))) if len(vals) else 1.0, 1.0)
    return scales


def residual_vector(
    loss: str,
    predicted: dict[str, np.ndarray],
    observed: dict[str, np.ndarray],
    scales: dict[str, float],
    weights: dict[str, float],
    relative_floor: float,
) -> np.ndarray:
    parts = []
    for obs, pred in predicted.items():
        y = observed[obs]
        w = math.sqrt(float(weights.get(obs, 1.0)))
        if loss == "mse":
            r = (pred - y) / scales[obs]
        elif loss == "log_mse":
            ok = (pred > 0) & (y > 0)
            r = np.full(len(y), _FAILED_RESIDUAL)
            r[ok] = np.log(pred[ok]) - np.log(y[ok])
        elif loss == "relative":
            r = (pred - y) / np.maximum(np.abs(y), relative_floor)
        else:
            raise ValueError(f"unknown loss {loss!r}")
        r = np.where(np.isfinite(r), r, _FAILED_RESIDUAL)
        parts.append(w * r)
    return np.concatenate(parts) if parts else np.zeros(0)


def stack_inputs(observations: list[dict[str, Any]], input_specs: list[dict[str, Any]]) -> dict[str, np.ndarray]:
    out: dict[str, np.ndarray] = {}
    for spec in input_specs:
        name = spec["name"]
        vals = [o["inputs"][name] for o in observations]
        out[name] = np.array(vals, dtype=object) if spec["kind"] == "categorical" else np.array(vals, dtype=float)
    return out


def stack_observed(observations: list[dict[str, Any]], names: list[str]) -> dict[str, np.ndarray]:
    return {n: np.array([float(o["observables"][n]) for o in observations], dtype=float) for n in names}


# ---------------------------------------------------------------------------
# Fitting
# ---------------------------------------------------------------------------

def fit_model(
    model: dict[str, Any],
    inputs: dict[str, np.ndarray],
    observed: dict[str, np.ndarray],
    settings: dict[str, Any],
    *,
    rng: np.random.Generator,
    restarts: int,
    warm_start: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Multi-start bounded least squares on the agent-selected loss. Returns params and fit metrics."""
    loss = settings["loss"]
    scales = settings["scales"]
    weights = settings.get("observable_weights", {})
    rel_floor = float(settings.get("relative_floor", 1e-12))
    obs_subset = {k: observed[k] for k in model["predicts"]}

    def resid(vec: np.ndarray) -> np.ndarray:
        try:
            pred = predict(model, inputs, _from_internal(model, vec))
        except ModelError:
            raise
        except Exception:
            n_res = sum(len(v) for v in obs_subset.values())
            return np.full(n_res, _FAILED_RESIDUAL)
        return residual_vector(loss, pred, obs_subset, scales, weights, rel_floor)

    names = list(model["parameters"])
    if not names:
        r = resid(np.zeros(0))
        best_vec, best_cost = np.zeros(0), float(np.mean(r**2)) if len(r) else 0.0
    else:
        lo, hi = _internal_bounds(model)
        starts = [_to_internal(model, warm_start) if warm_start else _to_internal(model, {k: c["init"] for k, c in model["parameters"].items()})]
        for _ in range(max(restarts - 1, 0)):
            starts.append(rng.uniform(lo, hi))
        best_vec, best_cost = None, float("inf")
        for x0 in starts:
            x0 = np.clip(x0, lo, hi)
            try:
                res = least_squares(resid, x0, bounds=(lo, hi), method="trf", max_nfev=400 * (len(names) + 1))
            except ModelError:
                raise
            except Exception:
                continue
            cost = float(np.mean(res.fun**2)) if len(res.fun) else 0.0
            if math.isfinite(cost) and cost < best_cost:
                best_vec, best_cost = res.x.copy(), cost
        if best_vec is None:
            best_vec = np.clip(starts[0], lo, hi)
            best_cost = float(np.mean(resid(best_vec) ** 2))

    params = _from_internal(model, best_vec) if names else {}
    pred = predict(model, inputs, params)
    per_obs = {}
    for obs in model["predicts"]:
        r = residual_vector(loss, {obs: pred[obs]}, {obs: obs_subset[obs]}, scales, weights, rel_floor)
        per_obs[obs] = float(np.mean(r**2)) if len(r) else 0.0
    n_res = int(sum(len(v) for v in obs_subset.values()))
    k = len(names)
    floor = float(settings.get("noise_floor", 1e-12))
    bic = float(n_res * math.log(max(best_cost, floor)) + k * math.log(max(n_res, 2)))
    at_bound = [
        n for n, cfg in model["parameters"].items()
        if math.isclose(params[n], cfg["bounds"][0], rel_tol=1e-6, abs_tol=1e-12)
        or math.isclose(params[n], cfg["bounds"][1], rel_tol=1e-6, abs_tol=1e-12)
    ]
    return {
        "params": params,
        "loss_value": best_cost,
        "per_observable_loss": per_obs,
        "n_residuals": n_res,
        "n_parameters": k,
        "bic": bic,
        "params_at_bounds": at_bound,
        "predictions": {o: [float(v) for v in pred[o]] for o in model["predicts"]},
    }


def bootstrap_selection_stability(
    models: dict[str, dict[str, Any]],
    fits: dict[str, dict[str, Any]],
    observations: list[dict[str, Any]],
    input_specs: list[dict[str, Any]],
    settings: dict[str, Any],
    *,
    n_boot: int,
    rng: np.random.Generator,
) -> dict[str, float]:
    """Fraction of bootstrap resamples in which each hypothesis has the lowest BIC.

    Each resample redraws observations with replacement and refits every
    hypothesis warm-started from its full-data parameters. Hypotheses must
    predict the same observables for BIC to be comparable; the caller checks.
    """
    ids = list(models)
    wins = {h: 0 for h in ids}
    n = len(observations)
    valid = 0
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        sample = [observations[i] for i in idx]
        x = stack_inputs(sample, input_specs)
        y = stack_observed(sample, sorted({o for m in models.values() for o in m["predicts"]}))
        bics = {}
        for h in ids:
            try:
                f = fit_model(models[h], x, y, settings, rng=rng, restarts=1, warm_start=fits[h]["params"] or None)
                bics[h] = f["bic"]
            except Exception:
                bics[h] = float("inf")
        best = min(bics, key=lambda h: bics[h])
        if math.isfinite(bics[best]):
            wins[best] += 1
            valid += 1
    return {h: (wins[h] / valid if valid else 0.0) for h in ids}
