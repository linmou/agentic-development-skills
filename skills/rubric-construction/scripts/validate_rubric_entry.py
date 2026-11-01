#!/usr/bin/env python3
# Mechanical gates G1-G4 for one rubric entry (rubric-quality-rubric.md); importable as validate_entry.
import argparse
import json
import re
from pathlib import Path

REQUIRED_RUBRIC_KEYS = {
    "id",
    "title",
    "applicability",
    "decision_rule",
    "dependencies",
    "lifecycle",
}
SCORE_RULE_KEY = re.compile(r"^score_(\d+)_rule$")


def is_non_empty_string(value: object) -> bool:
    return isinstance(value, str) and value.strip() != ""


def is_string_list(value: object) -> bool:
    return isinstance(value, list) and len(value) > 0 and all(is_non_empty_string(x) for x in value)


def validate_counter_pairs(value: object, key_name: str) -> list[str]:
    if not isinstance(value, list) or len(value) == 0:
        return [f"{key_name} must be a non-empty list"]

    issues = []
    for idx, pair in enumerate(value, start=1):
        if not isinstance(pair, list) or len(pair) != 2:
            issues.append(f"{key_name}[{idx}] must be [counter+, counter-]")
            continue

        plus, minus = pair
        if not is_non_empty_string(plus):
            issues.append(f"{key_name}[{idx}][0] must be non-empty string")
        if not is_non_empty_string(minus):
            issues.append(f"{key_name}[{idx}][1] must be non-empty string")

    return issues


def validate_entry(data: object) -> list[str]:
    if not isinstance(data, dict):
        return ["root must be object"]

    errors = []
    missing_keys = sorted(REQUIRED_RUBRIC_KEYS - set(data.keys()))
    if missing_keys:
        errors.append(f"missing keys {missing_keys}")

    if not is_non_empty_string(data.get("id", "")):
        errors.append("id must be non-empty string")

    if not is_non_empty_string(data.get("title", "")):
        errors.append("title must be non-empty string")

    applicability = data.get("applicability", {})
    if not isinstance(applicability, dict):
        errors.append("applicability must be object")
    else:
        if not is_string_list(applicability.get("include", [])):
            errors.append("applicability.include must be non-empty string list")
        if not is_string_list(applicability.get("exclude", [])):
            errors.append("applicability.exclude must be non-empty string list")

    dependencies = data.get("dependencies", {})
    if not isinstance(dependencies, dict):
        errors.append("dependencies must be object")
    else:
        if not is_string_list(dependencies.get("context_refs", [])):
            errors.append("dependencies.context_refs must be non-empty string list")
        if not is_string_list(dependencies.get("intent_refs", [])):
            errors.append("dependencies.intent_refs must be non-empty string list")

    if not isinstance(data.get("lifecycle", {}), dict):
        errors.append("lifecycle must be object")

    decision_rule = data.get("decision_rule", {})
    if not isinstance(decision_rule, dict):
        errors.append("decision_rule must be object")
        return errors

    score_levels = {m.group(1) for key in decision_rule if (m := SCORE_RULE_KEY.match(key))}
    if not score_levels:
        errors.append("decision_rule has no score_X_rule keys")
        return errors

    for score in sorted(score_levels, key=int):
        rule_key = f"score_{score}_rule"
        support_key = f"score_{score}_support_examples"
        counter_key = f"score_{score}_counter_examples"

        if not is_non_empty_string(decision_rule.get(rule_key, "")):
            errors.append(f"{rule_key} must be non-empty string")

        if not is_string_list(decision_rule.get(support_key)):
            errors.append(f"{support_key} must be non-empty string list")

        counter_value = decision_rule.get(counter_key)
        if counter_value is None:
            errors.append(f"missing {counter_key}")
        else:
            errors.extend(validate_counter_pairs(counter_value, counter_key))

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate rubric entry JSON files (gates G1-G4).")
    parser.add_argument("entries", nargs="+", type=Path, help="Rubric entry JSON file(s)")
    args = parser.parse_args()

    failed = 0
    for path in args.entries:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"{path}: cannot load ({exc})")
            failed += 1
            continue

        errors = validate_entry(data)
        if errors:
            failed += 1
            for item in errors:
                print(f"{path}: {item}")
        else:
            print(f"{path}: ok")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
