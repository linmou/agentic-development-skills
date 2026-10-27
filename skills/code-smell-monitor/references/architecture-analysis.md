# Universal architecture analysis

Run `--architecture` from a JS/TS package root. Install dependency-cruiser in the target project, or use `--install missing` to allow an ephemeral npx download. Prefer `--install never` in CI and locked-down environments.

The monitor runs dependency-cruiser on the package root, preserving `raw/architecture_depcruise.stdout.txt`, `raw/architecture_depcruise.meta.json`, and a normalized `raw/architecture_summary.json`. The `summary.json` `architecture` property also includes status, actual scope, graph sizes, and findings.

- `dependency_cycle`: observable strongly connected group; not automatically an architectural error.
- `high_fan_in` / `high_fan_out`: degree at or above `--architecture-max-degree` (default 12), a *review candidate*, never a confirmed DIP/SRP violation.
- `configured_rule_violation`: a dependency-cruiser violation attributed to an actual declared rule. The monitor does not generate forbidden rules from directory names.

Dependency-cruiser rules belong in the **project's own dependency-cruiser configuration**. The analyzer does not create a new rule format. **Review its config and `--output-type json` compatibility** before enforcing in CI.

Architecture checks are opt-in. They require a valid dependency-cruiser executable. Missing or malformed output means unavailable/failed coverage, not a clean scan. Python adapter coverage is not implemented: it is explicitly unavailable, not silently skipped. The current graph scan is package-wide, even if other monitors target a smaller file selection.

Future follow-up (separate PR): link findings to actual functional/quality requirements only with precise source references; inferred business impacts must remain hypotheses, never fabricated requirements.
