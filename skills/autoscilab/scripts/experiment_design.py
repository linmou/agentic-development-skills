"""Domain-agnostic experiment selection over agent-proposed search regions.

The agent proposes where to look (regions or explicit points); this module
samples candidates inside those regions, scores each candidate by how much the
fitted rival hypotheses disagree there (disambiguate mode) or by how sensitive
the leading hypothesis is to its own parameters (refine mode), and picks a
spread-out batch. It never decides which inputs matter or what an input means.
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np

from model_fitting import predict

DIVERSITY_LENGTH = 0.1  # normalized-input distance over which already-picked points suppress neighbours


def sample_region(
    region: dict[str, Any],
    input_specs: list[dict[str, Any]],
    n: int,
    rng: np.random.Generator,
) -> list[dict[str, Any]]:
    """Sample candidates in a region. Inputs the region does not mention span their full declared domain."""
    bounds = region.get("bounds", {})
    levels = region.get("levels", {})
    fixed = region.get("fixed", {})
    pts: list[dict[str, Any]] = [{} for _ in range(n)]
    for spec in input_specs:
        name = spec["name"]
        if name in fixed:
            for p in pts:
                p[name] = fixed[name]
            continue
        if spec["kind"] == "categorical":
            choices = levels.get(name, spec["levels"])
            for p, i in zip(pts, rng.integers(0, len(choices), size=n)):
                p[name] = choices[int(i)]
            continue
        lo, hi = bounds.get(name, spec["bounds"])
        lo, hi = max(float(lo), spec["bounds"][0]), min(float(hi), spec["bounds"][1])
        if lo > hi:
            raise ValueError(f"region bounds for {name!r} fall outside the declared domain")
        if spec.get("scale") == "log":
            vals = np.exp(rng.uniform(math.log(lo), math.log(hi), size=n))
        else:
            vals = rng.uniform(lo, hi, size=n)
        if spec["kind"] == "integer":
            vals = np.clip(np.round(vals), math.ceil(lo), math.floor(hi))
        for p, v in zip(pts, vals):
            p[name] = int(v) if spec["kind"] == "integer" else float(v)
    return pts


def normalized_coords(points: list[dict[str, Any]], input_specs: list[dict[str, Any]]) -> np.ndarray:
    """Map points to [0, 1]^d (log inputs in log space; categorical as level index)."""
    cols = []
    for spec in input_specs:
        name = spec["name"]
        if spec["kind"] == "categorical":
            levels = spec["levels"]
            denom = max(len(levels) - 1, 1)
            cols.append([levels.index(p[name]) / denom for p in points])
            continue
        lo, hi = spec["bounds"]
        if spec.get("scale") == "log":
            lo, hi = math.log(lo), math.log(hi)
            vals = [math.log(float(p[name])) for p in points]
        else:
            vals = [float(p[name]) for p in points]
        span = hi - lo if hi > lo else 1.0
        cols.append([(v - lo) / span for v in vals])
    return np.array(cols, dtype=float).T if cols else np.zeros((len(points), 0))


def _transform(loss: str, values: np.ndarray, scale: float) -> np.ndarray:
    if loss in ("log_mse", "relative"):
        with np.errstate(divide="ignore", invalid="ignore"):
            out = np.log(np.abs(values))
        return np.where(np.isfinite(out), out, np.nan)
    return values / scale


def _stack(points: list[dict[str, Any]], input_specs: list[dict[str, Any]]) -> dict[str, np.ndarray]:
    out = {}
    for spec in input_specs:
        vals = [p[spec["name"]] for p in points]
        out[spec["name"]] = np.array(vals, dtype=object) if spec["kind"] == "categorical" else np.array(vals, dtype=float)
    return out


def predictions_by_hypothesis(
    models: dict[str, dict[str, Any]],
    params: dict[str, dict[str, float]],
    points: list[dict[str, Any]],
    input_specs: list[dict[str, Any]],
) -> dict[str, dict[str, np.ndarray]]:
    x = _stack(points, input_specs)
    out = {}
    for h, m in models.items():
        try:
            out[h] = predict(m, x, params[h])
        except Exception:
            continue
    return out


def disagreement_scores(
    preds: dict[str, dict[str, np.ndarray]],
    loss: str,
    scales: dict[str, float],
    n_points: int,
) -> np.ndarray:
    """Mean over shared observables of the across-hypothesis variance of transformed predictions."""
    if len(preds) < 2:
        return np.zeros(n_points)
    shared = set.intersection(*(set(p) for p in preds.values()))
    if not shared:
        return np.zeros(n_points)
    per_obs = []
    for obs in sorted(shared):
        mat = np.vstack([_transform(loss, preds[h][obs], scales.get(obs, 1.0)) for h in preds])
        with np.errstate(invalid="ignore"):
            per_obs.append(np.nanvar(mat, axis=0))
    score = np.nanmean(np.vstack(per_obs), axis=0)
    return np.where(np.isfinite(score), score, 0.0)


def sensitivity_scores(
    model: dict[str, Any],
    params: dict[str, float],
    points: list[dict[str, Any]],
    input_specs: list[dict[str, Any]],
    loss: str,
    scales: dict[str, float],
    rel_step: float = 0.05,
) -> np.ndarray:
    """Sum over parameters of squared change in transformed predictions per small parameter step."""
    x = _stack(points, input_specs)
    base = predict(model, x, params)
    total = np.zeros(len(points))
    for name, cfg in model["parameters"].items():
        p2 = dict(params)
        lo, hi = cfg["bounds"]
        if cfg["scale"] == "log":
            p2[name] = min(max(params[name] * math.exp(rel_step * (math.log(hi) - math.log(lo))), lo), hi)
        else:
            p2[name] = min(max(params[name] + rel_step * (hi - lo), lo), hi)
        if p2[name] == params[name]:
            continue
        try:
            bumped = predict(model, x, p2)
        except Exception:
            continue
        for obs in model["predicts"]:
            d = _transform(loss, bumped[obs], scales.get(obs, 1.0)) - _transform(loss, base[obs], scales.get(obs, 1.0))
            total += np.where(np.isfinite(d), d**2, 0.0)
    return total


def greedy_diverse_batch(scores: np.ndarray, coords: np.ndarray, k: int) -> list[int]:
    """Pick k indices by score, damping candidates close to points already picked."""
    work = scores.astype(float).copy()
    chosen: list[int] = []
    for _ in range(min(k, len(work))):
        i = int(np.argmax(work))
        if work[i] <= -np.inf:
            break
        chosen.append(i)
        if coords.shape[1]:
            d2 = np.sum((coords - coords[i]) ** 2, axis=1)
            work = work * (1.0 - np.exp(-d2 / (2 * DIVERSITY_LENGTH**2)))
        work[i] = -np.inf
    return chosen


def one_factor_contrasts(
    observations: list[dict[str, Any]],
    input_specs: list[dict[str, Any]],
    observable_names: list[str],
    limit: int = 40,
) -> list[dict[str, Any]]:
    """Observation pairs that differ in exactly one input, with the observed change in every observable."""
    names = [s["name"] for s in input_specs]
    out: list[dict[str, Any]] = []
    for i in range(len(observations)):
        for j in range(i + 1, len(observations)):
            a, b = observations[i]["inputs"], observations[j]["inputs"]
            diff = [n for n in names if a[n] != b[n]]
            if len(diff) != 1:
                continue
            n = diff[0]
            changes = {}
            for obs in observable_names:
                ya, yb = float(observations[i]["observables"][obs]), float(observations[j]["observables"][obs])
                changes[obs] = {
                    "from": ya,
                    "to": yb,
                    "ratio": (yb / ya) if ya != 0 else None,
                }
            out.append({"input": n, "from": a[n], "to": b[n], "observations": [observations[i]["id"], observations[j]["id"]], "changes": changes})
            if len(out) >= limit:
                return out
    return out
