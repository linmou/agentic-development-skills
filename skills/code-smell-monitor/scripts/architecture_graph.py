#!/usr/bin/env python3
"""Normalize dependency-cruiser JSON without inventing architectural violations."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from typing import Any


def analyze(data: Any, max_degree: int = 12) -> dict[str, Any]:
    if max_degree < 1:
        raise ValueError('max_degree must be positive')
    if not isinstance(data, dict) or not isinstance(data.get("modules"), list):
        raise ValueError("dependency-cruiser output must contain a modules array")
    modules = data["modules"]
    edges: set[tuple[str, str]] = set()
    nodes: set[str] = set()
    for module in modules:
        if not isinstance(module, dict) or not isinstance(module.get("source"), str):
            raise ValueError("malformed module")
        source = module["source"]
        if (module.get('coreModule') or module.get('couldNotResolve')
            or 'node_modules' in Path(source).parts):
            continue
        nodes.add(source)
        for dep in module.get("dependencies", []):
            if not isinstance(dep, dict):
                raise ValueError("malformed dependency")
            target = dep.get("resolved")
            if (isinstance(target, str) and target and not dep.get("couldNotResolve")
                and not dep.get("coreModule") and not dep.get("isExternal")
                and 'node_modules' not in Path(target).parts):
                nodes.add(target)
                edges.add((source, target))
    incoming = {node: 0 for node in nodes}
    outgoing = {node: 0 for node in nodes}
    for source, target in edges:
        outgoing[source] += 1
        incoming[target] += 1
    findings: list[dict[str, Any]] = []

    def add(kind: str, source: str, target: str | None, evidence: dict[str, Any], classification: str) -> None:
        identity_parts = [kind, source, target]
        if kind == 'configured_rule_violation':
            identity_parts.append(evidence['rule'])
        identity = json.dumps(identity_parts, separators=(",", ":"))
        findings.append({
            "id": "architecture-" + hashlib.sha256(identity.encode()).hexdigest()[:16],
            "category": kind, "source": source, "target": target,
            "classification": classification, "evidence": evidence,
        })

    # A dependency cycle is a structural fact, not necessarily a design defect.
    adjacency = {node: [] for node in nodes}
    for source, target in edges:
        adjacency[source].append(target)
    reverse = {node: [] for node in nodes}
    for source, target in edges:
        reverse[target].append(source)
    # Iterative Kosaraju avoids Python recursion limits on real project graphs.
    seen: set[str] = set()
    order: list[str] = []
    for node in sorted(nodes):
        if node in seen:
            continue
        seen.add(node)
        traversal = [(node, iter(sorted(adjacency[node])))]
        while traversal:
            current, neighbors = traversal[-1]
            nxt = next(neighbors, None)
            if nxt is None:
                order.append(current)
                traversal.pop()
            elif nxt not in seen:
                seen.add(nxt)
                traversal.append((nxt, iter(sorted(adjacency[nxt]))))
    groups: list[list[str]] = []
    assigned: set[str] = set()
    for node in reversed(order):
        if node in assigned:
            continue
        stack = [node]
        assigned.add(node)
        group = []
        while stack:
            current = stack.pop()
            group.append(current)
            for parent in reverse[current]:
                if parent not in assigned:
                    assigned.add(parent)
                    stack.append(parent)
        if len(group) > 1 or (node, node) in edges:
            groups.append(sorted(group))
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
        "enforced_violations": sum(
            f["classification"] == "confirmed_contract_violation"
            and f["evidence"].get("severity") == "error" for f in findings
        ),
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
