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

## Agent-led architectural interpretation (default)

The script emits structural evidence, **not** a verdict against the repository's design decisions. The agent reads [agent-interpretation.md](agent-interpretation.md), discovers whichever authoritative sources actually exist in the target repository (including code-level policies or no written design records), examines the relevant implementation, and identifies source authority and currency using local conventions. No named workflow, filename, status vocabulary, or JSON manifest is required for interpretation.

Report an absent optional requirements manifest as `not_provided` for the machine evidence adapter only; it does not mean agent interpretation was not performed.

## Optional requirement evidence adapter (legacy API)

Pass `--requirements requirements.json` with `--architecture` or `--architecture-only` **only** when a preauthored v1 JSON mapping is available or a downstream machine consumer explicitly needs one. This JSON is **not** the input format for arbitrary project documents or a required output of the skill. It does not discover documents, interpret semantics, or decide whether the document is approved.

Paths in `modules` are relative to the analyzed `--repo`. Source `path` references are relative to `--workspace-root`, which defaults to `--repo`; the workspace must contain the analyzed repository. This allows a package-local analysis to cite a parent-workspace document without altering analyzer resolution or accepting path traversal. The manifest path itself is resolved from the caller's working directory.

The adapter requires explicit existing module files, `kind: functional|quality`, exact source lines, rationale and uncertainty, e.g.:

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

An analyst supplies the source and mapping. Names or directories do not prove responsibilities. The validator verifies quote text, line bounds, hash, module existence and allowed paths; it does **not** establish source authority, document status, or semantic correctness. Only findings touching a mapped source/target/cycle member get associations, labeled `impact_hypothesis` with `confidence: association_only`. Missing mappings remain unmapped; absent manifest returns `not_provided`. Invalid/stale quotes, missing uncertainty, escaping paths and duplicate IDs fail. Associations never change CI enforcement.

