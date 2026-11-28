"""Toy test environment for the engine tests (not part of the skill).

y = vmax(mode) * x1 / (0.5 + x1); x2 is a distractor; vmax is 3 for mode "a" and 6 for mode "b".
Reads {"inputs": {...}} on stdin and prints {"observables": {"y": ...}}.
"""
import json
import sys

point = json.load(sys.stdin)["inputs"]
vmax = 3.0 if point["mode"] == "a" else 6.0
print(json.dumps({"observables": {"y": vmax * point["x1"] / (0.5 + point["x1"])}}))
