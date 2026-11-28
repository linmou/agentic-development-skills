STRUCTURE = "a + b * x1 + c * x2"
PREDICTS = ["y"]
PARAMETERS = {
    "a": {"bounds": [-50.0, 50.0]},
    "b": {"bounds": [-50.0, 50.0]},
    "c": {"bounds": [-50.0, 50.0]},
}


def predict(inputs, params):
    return {"y": params["a"] + params["b"] * inputs["x1"] + params["c"] * inputs["x2"]}
