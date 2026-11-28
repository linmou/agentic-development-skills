import numpy as np

STRUCTURE = "c[mode] * x1 ** n"
PREDICTS = ["y"]
PARAMETERS = {
    "c_a": {"bounds": [0.01, 100.0], "scale": "log"},
    "c_b": {"bounds": [0.01, 100.0], "scale": "log"},
    "n": {"bounds": [-3.0, 3.0]},
}


def predict(inputs, params):
    c = np.where(inputs["mode"] == "a", params["c_a"], params["c_b"])
    return {"y": c * inputs["x1"] ** params["n"]}
