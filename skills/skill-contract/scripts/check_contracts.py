#!/usr/bin/env python3
"""Mechanical checks for skill-contract/1 contracts and their local callers.

Scans one or more skill roots (folders whose direct children contain SKILL.md),
loads callee contracts (contract.json), caller declarations (metadata.requires)
and caller call examples (references/calls/<callee>/*.json), and reports:

- invalid contracts and duplicate store ownership
- unresolved or version-incompatible declarations
- call examples that fail the callee request schema or lack provenance
- statuses a caller never mentions, and callers that never declared a callee
- with --proposed: which callers break under a proposed contract

Semantic questions (is the provenance real, does the caller act on each status,
does it write callee-owned stores) are left to the skill's semantic pass.
Standard library only; Python 3.11+.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

FORMAT = "skill-contract/1"
SEVERITY_ORDER = {"error": 0, "insufficient": 1, "warn": 2, "info": 3}

# ---------------------------------------------------------------------------
# Findings


@dataclass
class Finding:
    severity: str  # error | insufficient | warn | info
    code: str
    skill: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"severity": self.severity, "code": self.code, "skill": self.skill, "message": self.message}


def verdict(findings: list[Finding]) -> str:
    if any(f.severity == "error" for f in findings):
        return "fail"
    if any(f.severity == "insufficient" for f in findings):
        return "insufficient_evidence"
    return "pass"


# ---------------------------------------------------------------------------
# Frontmatter (the small YAML subset SKILL.md frontmatter uses)


def parse_frontmatter(text: str) -> dict[str, Any]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    data: dict[str, Any] = {}
    current_map: dict[str, str] | None = None
    in_block_scalar = False
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indented = line[0] in " \t"
        if indented:
            if in_block_scalar:
                continue
            if current_map is not None:
                key, sep, value = line.strip().partition(":")
                if sep:
                    current_map[key.strip()] = _unquote(value.strip())
            continue
        in_block_scalar = False
        current_map = None
        key, sep, value = line.partition(":")
        if not sep:
            continue
        key, value = key.strip(), value.strip()
        if value in (">", "|", ">-", "|-", ">+", "|+"):
            in_block_scalar = True
            data[key] = ""
        elif value == "":
            current_map = {}
            data[key] = current_map
        else:
            data[key] = _unquote(value)
    return data


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


# ---------------------------------------------------------------------------
# Semantic versions and ranges

Version = tuple[int, int, int]
_VERSION_RE = re.compile(r"^v?(\d+)(?:\.(\d+))?(?:\.(\d+))?$")


def parse_version(text: str) -> Version | None:
    match = _VERSION_RE.match(text.strip())
    if not match:
        return None
    major, minor, patch = (int(part) if part is not None else 0 for part in match.groups())
    return (major, minor, patch)


def contract_version(contract: dict[str, Any]) -> Version:
    """Version of a contract that already passed contract_problems."""
    version = parse_version(str(contract["version"]))
    if version is None:
        raise ValueError(f"unvalidated contract version: {contract['version']!r}")
    return version


def _comparator(token: str) -> list[tuple[str, Version]] | None:
    if token in ("*", "x", ""):
        return []
    for op in (">=", "<=", ">", "<", "=", "^", "~"):
        if token.startswith(op):
            version = parse_version(token[len(op):])
            if version is None:
                return None
            major, minor, patch = version
            if op == "^":
                upper = (major + 1, 0, 0) if major else ((0, minor + 1, 0) if minor else (0, 0, patch + 1))
                return [(">=", version), ("<", upper)]
            if op == "~":
                return [(">=", version), ("<", (major, minor + 1, 0))]
            return [(op, version)]
    version = parse_version(token)
    return None if version is None else [("=", version)]


def parse_range(text: str) -> list[tuple[str, Version]] | None:
    comparators: list[tuple[str, Version]] = []
    for token in text.split():
        parsed = _comparator(token)
        if parsed is None:
            return None
        comparators.extend(parsed)
    return comparators


def satisfies(version: Version, comparators: list[tuple[str, Version]]) -> bool:
    checks = {
        ">=": lambda a, b: a >= b,
        "<=": lambda a, b: a <= b,
        ">": lambda a, b: a > b,
        "<": lambda a, b: a < b,
        "=": lambda a, b: a == b,
    }
    return all(checks[op](version, bound) for op, bound in comparators)


def parse_requires(value: str) -> list[tuple[str, str]]:
    """'a@^1.0.0, b@~2.1' -> [('a', '^1.0.0'), ('b', '~2.1')]. Missing range means '*'."""
    entries = []
    for raw in value.split(","):
        raw = raw.strip()
        if not raw:
            continue
        name, sep, rng = raw.partition("@")
        entries.append((name.strip(), rng.strip() if sep else "*"))
    return entries


# ---------------------------------------------------------------------------
# JSON Schema subset

SUPPORTED_KEYWORDS = {
    "type", "properties", "required", "additionalProperties", "items", "enum", "const",
    "minLength", "minItems", "oneOf", "anyOf", "allOf", "description", "title", "default", "examples",
}
_TYPES = {
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "string": lambda v: isinstance(v, str),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool),
    "null": lambda v: v is None,
}


def schema_problems(schema: Any, path: str = "$") -> list[str]:
    """Report unsupported keywords or malformed values in a schema."""
    if not isinstance(schema, dict):
        return [f"{path}: schema must be an object"]
    problems = [f"{path}: unsupported keyword '{key}'" for key in schema if key not in SUPPORTED_KEYWORDS]
    types = schema.get("type")
    for name in [types] if isinstance(types, str) else (types or []):
        if name not in _TYPES:
            problems.append(f"{path}: unknown type '{name}'")
    for name, sub in (schema.get("properties") or {}).items():
        problems += schema_problems(sub, f"{path}.{name}")
    if "items" in schema:
        problems += schema_problems(schema["items"], f"{path}[]")
    for key in ("oneOf", "anyOf", "allOf"):
        for index, sub in enumerate(schema.get(key) or []):
            problems += schema_problems(sub, f"{path}<{key}{index}>")
    if "additionalProperties" in schema and not isinstance(schema["additionalProperties"], bool):
        problems.append(f"{path}: additionalProperties must be true or false")
    return problems


def validate(value: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    errors: list[str] = []
    types = schema.get("type")
    if types is not None:
        allowed = [types] if isinstance(types, str) else types
        if not any(_TYPES[name](value) for name in allowed):
            return [f"{path}: expected {'/'.join(allowed)}, got {type(value).__name__}"]
    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: must equal {json.dumps(schema['const'])}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: {json.dumps(value)} not in {json.dumps(schema['enum'])}")
    if isinstance(value, str) and len(value) < schema.get("minLength", 0):
        errors.append(f"{path}: shorter than {schema['minLength']}")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(f"{path}: fewer than {schema['minItems']} items")
        if "items" in schema:
            for index, item in enumerate(value):
                errors += validate(item, schema["items"], f"{path}[{index}]")
    if isinstance(value, dict):
        properties = schema.get("properties") or {}
        for name in schema.get("required") or []:
            if name not in value:
                errors.append(f"{path}: missing required '{name}'")
        for name, item in value.items():
            if name in properties:
                errors += validate(item, properties[name], f"{path}.{name}")
            elif schema.get("additionalProperties") is False:
                errors.append(f"{path}: unexpected field '{name}'")
    if "oneOf" in schema:
        results = [validate(value, sub, path) for sub in schema["oneOf"]]
        matches = sum(1 for result in results if not result)
        if matches == 0:
            # Prefer branches whose const discriminators match, so the message names the real gap.
            selected = [r for r in results if not any("must equal" in e for e in r)] or results
            detail = "; ".join(e for r in selected for e in r[:5])
            errors.append(f"{path}: matches no oneOf branch ({detail})")
        elif matches > 1:
            errors.append(f"{path}: matches {matches} oneOf branches; exactly one allowed")
    for sub in schema.get("allOf") or []:
        errors += validate(value, sub, path)
    if "anyOf" in schema:
        results = [validate(value, sub, path) for sub in schema["anyOf"]]
        if all(results):
            errors.append(f"{path}: matches no anyOf branch ({'; '.join(result[0] for result in results)})")
    return errors


# ---------------------------------------------------------------------------
# Skills, contracts, examples


@dataclass
class Skill:
    name: str
    path: Path
    frontmatter: dict[str, Any]
    contract: dict[str, Any] | None = None
    requires: list[tuple[str, str]] = field(default_factory=list)

    def prose(self) -> str:
        """SKILL.md plus Markdown references: the text a caller's behaviour lives in."""
        parts = [(self.path / "SKILL.md").read_text(encoding="utf-8", errors="replace")]
        references = self.path / "references"
        if references.is_dir():
            for doc in sorted(references.rglob("*.md")):
                parts.append(doc.read_text(encoding="utf-8", errors="replace"))
        return "\n".join(parts)

    def examples(self, callee: str) -> list[Path]:
        folder = self.path / "references" / "calls" / callee
        return sorted(folder.glob("*.json")) if folder.is_dir() else []


def discover(roots: list[Path], findings: list[Finding]) -> dict[str, Skill]:
    skills: dict[str, Skill] = {}
    seen: set[Path] = set()
    for root in roots:
        if not root.is_dir():
            findings.append(Finding("warn", "root-missing", "-", f"skill root not found: {root}"))
            continue
        for child in sorted(root.iterdir()):
            skill_md = child / "SKILL.md"
            if not skill_md.is_file():
                continue
            real = child.resolve()
            if real in seen:
                continue
            seen.add(real)
            frontmatter = parse_frontmatter(skill_md.read_text(encoding="utf-8", errors="replace"))
            name = str(frontmatter.get("name") or child.name)
            if name in skills:
                findings.append(Finding("warn", "duplicate-skill", name,
                                        f"two different folders named '{name}': {skills[name].path} and {child}; using the first"))
                continue
            skill = Skill(name=name, path=child, frontmatter=frontmatter)
            metadata = frontmatter.get("metadata")
            if isinstance(metadata, dict) and metadata.get("requires"):
                skill.requires = parse_requires(metadata["requires"])
            skills[name] = skill
    return skills


def load_contract(path: Path, findings: list[Finding], owner: str) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        findings.append(Finding("error", "contract-unreadable", owner, f"{path}: {exc}"))
        return None


def contract_problems(contract: dict[str, Any], skill: Skill | None) -> list[str]:
    problems: list[str] = []
    for key in ("contract_format", "skill", "version", "capability", "prose_contract",
                "request", "response", "status_field", "statuses", "writes", "changes"):
        if key not in contract:
            problems.append(f"missing key '{key}'")
    if problems:
        return problems
    if contract["contract_format"] != FORMAT:
        problems.append(f"contract_format must be '{FORMAT}'")
    if parse_version(str(contract["version"])) is None:
        problems.append(f"version '{contract['version']}' is not MAJOR.MINOR.PATCH")
    if skill is not None:
        if contract["skill"] != skill.name or skill.path.name != skill.name:
            problems.append(f"skill '{contract['skill']}' must match folder '{skill.path.name}' and SKILL.md name '{skill.name}'")
        prose = skill.path / str(contract["prose_contract"]).split("#", 1)[0]
        if not prose.is_file():
            problems.append(f"prose_contract not found: {prose}")
    for part in ("request", "response"):
        problems += [f"{part}: {issue}" for issue in schema_problems(contract[part])]
    statuses = contract["statuses"]
    if not isinstance(statuses, list) or not statuses or not all(isinstance(s, str) for s in statuses):
        problems.append("statuses must be a non-empty list of strings")
    elif isinstance(contract["response"], dict):
        status_schema = ((contract["response"].get("properties") or {}).get(contract["status_field"]) or {})
        if contract["status_field"] not in (contract["response"].get("required") or []):
            problems.append(f"response must require status_field '{contract['status_field']}'")
        if "enum" in status_schema and set(status_schema["enum"]) != set(statuses):
            problems.append(f"statuses {statuses} differ from response {contract['status_field']} enum {status_schema['enum']}")
    if not isinstance(contract["writes"], list) or not all(
            isinstance(w, dict) and w.get("store") and w.get("location") for w in contract["writes"]):
        problems.append("writes must be a list of {store, location}")
    changes = contract["changes"]
    if not isinstance(changes, list) or not changes or changes[-1].get("version") != contract["version"]:
        problems.append("last changes entry must carry the current version")
    return problems


def leaf_paths(value: Any, prefix: str = "") -> set[str]:
    if isinstance(value, dict) and value:
        paths: set[str] = set()
        for key, item in value.items():
            paths |= leaf_paths(item, f"{prefix}.{key}" if prefix else key)
        return paths
    if isinstance(value, list) and value:
        paths = set()
        for item in value:
            paths |= leaf_paths(item, f"{prefix}[]")
        return paths
    return {prefix} if prefix else set()


def uncovered(paths: set[str], provenance: dict[str, Any]) -> list[str]:
    keys = {key.strip() for key in provenance if str(provenance[key]).strip()}

    def covered(path: str) -> bool:
        return any(path == key or path.startswith(key + ".") or path.startswith(key + "[]") for key in keys)

    return sorted(path for path in paths if not covered(path))


def check_example(path: Path, caller: str, callee: str, request_schema: dict[str, Any]) -> tuple[list[Finding], bool]:
    """Returns findings and whether the request validated."""
    try:
        example = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [Finding("error", "example-unreadable", caller, f"{path}: {exc}")], False
    findings: list[Finding] = []
    request = example.get("request")
    if not isinstance(request, dict):
        return [Finding("error", "example-malformed", caller, f"{path.name}: 'request' object required")], False
    errors = validate(request, request_schema)
    for error in errors:
        findings.append(Finding("error", "example-invalid", caller, f"{callee}/{path.name}: {error}"))
    provenance = example.get("provenance")
    if not isinstance(provenance, dict):
        findings.append(Finding("error", "provenance-missing", caller, f"{callee}/{path.name}: 'provenance' object required"))
    else:
        for missing in uncovered(leaf_paths(request), provenance):
            findings.append(Finding("error", "provenance-missing", caller,
                                    f"{callee}/{path.name}: no provenance for field '{missing}'"))
    return findings, not errors


def mentions(text: str, name: str) -> bool:
    return re.search(rf"(?<![\w-])\$?{re.escape(name)}(?![\w-])", text) is not None


# ---------------------------------------------------------------------------
# Main check


def check(roots: list[Path], only_callee: str | None = None, proposed: Path | None = None) -> list[Finding]:
    findings: list[Finding] = []
    skills = discover(roots, findings)

    contracts: dict[str, dict[str, Any]] = {}
    for skill in skills.values():
        contract_file = skill.path / "contract.json"
        if not contract_file.is_file():
            continue
        contract = load_contract(contract_file, findings, skill.name)
        if contract is None:
            continue
        problems = contract_problems(contract, skill)
        for problem in problems:
            findings.append(Finding("error", "contract-invalid", skill.name, problem))
        if not problems:
            skill.contract = contract
            contracts[skill.name] = contract

    owners: dict[str, str] = {}
    for name, contract in contracts.items():
        for write in contract["writes"]:
            store = write["store"]
            if store in owners:
                findings.append(Finding("error", "dual-writer", name,
                                        f"store '{store}' is also claimed by '{owners[store]}'"))
            else:
                owners[store] = name

    current = dict(contracts)
    if proposed is not None:
        proposed_contract = load_contract(proposed, findings, "-")
        if proposed_contract is None:
            return findings
        target = skills.get(str(proposed_contract.get("skill")))
        problems = contract_problems(proposed_contract, target)
        for problem in problems:
            findings.append(Finding("error", "proposed-invalid", str(proposed_contract.get("skill")), problem))
        if problems or target is None:
            if target is None:
                findings.append(Finding("error", "proposed-unknown", str(proposed_contract.get("skill")),
                                        "proposed contract names no local skill"))
            return findings
        contracts[target.name] = proposed_contract
        only_callee = only_callee or target.name
        old = current.get(target.name)
        if old is not None:
            removed = sorted(set(old["statuses"]) - set(proposed_contract["statuses"]))
            added = sorted(set(proposed_contract["statuses"]) - set(old["statuses"]))
            same_major = contract_version(old)[0] == contract_version(proposed_contract)[0]
            if removed and same_major:
                findings.append(Finding("error", "breaking-without-major", target.name,
                                        f"statuses removed {removed} without a MAJOR bump"))
            if added:
                findings.append(Finding("warn", "status-added", target.name,
                                        f"new statuses {added}: every caller must handle them"))

    # Declared callers
    declared: dict[str, set[str]] = {}
    for caller in skills.values():
        for callee_name, rng in caller.requires:
            declared.setdefault(callee_name, set()).add(caller.name)
            if only_callee and callee_name != only_callee:
                continue
            callee = skills.get(callee_name)
            contract = contracts.get(callee_name)
            if callee is None:
                findings.append(Finding("error", "requires-unresolved", caller.name,
                                        f"requires '{callee_name}', not found in the scanned roots"))
                continue
            if contract is None:
                findings.append(Finding("insufficient", "callee-no-contract", caller.name,
                                        f"requires '{callee_name}', which has no valid contract.json"))
                continue
            comparators = parse_range(rng)
            if comparators is None:
                findings.append(Finding("error", "range-invalid", caller.name, f"'{callee_name}@{rng}' is not a valid range"))
            elif not satisfies(contract_version(contract), comparators):
                findings.append(Finding("error", "version-mismatch", caller.name,
                                        f"requires {callee_name}@{rng}, contract is {contract['version']}"))
            examples = caller.examples(callee_name)
            if not examples:
                findings.append(Finding("insufficient", "no-call-example", caller.name,
                                        f"no references/calls/{callee_name}/*.json; request fit cannot be checked"))
            for example in examples:
                example_findings, valid_now = check_example(example, caller.name, callee_name, contract["request"])
                findings += example_findings
                old = current.get(callee_name)
                if proposed is not None and old is not None and not valid_now:
                    _, valid_before = check_example(example, caller.name, callee_name, old["request"])
                    if valid_before and contract_version(old)[0] == contract_version(contract)[0]:
                        findings.append(Finding("error", "breaking-without-major", callee_name,
                                                f"{caller.name}/{example.name} was valid under {old['version']} "
                                                f"and fails {contract['version']} without a MAJOR bump"))
            prose = caller.prose()
            for status in contract["statuses"]:
                if not mentions(prose, status):
                    findings.append(Finding("warn", "status-unmentioned", caller.name,
                                            f"never mentions {callee_name} status '{status}'; confirm it is handled"))

    # Undeclared callers and high-stakes suggestions
    for callee_name, contract in contracts.items():
        if only_callee and callee_name != only_callee:
            continue
        for caller in skills.values():
            if caller.name == callee_name or caller.name in declared.get(callee_name, set()):
                continue
            if mentions(caller.prose(), callee_name):
                findings.append(Finding("warn", "undeclared-caller", caller.name,
                                        f"mentions '{callee_name}' without metadata.requires; declare it or confirm it is not a call"))
        if contract.get("high_stakes"):
            findings.append(Finding("info", "trace-tier-suggested", callee_name,
                                    "high_stakes contract: consider the optional trace check (references/trace-check.md)"))
    return findings


def render(findings: list[Finding]) -> str:
    lines = [f"{verdict(findings).upper()}: {sum(f.severity == 'error' for f in findings)} error(s), "
             f"{sum(f.severity == 'insufficient' for f in findings)} insufficient, "
             f"{sum(f.severity == 'warn' for f in findings)} warning(s)"]
    for finding in sorted(findings, key=lambda f: (SEVERITY_ORDER[f.severity], f.skill, f.code)):
        lines.append(f"- [{finding.severity}] {finding.skill}: {finding.code}: {finding.message}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check skill-contract/1 contracts and their local callers.")
    parser.add_argument("roots", nargs="+", type=Path, help="folders whose direct children are skills")
    parser.add_argument("--callee", help="only check callers of this callee")
    parser.add_argument("--proposed", type=Path, help="impact check: a proposed contract.json for an existing callee")
    parser.add_argument("--json", action="store_true", help="print findings as JSON")
    args = parser.parse_args(argv)
    findings = check([root.expanduser() for root in args.roots], args.callee, args.proposed)
    if args.json:
        print(json.dumps({"verdict": verdict(findings), "findings": [f.as_dict() for f in findings]}, indent=2))
    else:
        print(render(findings))
    return 1 if verdict(findings) == "fail" else 0


if __name__ == "__main__":
    sys.exit(main())
