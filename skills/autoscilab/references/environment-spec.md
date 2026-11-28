# Environment spec (`autoscilab-env/1`)

The skill talks to every experimental system through one interface: an `environment.json` spec plus an oracle command. The skill defines this format; each environment supplies an **adapter** that maps its real interface onto it. The engine validates the spec and never interprets what an input means scientifically.

## `environment.json`

```json
{
  "spec_version": "autoscilab-env/1",
  "goal": "Find how the oscillation period depends on the rig settings.",
  "description": "Learner-visible context: units, what each knob does, known constraints.",
  "budget": 40,
  "inputs": [
    {"name": "length", "kind": "continuous", "bounds": [0.05, 5.0], "scale": "log",
     "role": "control", "unit": "m"},
    {"name": "amplitude", "kind": "continuous", "bounds": [0.01, 1.2], "role": "control", "unit": "rad"},
    {"name": "brake_gain", "kind": "continuous", "bounds": [0.0, 2.0], "role": "intervention",
     "baseline": 0.0, "description": "Strength of the eddy-current brake; 0 disables it."},
    {"name": "medium", "kind": "categorical", "levels": ["air", "water"]}
  ],
  "observables": [
    {"name": "period", "positive": true, "unit": "s", "description": "Mean period over 10 swings."}
  ],
  "oracle": {"command": "python3 adapters/rig_oracle.py"},
  "target": {
    "representation": "equation",
    "output_format": "Python source defining def law(length, amplitude, brake_gain, medium): returning period."
  }
}
```

| Field | Required | Meaning |
|---|---|---|
| `spec_version` | yes | Always `autoscilab-env/1`. |
| `goal` | yes | The discovery question. |
| `description` | no | Everything the learner may know about the system before experimenting. |
| `budget` | yes | Positive integer: maximum oracle queries. |
| `inputs[]` | yes | Every settable knob. `kind`: `continuous` (default), `integer`, `categorical`. Numeric kinds need `bounds` `[lo, hi]`; `scale` `linear` (default) or `log` (needs `lo > 0`). Categorical needs `levels` (≥ 2). `role` (`control` default, or `intervention`), `baseline`, `unit` and `description` are context for the agent; the engine only checks them for shape. |
| `observables[]` | yes | Every value one query returns. `positive`, `unit` and `description` are context for the agent. |
| `oracle.command` | no | Shell command implementing the oracle protocol below. Omit it when measurements arrive by hand (lab assays); then `observe` records manual values instead. |
| `target.representation` | yes | Free-text label of the answer type (`equation`, `graph`, `ranking`, …). |
| `target.output_format` | yes | Exactly what the final mechanism must look like. `finalize` stores the agent's mechanism as given; checking it against this format is the caller's job. |

## Oracle protocol

One query per process call:

- stdin: `{"inputs": {"<name>": <value>, ...}}` with every declared input.
- stdout: `{"observables": {"<name>": <finite number>, ...}}` with every declared observable.
- Non-zero exit code means the query failed; the engine stops the batch and records nothing for it.

## Writing an adapter

An adapter is a small script owned by the environment, not by the skill. It:

1. Writes `environment.json` from the environment's **public** interface: names, bounds, units and the target format a user of that environment would be told.
2. Implements the oracle protocol by forwarding inputs to the real system (simulator, instrument API, lab queue) and returning only learner-visible observables.
3. Keeps hidden state out of both: no ground truth, task identity or difficulty labels in the spec, the oracle output or error messages.
4. Enforces the budget itself when the evaluation must be tamper-proof; the engine's budget check protects honest runs, not adversarial ones.

When the environment already speaks a different protocol, write the adapter at the start of the run (Setup step) and keep it beside the workspace, outside the skill folder.
