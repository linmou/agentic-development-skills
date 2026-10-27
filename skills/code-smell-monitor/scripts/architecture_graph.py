#!/usr/bin/env python3
"""Normalize dependency-cruiser JSON without inventing architectural violations."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from typing import Any


def analyze(data: Any, max_degree: int = 12) -> dict[str, Any]:
    if not isinstance(data, dict) or not isinstance(data.get("modules"), list):
        raise ValueError("dependency-cruiser output must contain a modules array")
    modules = data["modules"]
    edges: set[tuple[str, str]] = set()
    nodes: set[str] = set()
    for module in modules:
        if not isinstance(module, dict) or not isinstance(module.get("source"), str):
            raise ValueError("malformed module")
        source = module["source"]
        nodes.add(source)
        for dep in module.get("dependencies", []):
            if not isinstance(dep, dict):
                raise ValueError("malformed dependency")
            target = dep.get("resolved")
            if isinstance(target, str) and target and not dep.get("couldNotResolve") and not dep.get("coreModule") and not dep.get("isExternal"):
                nodes.add(target)
                edges.add((source, target))
    incoming = {node: 0 for node in nodes}
    outgoing = {node: 0 for node in nodes}
    for source, target in edges:
        outgoing[source] += 1
        incoming[target] += 1
    findings: list[dict[str, Any]] = []

    def add(kind: str, source: str, target: str | None, evidence: dict[str, Any], classification: str) -> None:
        identity = json.dumps([kind, source, target], separators=(",", ":"))
        findings.append({
            "id": "architecture-" + hashlib.sha256(identity.encode()).hexdigest()[:16],
            "category": kind, "source": source, "target": target,
            "classification": classification, "evidence": evidence,
        })

    # A dependency cycle is a structural fact, not necessarily a design defect.
    adjacency = {node: [] for node in nodes}
    for source, target in edges:
        adjacency[source].append(target)
    position: dict[str, int] = {}
    low: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    groups: list[list[str]] = []
    def visit(node: str) -> None:
        position[node] = low[node] = len(position)
        stack.append(node)
        on_stack.add(node)
        for nxt in sorted(adjacency[node]):
            if nxt not in position:
                visit(nxt)
                low[node] = min(low[node], low[nxt])
            elif nxt in on_stack:
                low[node] = min(low[node], position[nxt])
        if low[node] == position[node]:
            group = []
            while True:
                member = stack.pop()
                on_stack.remove(member)
                group.append(member)
                if member == node:
                    break
            if len(group) > 1 or (len(group) == 1 and (node, node) in edges):
                groups.append(sorted(group))
    for node in sorted(nodes):
        if node not in position:
            visit(node)
    for group in groups:
        add("dependency_cycle", group[0], None, {"members": group}, "structural_fact")
    for node in sorted(nodes):
        if outgoing[node] >= max_degree:
            add("high_fan_out", node, None, {"degree": outgoing[node], "threshold": max_degree}, "review_candidate")
        if incoming[node] >= max_degree:
            add("high_fan_in", node, None, {"degree": incoming[node], "threshold": max_degree}, "review_candidate")
    violations = data.get("summary", {}).get("violations", []) if isinstance(data.get("summary"), dict) else []
    if not isinstance(violations, list):
        raise ValueError("malformed violations")
    for v in violations:
        if not isinstance(v, dict):
            raise ValueError("malformed violation")
        rule = v.get("rule", {})
        rule_name = rule.get("name") if isinstance(rule, dict) else None
        source, target = v.get("from"), v.get("to")
        if not all(isinstance(x, str) and x for x in (rule_name, source, target)):
            raise ValueError("violation missing rule/from/to")
        add("configured_rule_violation", source, target,
            {"rule": rule_name, "severity": rule.get("severity"), "comment": rule.get("comment")},
            "confirmed_contract_violation")
    return {
        "graph": {"nodes": len(nodes), "edges": len(edges)},
        "findings": sorted(findings, key=lambda item: (item["category"], item["source"], item["target"] or "")),
        "enforced_violations": sum(f["classification"] == "confirmed_contract_violation" for f in findings),
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--max-degree", type=int, default=12)
    args = parser.parse_args()
    if args.max_degree < 1:
        parser.error("--max-degree must be positive")
    result = analyze(json.loads(args.input.read_text()), args.max_degree)
    rendered = json.dumps(result, indent=2)
    if args.out:
        args.out.write_text(rendered + "\n")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
