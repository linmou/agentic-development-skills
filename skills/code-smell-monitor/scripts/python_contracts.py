"""Optional Import Linter contract evidence; never infer contracts from directory names.

The bundled AST graph remains available without this optional third-party tool.
The CLI's text report is retained verbatim; only recognized, successful contract
summaries authorize treating exit 1 as an architectural contract violation.
"""
from __future__ import annotations

import configparser
import hashlib
import re
from pathlib import Path
from typing import Any


ANSI = re.compile(r"\x1b\[[0-9;]*m")
SUMMARY = re.compile(r"(?m)^\s*Contracts:\s*(?:(\d+)\s+kept\s*,\s*)?(\d+)\s+broken\b", re.I)
BROKEN_NAME = re.compile(r"(?m)^\s*(.+?)\s+BROKEN(?:\s+\(.*\))?\s*$")
IMPORT_EDGE = re.compile(r"(?m)^\s*(?:-\s*)?([\w.]+)\s+->\s+([\w.]+)\s+\(l\.\s*(\d+)\s*\)")


def _ini_config(path: Path) -> dict[str, Any] | None:
    cfg = configparser.ConfigParser(interpolation=None)
    with path.open(encoding="utf-8") as handle:
        cfg.read_file(handle)
    if "importlinter" not in cfg:
        return None
    contracts = []
    for section in cfg.sections():
        if section.startswith("importlinter:contract:"):
            contracts.append({"id": section.removeprefix("importlinter:contract:"),
                              "name": cfg.get(section, "name", fallback="")})
    return {"config": path.name, "contracts": contracts}


def _toml_config(path: Path) -> dict[str, Any] | None:
    try:
        import tomllib
    except ImportError:
        # Python 3.10: conservative detection; CLI validates the actual TOML.
        source = path.read_text(encoding="utf-8")
        if not re.search(r"(?m)^\s*\[tool\.importlinter\]\s*$", source):
            return None
        names = re.findall(r"(?m)^\s*name\s*=\s*[\"']([^\"']+)[\"']\s*$",
                           source.split("[[tool.importlinter.contracts]]", 1)[-1])
        return {"config": path.name,
                "contracts": [{"id": str(i), "name": name} for i, name in enumerate(names)]}
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    config = data.get("tool", {}).get("importlinter")
    if not isinstance(config, dict):
        return None
    contracts = config.get("contracts", [])
    if not isinstance(contracts, list):
        raise ValueError("importlinter contracts must be a list")
    return {"config": path.name, "contracts": [
        {"id": str(item.get("id", i)), "name": str(item.get("name", ""))}
        for i, item in enumerate(contracts) if isinstance(item, dict)
    ]}


def discover(repo: Path) -> dict[str, Any]:
    """Only explicitly defined project contracts qualify for enforcement."""
    matches = []
    for name in (".importlinter", "pyproject.toml", "setup.cfg"):
        path = repo / name
        if path.is_file():
            entry = _toml_config(path) if name.endswith(".toml") else _ini_config(path)
            if entry and entry["contracts"]:
                matches.append(entry)
    if len(matches) > 1:
        raise ValueError("multiple Import Linter contract configurations: " +
                         ", ".join(item["config"] for item in matches))
    if not matches:
        return {"status": "not_configured", "config": None, "contracts": [],
                "reason": "No explicit Import Linter contracts found"}
    return {"status": "configured", **matches[0]}


def classify(result: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    """Parse recognized Import Linter summaries and preserve source evidence."""
    base = {"detector": "import-linter", "config": config["config"],
            "configured_contracts": config["contracts"],
            "status": "failed", "findings": [], "enforced_violations": 0,
            "raw_report": "raw/architecture_import_linter.stdout.txt",
            "command": result["cmd"], "exit_code": result["exit_code"],
            "analysis_scope": "configured Python root package(s)"}
    if result.get("timed_out"):
        base["status"] = "timed_out"
        return base
    if result["exit_code"] in (126, 127):
        base["status"] = "unavailable"
        return base
    clean = ANSI.sub("", result.get("stdout", ""))
    match = SUMMARY.search(clean)
    if not match:
        base["error"] = "Import Linter did not emit a recognizable contract summary"
        return base
    kept, broken = int(match.group(1) or 0), int(match.group(2))
    base["contract_counts"] = {"kept": kept, "broken": broken}
    if broken == 0 and result["exit_code"] == 0:
        base["status"] = "covered"
        return base
    if broken == 0 or result["exit_code"] != 1 or "Broken contracts" not in clean:
        base["error"] = "CLI exit code disagrees with the contract summary"
        return base
    names = list(dict.fromkeys(BROKEN_NAME.findall(clean)))
    if len(names) != broken:
        base["error"] = "Cannot match broken contracts to their names"
        return base
    configs = {item["name"]: item for item in config["contracts"]}
    if any(name not in configs for name in names):
        base["error"] = "Broken contract names do not match the configured rules"
        return base
    import_edges = [{"from": source, "to": target, "line": int(line)}
                    for source, target, line in IMPORT_EDGE.findall(clean)]
    for name in names:
        item = configs[name]
        identity = config["config"] + ":" + item["id"] + ":" + name
        base["findings"].append({
            "id": "architecture-" + hashlib.sha256(identity.encode()).hexdigest()[:16],
            "category": "configured_rule_violation",
            "source": config["config"], "target": None,
            "classification": "confirmed_contract_violation",
            "evidence": {"rule": item["id"], "name": name, "config": config["config"],
                         "raw_report": base["raw_report"],
                         "reported_import_edges": import_edges,
                         "note": "Import paths are copied from the tool's combined report; "
                                 "inspect the raw report for each contract's exact chain."},
        })
    base["status"] = "violations"
    base["enforced_violations"] = len(base["findings"])
    return base
