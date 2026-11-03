# Universal architecture analysis

Run `--architecture` from a JS/TS package root or Python repository. Use `--architecture-only` to avoid unrelated checks. Install dependency-cruiser and its TypeScript parser dependency for TS projects, or use `--install missing` to allow an ephemeral npx download. Prefer `--install never` in CI and locked-down environments. Install target project dependencies with its frozen-lockfile workflow before JS/TS resolution.

The monitor runs dependency-cruiser on the package root, preserving `raw/architecture_depcruise.stdout.txt`, `raw/architecture_depcruise.meta.json`, and a normalized `raw/architecture_summary.json`. The `summary.json` `architecture` property also includes status, actual scope, graph sizes, and findings.

- `dependency_cycle`: observable strongly connected group; not automatically an architectural error.
- `high_fan_in` / `high_fan_out`: degree at or above `--architecture-max-degree` (default 12), a *review candidate*, never a confirmed DIP/SRP violation.
- `configured_rule_violation`: a dependency-cruiser violation attributed to an actual declared rule. The monitor does not generate forbidden rules from directory names.

Dependency-cruiser rules belong in the **project's own dependency-cruiser configuration**. The analyzer does not create a new rule format. **Review its config and `--output-type json` compatibility** before enforcing in CI.

Architecture checks are opt-in. The JS/TS adapter requires dependency-cruiser. Without a project configuration, the monitor passes `--no-config` and creates no rules. A present `tsconfig.json` is passed to the resolver. Dependency/build directories are excluded and `node_modules` is not followed. Existing project config can restrict scope further; inspect raw command/output metadata. Unresolved imports mean partial coverage. Missing or malformed output means unavailable/failed coverage, not a clean scan. Graph scans cover the package/repository, even if other monitors target a smaller file selection.

## Python adapter

The bundled AST adapter parses `.py` files without importing project code. It indexes repository-root and `src/` layouts, absolute/relative imports and package initializers. It emits the common graph format into `raw/architecture_python.json`, plus line-level import resolution, parser errors, exclusions and limitations in `raw/architecture_python_summary.json`. Conditional/type-only imports are potential edges. Ambiguous names, recognized dynamic import calls, unresolved imports, unreadable directories and syntax errors mean partial coverage. Standard-library imports are recognized without executing them. External/unresolved imports remain explicit evidence: runtime path changes, arbitrary import hooks and namespace-package behavior are outside this static adapter's completeness claim. A package with no Python files is unavailable. Symlinks and dependency/build directories are excluded. This adapter reports structural cycles/degrees only; it does not evaluate dependency-cruiser rules against Python.

Mixed projects preserve per-adapter statuses and findings. One successful adapter cannot hide another unavailable adapter. `--fail-on-tool-error` fails on incomplete architecture coverage; without that flag incomplete coverage is a warning. Metrics and requirement associations never trigger enforcement. Raw summaries and the Markdown report preserve the actual analysis scope and limitations.

## Requirement-aware interpretation

Pass `--requirements requirements.json` with `--architecture` or `--architecture-only`. Paths inside the manifest are relative to `--repo`; the manifest path itself is relative to the calling directory. Version 1 requires explicit existing module files, requirement type, exact source lines, mapping rationale and uncertainty:

```json
{
  "version": 1,
  "requirements": [{
    "id": "FR-007",
    "kind": "functional",
    "source": {
      "path": "docs/requirements.md",
      "line_start": 12,
      "line_end": 12,
      "quote": "Learner progress must survive reloads."
    },
    "modules": ["src/progress.ts"],
    "rationale": "Dependencies of progress persistence deserve lifecycle review.",
    "uncertainty": "Coupling alone does not demonstrate lost progress; validate reload behavior."
  }]
}
```

Use `kind: "quality"` for an explicitly documented quality requirement. Do not relabel an inferred benefit as a requirement. An analyst supplies the mapping after reading the source and implementation; names and directories do not establish responsibility or violation. Check whether the quoted source is authoritative and current, especially when a spec contains historical sections. Quote verification does not establish authority.

Only findings touching an explicitly mapped source, target or cycle member receive associations. Each association retains finding ID, structural evidence, requirement ID, exact source and SHA-256, rationale and uncertainty, with `classification: impact_hypothesis` and `confidence: association_only`. Missing mappings leave findings unmapped; absent requirements report `not_provided`. No findings does not prove requirement satisfaction. JSON and Markdown preserve source records and associations. Invalid/stale quotes, escaping paths, duplicate IDs or missing uncertainty produce a failed report and exit 2. Requirements never change configured rule enforcement.


## Issue #14: Configured Python architecture contracts

The AST adapter always remains available for discovery. When a project has explicit Import Linter contracts in `.importlinter`, `setup.cfg`, or `pyproject.toml`, install `import-linter` and run `--architecture-only --install never`. The monitor runs `lint-imports --config <file>` from the repository root, retains raw output and records contract coverage separately under `architecture.python_contracts`. A recognized broken-contract summary is enforced; missing tools and ambiguous output are incomplete, never clean. No contracts are synthesized from directory names.

Graph coverage records unresolved imports, files omitted from the dependency-cruiser graph, and TypeScript files omitted from the graph. Unresolved third-party, test-framework, Deno, or dynamic imports stay visible as partial coverage. Mixed-language results retain individual adapter statuses. Only explicit configured contracts are enforceable; graph metrics and source-mapped requirement impacts remain advisory.
