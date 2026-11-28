# Model modules: how you write a hypothesis

Every competing mechanism is a Python file you write at `<workdir>/models/<id>.py`. The file **is** the hypothesis: its functional form, which inputs it uses and how they combine are your scientific claims. The engine only fits the free parameters you declare, so nothing in the engine prefers one form over another.

## Protocol

```python
import numpy as np

STRUCTURE = "c * length ** 0.5 * (1 + a * amplitude ** 2)"   # structural identity
PREDICTS = ["period"]                                         # observables this model predicts
PARAMETERS = {                                                # free parameters to fit
    "c": {"bounds": [1e-2, 1e2], "scale": "log"},
    "a": {"bounds": [-1.0, 1.0], "init": 0.0},
}

def predict(inputs, params):
    """inputs: dict of name -> np.ndarray over a batch (categorical inputs are object arrays).
    params: dict of name -> float. Return dict of observable -> np.ndarray of the batch length."""
    L, th = inputs["length"], inputs["amplitude"]
    return {"period": params["c"] * np.sqrt(L) * (1 + params["a"] * th ** 2)}
```

| Field | Required | Rules |
|---|---|---|
| `STRUCTURE` | yes | One canonical string per structural family, written consistently (same variable order, same spacing, constants unnamed or uniformly named). Two models with the same `STRUCTURE` count as one structure in clustering and in the audit. Whitespace runs are collapsed; nothing else is normalized. |
| `PREDICTS` | yes | Subset of the environment's observables. All models fitted together must predict the same set. |
| `PARAMETERS` | no | `{}` for a parameter-free model. Each entry: `bounds` (finite, `lo < hi`), optional `scale` (`linear`/`log`; log needs `lo > 0`), optional `init` (defaults to the bound midpoint, geometric for log). |
| `predict` | yes | Vectorized over the batch. Exceptions during fitting count as a failed evaluation at that parameter value; a missing observable or wrong shape is a protocol error. |

## Structural hypotheses (graphs, networks, pathways)

For a structure-learning target, a model is a candidate structure **plus** the dynamics you believe connect it. Write both explicitly:

```python
EDGES = [("u", "n1", +1), ("n1", "n2", -1)]
STRUCTURE = "u->n1(+); n1->n2(-)"          # sorted, canonical edge list
PREDICTS = ["n1", "n2"]
PARAMETERS = {...}                          # whatever your chosen node response needs

def node_response(drive, theta):
    ...                                     # YOUR choice of response function: state it in memory notes

def predict(inputs, params):
    ...                                     # propagate inputs through EDGES with node_response
```

The response function is a scientific assumption, not plumbing. Decide it from what the environment description and your observations support, record the reason in `memory` notes, and when the data are ambiguous, fit the same edge set under two response families so a structure is not chosen merely because one response family happens to fit it.

## Choosing fit settings

`fit` makes you declare the loss on every call, because the right loss follows from the noise you expect:

| `--loss` | Use when |
|---|---|
| `log_mse` | Observables are strictly positive and errors scale with magnitude (multiplicative noise, values spanning decades). |
| `relative` | Same idea, but values may approach zero; `--relative-floor` sets the denominator floor. |
| `mse` | Additive noise or signed observables. Residuals are divided by each observable's standard deviation across the data so several observables combine on one scale. |

`--noise-floor` is the smallest mean squared residual BIC will credit. Leave it at the default for exact simulators; set it to the known measurement precision (for example `0.02**2` for 2 % multiplicative noise under `log_mse`) so BIC does not reward fitting noise. Record the choice and its reason in `memory` notes.

## Final mechanism

`finalize` stores the `mechanism` you write in the environment's `target.output_format`, plus the selected model's source and fitted parameters. Translate the winning model into that format yourself (for example, substitute fitted constants into an expression, or list the edges of the winning structure).
