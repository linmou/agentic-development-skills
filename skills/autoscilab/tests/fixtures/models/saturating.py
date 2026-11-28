import numpy as np

STRUCTURE = "vmax[mode] * x1 / (K + x1)"
PREDICTS = ["y"]
PARAMETERS = {
    "vmax_a": {"bounds": [0.01, 100.0], "scale": "log"},
    "vmax_b": {"bounds": [0.01, 100.0], "scale": "log"},
    "K": {"bounds": [0.001, 100.0], "scale": "log"},
}


def predict(inputs, params):
    vmax = np.where(inputs["mode"] == "a", params["vmax_a"], params["vmax_b"])
    return {"y": vmax * inputs["x1"] / (params["K"] + inputs["x1"])}
