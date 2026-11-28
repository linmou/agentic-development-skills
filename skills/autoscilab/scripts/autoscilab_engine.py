#!/usr/bin/env python3
"""AutoSciLab engine: domain-agnostic bookkeeping and numerics for closed-loop discovery.

The engine owns the workspace ledger, budget enforcement, the oracle call
protocol, fitting of agent-written hypothesis models, bootstrap selection
stability, hypothesis-conditioned experiment scoring, and the protocol audit.
It carries no model of any scientific domain: the environment is described by
an `autoscilab-env/1` spec (references/environment-spec.md) and every
hypothesis is a model module the agent writes (references/model-modules.md).

Every subcommand prints one JSON object to stdout.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from experiment_design import (  # noqa: E402
    disagreement_scores,
    greedy_diverse_batch,
    normalized_coords,
    one_factor_contrasts,
    predictions_by_hypothesis,
    sample_region,
    sensitivity_scores,
)
from model_fitting import (  # noqa: E402
    LOSSES,
    ModelError,
    bootstrap_selection_stability,
    fit_model,
    load_model,
    observable_scales,
    stack_inputs,
    stack_observed,
)

SPEC_VERSION = "autoscilab-env/1"
DEFAULT_CONFIDENCE_THRESHOLD = 0.9
ORACLE_TIMEOUT_S = 600


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

class EngineError(Exception):
    def __init__(self, message: str, code: int = 1, **extra: Any):
        super().__init__(message)
        self.code = code
        self.extra = extra


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _save(path: Path, payload: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=False), encoding="utf-8")
    tmp.replace(path)


def _append_history(workdir: Path, event: dict[str, Any]) -> None:
    event = {"time": _now(), **event}
    with (workdir / "history.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, sort_keys=True) + "\n")


def _history(workdir: Path) -> list[dict[str, Any]]:
    path = workdir / "history.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _record_hash(record: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(record, sort_keys=True).encode("utf-8")).hexdigest()


def _json_arg(raw: str | None, file_path: str | None, what: str) -> Any:
    if file_path:
        return json.loads(Path(file_path).read_text(encoding="utf-8"))
    if raw is None:
        raise EngineError(f"{what} is required (pass the JSON inline or as a file)")
    return json.loads(raw)


def _emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, default=_json_default))


def _json_default(o: Any) -> Any:
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(f"not JSON serializable: {type(o)}")


# ---------------------------------------------------------------------------
# Environment spec
# ---------------------------------------------------------------------------

def validate_environment(spec: Any) -> list[str]:
    """Return a list of problems with an autoscilab-env/1 spec (empty when valid)."""
    errs: list[str] = []
    if not isinstance(spec, dict):
        return ["environment spec must be a JSON object"]
    if spec.get("spec_version") != SPEC_VERSION:
        errs.append(f"spec_version must be {SPEC_VERSION!r}")
    if not isinstance(spec.get("goal"), str) or not spec["goal"].strip():
        errs.append("goal must be a non-empty string")
    budget = spec.get("budget")
    if not isinstance(budget, int) or isinstance(budget, bool) or budget <= 0:
        errs.append("budget must be a positive integer")

    inputs = spec.get("inputs")
    if not isinstance(inputs, list) or not inputs:
        errs.append("inputs must be a non-empty list")
        inputs = []
    seen: set[str] = set()
    for i, inp in enumerate(inputs):
        where = f"inputs[{i}]"
        if not isinstance(inp, dict) or not isinstance(inp.get("name"), str) or not inp["name"]:
            errs.append(f"{where}.name must be a non-empty string")
            continue
        name = inp["name"]
        if name in seen:
            errs.append(f"duplicate input name {name!r}")
        seen.add(name)
        kind = inp.get("kind", "continuous")
        if kind not in ("continuous", "integer", "categorical"):
            errs.append(f"{where}.kind must be continuous, integer or categorical")
            continue
        if kind == "categorical":
            levels = inp.get("levels")
            if not isinstance(levels, list) or len(levels) < 2:
                errs.append(f"{where}.levels must list at least two values")
            continue
        b = inp.get("bounds")
        if not (isinstance(b, list) and len(b) == 2 and all(isinstance(v, (int, float)) for v in b) and b[0] < b[1]):
            errs.append(f"{where}.bounds must be [lo, hi] with lo < hi")
            continue
        scale = inp.get("scale", "linear")
        if scale not in ("linear", "log"):
            errs.append(f"{where}.scale must be linear or log")
        elif scale == "log" and b[0] <= 0:
            errs.append(f"{where}: log scale needs lo > 0")
        if inp.get("role", "control") not in ("control", "intervention"):
            errs.append(f"{where}.role must be control or intervention")

    observables = spec.get("observables")
    if not isinstance(observables, list) or not observables:
        errs.append("observables must be a non-empty list")
        observables = []
    oseen: set[str] = set()
    for i, ob in enumerate(observables):
        if not isinstance(ob, dict) or not isinstance(ob.get("name"), str) or not ob["name"]:
            errs.append(f"observables[{i}].name must be a non-empty string")
            continue
        if ob["name"] in oseen:
            errs.append(f"duplicate observable name {ob['name']!r}")
        oseen.add(ob["name"])

    oracle = spec.get("oracle")
    if oracle is not None and not (isinstance(oracle, dict) and isinstance(oracle.get("command"), str) and oracle["command"].strip()):
        errs.append("oracle, when present, must be {\"command\": \"...\"}")

    target = spec.get("target")
    if not (isinstance(target, dict) and isinstance(target.get("representation"), str) and target["representation"]
            and isinstance(target.get("output_format"), str) and target["output_format"].strip()):
        errs.append("target must give non-empty representation and output_format strings")
    return errs


def _normalize_environment(spec: dict[str, Any]) -> dict[str, Any]:
    spec = json.loads(json.dumps(spec))
    for inp in spec["inputs"]:
        inp.setdefault("kind", "continuous")
        inp.setdefault("role", "control")
        if inp["kind"] != "categorical":
            inp.setdefault("scale", "linear")
            inp["bounds"] = [float(inp["bounds"][0]), float(inp["bounds"][1])]
    return spec


def _validate_point(point: Any, env: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(point, dict):
        raise EngineError("each experiment must be an object mapping input names to values")
    names = {i["name"] for i in env["inputs"]}
    unknown = sorted(set(point) - names)
    missing = sorted(names - set(point))
    if unknown or missing:
        raise EngineError("experiment inputs do not match the environment", unknown=unknown, missing=missing)
    out: dict[str, Any] = {}
    for spec in env["inputs"]:
        name, v = spec["name"], point[spec["name"]]
        if spec["kind"] == "categorical":
            if v not in spec["levels"]:
                raise EngineError(f"{name}={v!r} is not one of the declared levels")
            out[name] = v
            continue
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(float(v)):
            raise EngineError(f"{name} must be a finite number")
        lo, hi = spec["bounds"]
        if not (lo <= float(v) <= hi):
            raise EngineError(f"{name}={v} is outside the declared bounds [{lo}, {hi}]")
        if spec["kind"] == "integer":
            if float(v) != round(float(v)):
                raise EngineError(f"{name} must be an integer")
            out[name] = int(round(float(v)))
        else:
            out[name] = float(v)
    return out


def _observable_names(env: dict[str, Any]) -> list[str]:
    return [o["name"] for o in env["observables"]]


# ---------------------------------------------------------------------------
# Workspace
# ---------------------------------------------------------------------------

class Workspace:
    def __init__(self, workdir: str):
        self.dir = Path(workdir).resolve()
        self.env_path = self.dir / "environment.json"
        self.state_path = self.dir / "state.json"
        self.obs_path = self.dir / "observations.json"
        self.fits_path = self.dir / "fits.json"
        self.memory_path = self.dir / "memory.json"
        self.models_dir = self.dir / "models"

    def require(self) -> None:
        if not self.state_path.exists():
            raise EngineError(f"{self.dir} is not initialized; run init first")

    @property
    def env(self) -> dict[str, Any]:
        return _load(self.env_path)

    @property
    def state(self) -> dict[str, Any]:
        return _load(self.state_path)

    def save_state(self, state: dict[str, Any]) -> None:
        _save(self.state_path, state)

    @property
    def observations(self) -> list[dict[str, Any]]:
        return _load(self.obs_path, [])

    def model_path(self, model_id: str) -> Path:
        if not model_id or "/" in model_id or "\\" in model_id or model_id.startswith("."):
            raise EngineError(f"invalid model id {model_id!r}; use the file stem of models/<id>.py")
        return self.models_dir / f"{model_id}.py"

    def load_models(self, ids: list[str]) -> dict[str, dict[str, Any]]:
        obs_names = _observable_names(self.env)
        models = {}
        for mid in ids:
            try:
                models[mid] = load_model(self.model_path(mid), obs_names)
            except ModelError as exc:
                raise EngineError(str(exc)) from exc
        return models


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_init(args: argparse.Namespace) -> dict[str, Any]:
    ws = Workspace(args.workdir)
    spec = _json_arg(args.spec_json, args.spec_file, "--spec-json/--spec-file")
    errors = validate_environment(spec)
    if errors:
        raise EngineError("invalid environment spec", errors=errors)
    if ws.state_path.exists() and not args.force:
        raise EngineError(f"{ws.dir} is already initialized (pass --force to start over)")
    ws.dir.mkdir(parents=True, exist_ok=True)
    ws.models_dir.mkdir(exist_ok=True)
    env = _normalize_environment(spec)
    threshold = float(args.confidence_threshold)
    _save(ws.env_path, env)
    _save(ws.obs_path, [])
    _save(ws.memory_path, {
        "validated_hypotheses": [], "falsified_hypotheses": [], "uncertain_hypotheses": [],
        "active_inputs": [], "inactive_inputs": [], "untested_inputs": [i["name"] for i in env["inputs"]],
        "notes": [],
    })
    ws.save_state({
        "budget": env["budget"],
        "queries_used": 0,
        "observe_rounds": 0,
        "confidence_threshold": threshold,
        "confidence": None,
        "acquisition_mode": "disambiguate",
        "fit_settings": None,
        "pending_predictions": [],
    })
    if (ws.dir / "history.jsonl").exists():
        (ws.dir / "history.jsonl").unlink()
    _append_history(ws.dir, {"event": "init", "budget": env["budget"], "confidence_threshold": threshold,
                             "oracle": bool(env.get("oracle"))})
    return {"status": "ok", "workdir": str(ws.dir), "budget": env["budget"],
            "oracle_configured": bool(env.get("oracle")), "models_dir": str(ws.models_dir)}


def _call_oracle(command: str, point: dict[str, Any], obs_names: list[str]) -> dict[str, float]:
    try:
        proc = subprocess.run(
            shlex.split(command), input=json.dumps({"inputs": point}),
            capture_output=True, text=True, timeout=ORACLE_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired as exc:
        raise EngineError("oracle timed out") from exc
    if proc.returncode != 0:
        raise EngineError("oracle returned a non-zero exit code", oracle_stderr=proc.stderr.strip()[-2000:])
    try:
        payload = json.loads(proc.stdout)
        values = payload["observables"]
    except Exception as exc:
        raise EngineError("oracle output must be JSON {\"observables\": {...}}", oracle_stdout=proc.stdout[-2000:]) from exc
    out = {}
    for name in obs_names:
        v = values.get(name) if isinstance(values, dict) else None
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(float(v)):
            raise EngineError(f"oracle output is missing a finite value for observable {name!r}")
        out[name] = float(v)
    return out


def _prediction_check(pending: list[dict[str, Any]], record: dict[str, Any]) -> dict[str, Any] | None:
    for item in pending:
        if item["inputs"] == record["inputs"]:
            check = {}
            for h, preds in item["predictions"].items():
                check[h] = {obs: {"predicted": p, "observed": record["observables"][obs]} for obs, p in preds.items()}
            return check
    return None


def cmd_observe(args: argparse.Namespace) -> dict[str, Any]:
    ws = Workspace(args.workdir)
    ws.require()
    env, state = ws.env, ws.state
    batch = _json_arg(args.experiments_json, args.experiments_file, "--experiments-json/--experiments-file")
    if not isinstance(batch, list) or not batch:
        raise EngineError("experiments must be a non-empty list")
    oracle = env.get("oracle")
    remaining = state["budget"] - state["queries_used"]
    if len(batch) > remaining:
        raise EngineError("batch exceeds the remaining budget; nothing was queried", code=2,
                          batch_size=len(batch), budget_remaining=remaining)

    obs_names = _observable_names(env)
    if oracle:
        points = [_validate_point(p, env) for p in batch]
        manual_values = None
    else:
        points, manual_values = [], []
        for item in batch:
            if not isinstance(item, dict) or "inputs" not in item or "observables" not in item:
                raise EngineError("without an oracle, each item must be {\"inputs\": {...}, \"observables\": {...}}")
            points.append(_validate_point(item["inputs"], env))
            vals = {}
            for name in obs_names:
                v = item["observables"].get(name)
                if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(float(v)):
                    raise EngineError(f"manual record is missing a finite value for observable {name!r}")
                vals[name] = float(v)
            manual_values.append(vals)

    observations = ws.observations
    round_no = state["observe_rounds"] + 1
    new_records, checks, failure = [], [], None
    for i, point in enumerate(points):
        try:
            values = _call_oracle(oracle["command"], point, obs_names) if oracle else manual_values[i]
        except EngineError as exc:
            failure = {"error": str(exc), **exc.extra, "failed_experiment_index": i}
            break
        record = {"id": len(observations) + 1, "round": round_no, "source": "oracle" if oracle else "manual",
                  "inputs": point, "observables": values}
        observations.append(record)
        new_records.append(record)
        check = _prediction_check(state.get("pending_predictions", []), record)
        if check is not None:
            checks.append({"observation": record["id"], "hypotheses": check})

    if new_records:
        _save(ws.obs_path, observations)
        state["queries_used"] += len(new_records)
        state["observe_rounds"] = round_no
        ws.save_state(state)
        _append_history(ws.dir, {"event": "observe", "round": round_no, "source": new_records[0]["source"],
                                 "observation_ids": [r["id"] for r in new_records],
                                 "record_hashes": [_record_hash(r) for r in new_records]})
    result = {
        "status": "ok" if failure is None else "partial",
        "recorded": new_records,
        "queries_used": state["queries_used"],
        "budget_remaining": state["budget"] - state["queries_used"],
        "prediction_checks": checks,
    }
    if failure:
        result["failure"] = failure
    return result


def _format_table(env: dict[str, Any], observations: list[dict[str, Any]], max_rows: int) -> str:
    in_names = [i["name"] for i in env["inputs"]]
    ob_names = _observable_names(env)
    header = ["id", "round", *in_names, *ob_names]
    lines = [" | ".join(header)]
    for rec in observations[-max_rows:]:
        row = [str(rec["id"]), str(rec["round"])]
        row += [f"{rec['inputs'][n]:.6g}" if isinstance(rec["inputs"][n], (int, float)) else str(rec["inputs"][n]) for n in in_names]
        row += [f"{rec['observables'][n]:.6g}" for n in ob_names]
        lines.append(" | ".join(row))
    return "\n".join(lines)


def cmd_status(args: argparse.Namespace) -> dict[str, Any]:
    ws = Workspace(args.workdir)
    ws.require()
    env, state, observations = ws.env, ws.state, ws.observations
    fits = _load(ws.fits_path)
    ranking = None
    if fits:
        ranking = [
            {"model": h, "structure": fits["hypotheses"][h]["structure"], "bic": fits["hypotheses"][h]["bic"],
             "loss_value": fits["hypotheses"][h]["loss_value"], "conf_boot": fits["hypotheses"][h].get("conf_boot")}
            for h in fits["ranking"]
        ]
    return {
        "goal": env["goal"],
        "target": env["target"],
        "queries_used": state["queries_used"],
        "budget": state["budget"],
        "budget_remaining": state["budget"] - state["queries_used"],
        "observe_rounds": state["observe_rounds"],
        "acquisition_mode": state["acquisition_mode"],
        "confidence": state["confidence"],
        "confidence_threshold": state["confidence_threshold"],
        "fit_settings": state["fit_settings"],
        "latest_fit_ranking": ranking,
        "memory": _load(ws.memory_path, {}),
        "models_on_disk": sorted(p.stem for p in ws.models_dir.glob("*.py")),
        "one_factor_contrasts": one_factor_contrasts(observations, env["inputs"], _observable_names(env)),
        "data_table": _format_table(env, observations, args.max_rows),
    }


def cmd_cluster(args: argparse.Namespace) -> dict[str, Any]:
    ws = Workspace(args.workdir)
    ws.require()
    if args.models:
        ids = _split_ids(args.models)
        models = ws.load_models(ids)
        items = [(mid, models[mid]["structure"]) for mid in ids]
    else:
        raw = _json_arg(args.structures_json, args.structures_file, "--models or --structures-json")
        if not isinstance(raw, list) or not raw:
            raise EngineError("structures must be a non-empty list of strings")
        items = [(f"proposal_{i + 1}", " ".join(str(s).split())) for i, s in enumerate(raw)]
    groups: dict[str, list[str]] = {}
    for member, structure in items:
        groups.setdefault(structure, []).append(member)
    total = len(items)
    entropy = -sum((len(m) / total) * math.log2(len(m) / total) for m in groups.values())
    delta = None if args.prev_entropy is None else entropy - args.prev_entropy
    k_sampled = args.k_sampled if args.k_sampled is not None else total
    converged = (delta is not None and abs(delta) < args.entropy_tol) or k_sampled >= args.k_max
    _append_history(ws.dir, {"event": "cluster", "n_proposals": total, "n_clusters": len(groups),
                             "entropy_bits": entropy})
    return {
        "n_proposals": total,
        "clusters": sorted(({"structure": s, "count": len(m), "members": m} for s, m in groups.items()),
                           key=lambda c: -c["count"]),
        "entropy_bits": round(entropy, 4),
        "delta_entropy": None if delta is None else round(delta, 4),
        "converged": converged,
        "stop_reason": None if not converged else ("k_max reached" if k_sampled >= args.k_max else "entropy stabilized"),
    }


def _split_ids(raw: str) -> list[str]:
    raw = raw.strip()
    ids = json.loads(raw) if raw.startswith("[") else [s.strip() for s in raw.split(",")]
    ids = [i for i in ids if i]
    if len(set(ids)) != len(ids):
        raise EngineError("model ids must be unique")
    if not ids:
        raise EngineError("at least one model id is required")
    return ids


def cmd_fit(args: argparse.Namespace) -> dict[str, Any]:
    ws = Workspace(args.workdir)
    ws.require()
    env, state, observations = ws.env, ws.state, ws.observations
    if not observations:
        raise EngineError("no observations to fit; run observe first")
    ids = _split_ids(args.models)
    models = ws.load_models(ids)
    predicted_sets = {tuple(sorted(m["predicts"])) for m in models.values()}
    if len(predicted_sets) > 1:
        raise EngineError("all hypotheses in one fit must predict the same observables so BIC is comparable",
                          predicts={h: m["predicts"] for h, m in models.items()})
    weights = json.loads(args.observable_weights_json) if args.observable_weights_json else {}
    obs_names = _observable_names(env)
    settings = {
        "loss": args.loss,
        "noise_floor": args.noise_floor,
        "relative_floor": args.relative_floor,
        "observable_weights": weights,
        "scales": observable_scales(observations, obs_names),
    }
    if args.loss == "log_mse":
        used = sorted(predicted_sets.pop())
        bad = [o["id"] for o in observations if any(o["observables"][n] <= 0 for n in used)]
        if bad:
            raise EngineError("log_mse needs strictly positive observed values", observation_ids=bad[:20])

    rng = np.random.default_rng(args.seed)
    x = stack_inputs(observations, env["inputs"])
    y = stack_observed(observations, obs_names)
    fits: dict[str, dict[str, Any]] = {}
    for h, m in models.items():
        try:
            fits[h] = fit_model(m, x, y, settings, rng=rng, restarts=args.restarts)
        except ModelError as exc:
            raise EngineError(str(exc)) from exc

    ranking = sorted(fits, key=lambda h: fits[h]["bic"])
    conf: dict[str, float] = {}
    if len(models) >= 2 and args.n_boot > 0 and len(observations) >= 3:
        conf = bootstrap_selection_stability(models, fits, observations, env["inputs"], settings,
                                             n_boot=args.n_boot, rng=rng)
    top = ranking[0]
    confidence = conf.get(top) if conf else None
    threshold = state["confidence_threshold"]
    mode = "refine" if (confidence is not None and confidence >= threshold) else "disambiguate"
    warnings = []
    if len(models) < 2:
        warnings.append("only one hypothesis was fitted; the bootstrap gate needs rivals, so the mode stays disambiguate")
    distinct = len({m["structure"] for m in models.values()})
    if distinct < len(models):
        warnings.append("some hypotheses share the same STRUCTURE string; they count as one structure in the audit")

    hyp_out = {}
    for h in ids:
        hyp_out[h] = {"structure": models[h]["structure"], "predicts": models[h]["predicts"],
                      "conf_boot": conf.get(h), **fits[h],
                      "source_sha256": hashlib.sha256(models[h]["source"].encode()).hexdigest()}
    payload = {
        "round": state["observe_rounds"],
        "n_observations": len(observations),
        "settings": {k: v for k, v in settings.items()},
        "ranking": ranking,
        "confidence": confidence,
        "acquisition_mode": mode,
        "hypotheses": hyp_out,
    }
    _save(ws.fits_path, payload)
    state.update({"confidence": confidence, "acquisition_mode": mode,
                  "fit_settings": {k: v for k, v in settings.items() if k != "scales"}})
    ws.save_state(state)
    _append_history(ws.dir, {"event": "fit", "round": state["observe_rounds"], "models": ids,
                             "structures": {h: models[h]["structure"] for h in ids},
                             "bic": {h: fits[h]["bic"] for h in ids}, "conf_boot": conf,
                             "loss": args.loss, "acquisition_mode": mode,
                             "source_sha256": {h: hyp_out[h]["source_sha256"] for h in ids}})
    summary = {h: {k: hyp_out[h][k] for k in ("structure", "params", "loss_value", "per_observable_loss",
                                              "n_parameters", "bic", "conf_boot", "params_at_bounds")} for h in ids}
    return {"ranking": ranking, "confidence": confidence, "confidence_threshold": threshold,
            "acquisition_mode": mode, "hypotheses": summary, "warnings": warnings}


def cmd_acquire(args: argparse.Namespace) -> dict[str, Any]:
    ws = Workspace(args.workdir)
    ws.require()
    env, state = ws.env, ws.state
    fits = _load(ws.fits_path)
    if not fits:
        raise EngineError("no fitted hypotheses; run fit before acquire")
    ids = _split_ids(args.models) if args.models else list(fits["ranking"])
    missing = [h for h in ids if h not in fits["hypotheses"]]
    if missing:
        raise EngineError("these models were not in the latest fit", models=missing)
    models = ws.load_models(ids)
    params = {h: fits["hypotheses"][h]["params"] for h in ids}
    mode = args.mode or state["acquisition_mode"]
    loss = fits["settings"]["loss"]
    scales = fits["settings"]["scales"]
    rng = np.random.default_rng(args.seed)

    candidates: list[dict[str, Any]] = []
    origin: list[str] = []
    if args.regions_json or args.regions_file:
        regions = _json_arg(args.regions_json, args.regions_file, "regions")
        if not isinstance(regions, list):
            raise EngineError("regions must be a list")
        for r_i, region in enumerate(regions):
            try:
                pts = sample_region(region, env["inputs"], args.n_candidates, rng)
            except ValueError as exc:
                raise EngineError(str(exc)) from exc
            candidates += pts
            origin += [region.get("rationale", f"region_{r_i + 1}")] * len(pts)
    if args.points_json or args.points_file:
        explicit = _json_arg(args.points_json, args.points_file, "points")
        for p in explicit:
            candidates.append(_validate_point(p, env))
            origin.append("explicit point")
    if not candidates:
        raise EngineError("give search regions (--regions-json) and/or explicit candidate points (--points-json)")

    if mode == "refine":
        top = ids[0]
        scores = sensitivity_scores(models[top], params[top], candidates, env["inputs"], loss, scales)
    else:
        if len(ids) < 2:
            raise EngineError("disambiguate mode needs at least two fitted hypotheses")
        preds = predictions_by_hypothesis(models, params, candidates, env["inputs"])
        scores = disagreement_scores(preds, loss, scales, len(candidates))
    coords = normalized_coords(candidates, env["inputs"])
    chosen = greedy_diverse_batch(scores, coords, args.n_experiments)
    chosen_pts = [candidates[i] for i in chosen]
    preds_chosen = predictions_by_hypothesis(models, params, chosen_pts, env["inputs"])
    selected, pending = [], []
    for j, i in enumerate(chosen):
        hp = {h: {obs: float(v[j]) for obs, v in preds_chosen[h].items()} for h in preds_chosen}
        selected.append({"inputs": candidates[i], "score": float(scores[i]), "origin": origin[i],
                         "predictions_by_hypothesis": hp})
        pending.append({"inputs": candidates[i], "predictions": hp})
    state["pending_predictions"] = pending
    ws.save_state(state)
    _append_history(ws.dir, {"event": "acquire", "mode": mode, "models": ids, "n_candidates": len(candidates),
                             "selected": [s["inputs"] for s in selected]})
    return {"mode": mode, "n_candidates_scored": len(candidates), "selected": selected,
            "budget_remaining": state["budget"] - state["queries_used"],
            "next": "run observe on the selected inputs; observe reports predicted vs observed per hypothesis"}


MEMORY_KEYS = ("validated_hypotheses", "falsified_hypotheses", "uncertain_hypotheses",
               "active_inputs", "inactive_inputs", "untested_inputs", "notes")


def cmd_memory(args: argparse.Namespace) -> dict[str, Any]:
    ws = Workspace(args.workdir)
    ws.require()
    update = _json_arg(args.memory_json, args.memory_file, "--memory-json/--memory-file")
    if not isinstance(update, dict) or not update:
        raise EngineError("memory update must be a non-empty object")
    unknown = sorted(set(update) - set(MEMORY_KEYS))
    if unknown:
        raise EngineError("unknown memory keys", unknown=unknown, allowed=list(MEMORY_KEYS))
    for k, v in update.items():
        if not isinstance(v, list):
            raise EngineError(f"memory field {k!r} must be a list")
    memory = _load(ws.memory_path, {})
    memory.update(update)
    _save(ws.memory_path, memory)
    _append_history(ws.dir, {"event": "memory", "keys": sorted(update)})
    return {"status": "ok", "memory": memory}


def compute_audit(ws: Workspace, final_model: str | None = None) -> dict[str, Any]:
    """Protocol checks over the ledger. These test the discovery process, not the answer."""
    state, observations, history = ws.state, ws.observations, _history(ws.dir)
    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"check": name, "passed": bool(passed), "detail": detail})

    n_oracle = sum(1 for o in observations if o["source"] == "oracle")
    n_manual = len(observations) - n_oracle
    add("budget_respected", state["queries_used"] <= state["budget"] and len(observations) == state["queries_used"],
        f"{state['queries_used']} used of {state['budget']}; {len(observations)} recorded ({n_oracle} oracle, {n_manual} manual)")

    logged = [h for e in history if e["event"] == "observe" for h in e["record_hashes"]]
    actual = [_record_hash(o) for o in observations]
    add("ledger_matches_observations", logged == actual,
        "every observation matches the hash logged when it was recorded" if logged == actual
        else "observations.json differs from the hashes logged at observe time")

    observes = [e for e in history if e["event"] == "observe"]
    add("multiple_observe_rounds", len(observes) >= 2, f"{len(observes)} observe rounds")

    fit_events = [e for e in history if e["event"] == "fit"]
    rival_fits = [e for e in fit_events if len(set(e["structures"].values())) >= 2]
    add("competing_hypotheses_fitted", bool(rival_fits),
        f"{len(rival_fits)} fit rounds compared at least two distinct structures")

    acquire_then_observe = False
    seen_acquire = False
    for e in history:
        if e["event"] == "acquire":
            seen_acquire = True
        elif e["event"] == "observe" and seen_acquire:
            acquire_then_observe = True
    add("hypothesis_conditioned_experiments", acquire_then_observe,
        "at least one observe followed an acquire" if acquire_then_observe else "no observe followed an acquire")

    n_mem = sum(1 for e in history if e["event"] == "memory")
    add("memory_updated", n_mem >= 1, f"{n_mem} memory updates")

    if final_model is not None:
        fitted = any(final_model in e["models"] for e in fit_events)
        add("final_model_was_fitted", fitted, f"model {final_model!r} {'appears' if fitted else 'never appears'} in a fit round")

    return {"passed": all(c["passed"] for c in checks), "checks": checks}


def cmd_finalize(args: argparse.Namespace) -> dict[str, Any]:
    ws = Workspace(args.workdir)
    ws.require()
    env, state, observations = ws.env, ws.state, ws.observations
    sel = _json_arg(args.selection_json, args.selection_file, "--selection-json/--selection-file")
    if not isinstance(sel, dict) or not isinstance(sel.get("model"), str):
        raise EngineError("selection must include the chosen model id as 'model'")
    if sel.get("mechanism") in (None, "", {}, []):
        raise EngineError("selection must include 'mechanism' written in the environment's target.output_format")
    if not isinstance(sel.get("rationale"), str) or not sel["rationale"].strip():
        raise EngineError("selection must include a non-empty 'rationale'")
    if not state.get("fit_settings"):
        raise EngineError("no fit settings recorded; run fit before finalize")

    mid = sel["model"]
    model = ws.load_models([mid])[mid]
    settings = dict(state["fit_settings"])
    settings["scales"] = observable_scales(observations, _observable_names(env))
    x = stack_inputs(observations, env["inputs"])
    y = stack_observed(observations, _observable_names(env))
    fits = _load(ws.fits_path, {})
    warm = fits.get("hypotheses", {}).get(mid, {}).get("params")
    final_fit = fit_model(model, x, y, settings, rng=np.random.default_rng(args.seed), restarts=args.restarts,
                          warm_start=warm or None)
    audit = compute_audit(ws, final_model=mid)
    result = {
        "status": "completed" if audit["passed"] else "error",
        "queries_used": state["queries_used"],
        "budget": state["budget"],
        "goal": env["goal"],
        "target": env["target"],
        "final_mechanism": sel["mechanism"],
        "rationale": sel["rationale"],
        "model": {"id": mid, "structure": model["structure"], "predicts": model["predicts"],
                  "params": final_fit["params"], "loss": settings["loss"], "loss_value": final_fit["loss_value"],
                  "bic": final_fit["bic"], "source": model["source"]},
        "audit": audit,
        "errors": [] if audit["passed"] else [f"audit check failed: {c['check']} ({c['detail']})"
                                              for c in audit["checks"] if not c["passed"]],
        "finalized_at": _now(),
    }
    _save(ws.dir / "final_result.json", result)
    _append_history(ws.dir, {"event": "finalize", "model": mid, "status": result["status"]})
    return {"status": result["status"], "result_path": str(ws.dir / "final_result.json"),
            "queries_used": result["queries_used"], "budget": result["budget"],
            "model": {k: result["model"][k] for k in ("id", "structure", "params", "loss_value", "bic")},
            "audit": audit, "errors": result["errors"]}


def cmd_audit(args: argparse.Namespace) -> dict[str, Any]:
    ws = Workspace(args.workdir)
    ws.require()
    return compute_audit(ws, final_model=args.final_model)


def cmd_validate_env(args: argparse.Namespace) -> dict[str, Any]:
    spec = _json_arg(args.spec_json, args.spec_file, "--spec-json/--spec-file")
    errors = validate_environment(spec)
    return {"valid": not errors, "errors": errors}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    def spec_args(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--spec-json")
        sp.add_argument("--spec-file")

    sp = sub.add_parser("validate-env", help="Check an autoscilab-env/1 spec without creating a workspace.")
    spec_args(sp)

    sp = sub.add_parser("init", help="Create a workspace from an environment spec.")
    sp.add_argument("--workdir", required=True)
    spec_args(sp)
    sp.add_argument("--confidence-threshold", type=float, default=DEFAULT_CONFIDENCE_THRESHOLD)
    sp.add_argument("--force", action="store_true")

    sp = sub.add_parser("observe", help="Run experiments through the oracle (or record manual measurements).")
    sp.add_argument("--workdir", required=True)
    sp.add_argument("--experiments-json")
    sp.add_argument("--experiments-file")

    sp = sub.add_parser("status", help="Show budget, mode, fit ranking, memory, contrasts, and the data table.")
    sp.add_argument("--workdir", required=True)
    sp.add_argument("--max-rows", type=int, default=60)

    sp = sub.add_parser("cluster", help="Group proposals by STRUCTURE and track Shannon entropy.")
    sp.add_argument("--workdir", required=True)
    sp.add_argument("--models", help="Comma-separated or JSON list of model ids.")
    sp.add_argument("--structures-json")
    sp.add_argument("--structures-file")
    sp.add_argument("--prev-entropy", type=float)
    sp.add_argument("--entropy-tol", type=float, default=0.1)
    sp.add_argument("--k-sampled", type=int)
    sp.add_argument("--k-max", type=int, default=20)

    sp = sub.add_parser("fit", help="Fit model modules, rank by BIC, and run the bootstrap gate.")
    sp.add_argument("--workdir", required=True)
    sp.add_argument("--models", required=True, help="Comma-separated or JSON list of model ids (files models/<id>.py).")
    sp.add_argument("--loss", required=True, choices=LOSSES)
    sp.add_argument("--noise-floor", type=float, default=1e-12,
                    help="Smallest per-residual loss value BIC will credit; set it from known measurement precision.")
    sp.add_argument("--relative-floor", type=float, default=1e-12)
    sp.add_argument("--observable-weights-json")
    sp.add_argument("--restarts", type=int, default=8)
    sp.add_argument("--n-boot", type=int, default=20)
    sp.add_argument("--seed", type=int, default=0)

    sp = sub.add_parser("acquire", help="Score candidates in search regions and pick the next batch.")
    sp.add_argument("--workdir", required=True)
    sp.add_argument("--regions-json")
    sp.add_argument("--regions-file")
    sp.add_argument("--points-json")
    sp.add_argument("--points-file")
    sp.add_argument("--models", help="Subset of fitted model ids; refine mode uses the first one.")
    sp.add_argument("--mode", choices=("disambiguate", "refine"))
    sp.add_argument("--n-experiments", type=int, default=4)
    sp.add_argument("--n-candidates", type=int, default=256)
    sp.add_argument("--seed", type=int, default=0)

    sp = sub.add_parser("memory", help="Update the scoreboard.")
    sp.add_argument("--workdir", required=True)
    sp.add_argument("--memory-json")
    sp.add_argument("--memory-file")

    sp = sub.add_parser("finalize", help="Refit the chosen model on all data, audit, and write final_result.json.")
    sp.add_argument("--workdir", required=True)
    sp.add_argument("--selection-json")
    sp.add_argument("--selection-file")
    sp.add_argument("--restarts", type=int, default=8)
    sp.add_argument("--seed", type=int, default=0)

    sp = sub.add_parser("audit", help="Run the protocol audit over the ledger.")
    sp.add_argument("--workdir", required=True)
    sp.add_argument("--final-model")
    return p


HANDLERS = {
    "validate-env": cmd_validate_env,
    "init": cmd_init,
    "observe": cmd_observe,
    "status": cmd_status,
    "cluster": cmd_cluster,
    "fit": cmd_fit,
    "acquire": cmd_acquire,
    "memory": cmd_memory,
    "finalize": cmd_finalize,
    "audit": cmd_audit,
}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        payload = HANDLERS[args.cmd](args)
    except EngineError as exc:
        _emit({"status": "error", "error": str(exc), **exc.extra})
        return exc.code
    except json.JSONDecodeError as exc:
        _emit({"status": "error", "error": f"invalid JSON argument: {exc}"})
        return 1
    _emit(payload)
    if args.cmd == "audit" and not payload["passed"]:
        return 1
    if args.cmd == "finalize" and payload["status"] != "completed":
        return 1
    if args.cmd == "validate-env" and not payload["valid"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
