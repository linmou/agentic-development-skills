# Code Smell Monitor Tool Matrix

Intent: Map smell requirements to common deterministic tools so the monitor stays objective and avoids fake certainty.

## Complexity

- Python: `radon cc` for cyclomatic complexity, `radon mi` for maintainability index, `ruff` rule families for long/complex functions when configured.
- JavaScript/TypeScript: `eslint` with project rules when available. Without project config, treat complexity output as incomplete rather than inventing metrics.

## Duplication

- Cross-language: `jscpd` for exact and near-duplicate blocks.
- Semantic duplication is a review prompt only. Use repeated tool findings, file names, and recurring function names as evidence.

## Dead or Unused Code

- Python: `ruff` for unused imports and variables, `vulture` for suspected unused functions/classes/modules.
- JavaScript/TypeScript: `eslint` for unused variables/imports, `depcheck` for suspected unused dependencies.
- Dynamic imports, decorators, routing, registries, plugin hooks, and reflection make dead-code findings suspect.

## Coupling and Dependencies

- JavaScript/TypeScript: `madge` for circular dependencies and dependency graph evidence.
- Python: prefer import-linter or pydeps only when already present in the project; the bundled script avoids forcing a project-specific architecture model.

## Type and Static Safety

- Python: `mypy`.
- JavaScript/TypeScript: package `typecheck` script when available, otherwise `tsc --noEmit` when TypeScript is detected.

## Security and Dependency Health

- Python: `bandit` for code-level security. Use the project dependency manager audit only if already configured.
- JavaScript/TypeScript: `npm audit`, `pnpm audit`, or `yarn npm audit` according to the lockfile/package manager.
- Separate dependency vulnerabilities from code-level unsafe patterns.

## Observability and Debuggability

- Use lint and security tools for obvious unsafe constructs.
- Treat swallowed exceptions, empty handlers, print/debugger usage, and missing timeouts as review prompts unless a configured lint rule reports them.

## Installation Boundary

- Install missing monitor tools only for detected stacks.
- Prefer local project tools and scripts first.
- Use `--install never` for locked-down environments.
- Do not install heavyweight or language-server-specific tools unless the project stack makes them relevant.
