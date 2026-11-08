---
name: code-smell-monitor
description: Build and run objective code quality smell monitoring for a repository. Use when you need scoped, tool-based feedback on complexity, duplication, dead code, dependency coupling, type/static safety, security, dependency health, observability risks, or general maintainability signals for a small module, changed files, a package, or the whole repo.
---

# Code Smell Monitor

## Purpose

Produce reproducible code-quality **evidence**, then use repository-specific context to decide which findings deserve review. The bundled runner collects deterministic signals; **you**, the agent, own repository discovery, tool selection, source authority, interpretation, and the final issue-oriented report. No user-authored requirements manifest or configured architecture rules are prerequisites for an advisory scan.

Use judgment to adapt to repositories with different stacks and document systems. For interpretation details and evidence classification, read [references/agent-interpretation.md](references/agent-interpretation.md) when reporting architectural or requirements-aware findings.

## Quick Start

Run the bundled monitor from the target repository:

```bash
python3 ~/.agents/skills/code-smell-monitor/scripts/code_smell_monitor.py --repo . --scope path/to/module path/to/file.py
```

For optional architecture analysis (JavaScript/TypeScript package root or Python repository):

```bash
python3 ~/.agents/skills/code-smell-monitor/scripts/code_smell_monitor.py --repo . --scope . --architecture --install never
```

When dependency-cruiser is installed, this mode generates package-wide JS/TS dependency graph findings. Python uses a bundled static AST import adapter without executing target code. Mixed projects report both adapters. Cycles are structural facts; high fan-in/out are review candidates, not confirmed design violations. Only explicitly configured `error` rule violations are CI-blocking. Missing tools or unresolved imports produce unavailable or partial coverage, not a clean scan. See `references/architecture-analysis.md`.

Use `--architecture-only` to run architecture adapters without unrelated detectors. The legacy `--requirements path/to/requirements.json` flag is an **optional evidence-mapping adapter**, not a way to discover or interpret repository design intent. Do not ask the user to author that JSON to run a review. When legacy mappings cite documents above a nested package root, use `--workspace-root path/to/workspace` (the workspace must contain `--repo`). Its quote/hash/path checks do not establish decision authority or semantic correctness. Neither mapped nor agent-interpreted requirements alone trigger CI enforcement.

For a full repository pass:

```bash
python3 ~/.agents/skills/code-smell-monitor/scripts/code_smell_monitor.py --repo . --scope .
```

Use `--install never` in locked-down environments and in offline regression tests. The current CLI default `--install missing` may download tools; make sure network and environment changes are allowed before running.

## Dependencies and Installation

The monitor requires Python 3.10 or newer to run. It uses these external tools:

- Python repositories: `ruff`, `radon`, `vulture`, `bandit`, and `mypy`.
- JavaScript/TypeScript repositories: Node.js with `npm`/`npx`, plus the project's package manager when a lockfile or package script requires it. The application dependencies must already be installed for project-local lint, typecheck, and dependency resolution.

By default, `--install missing` checks for the Python tools and installs missing ones with `python3 -m pip install --user`. For JavaScript/TypeScript tools, it uses a local `node_modules/.bin` tool first, then a tool on `PATH`, and otherwise fetches the tool through `npx --yes` for that run. This requires network access. The installation commands and their exit codes are recorded in the report.

The monitor does not install the target project's own dependencies. Install those before running checks when the project needs them:

```bash
npm ci                          # package-lock.json
pnpm install --frozen-lockfile  # pnpm-lock.yaml
yarn install --immutable        # yarn.lock
```

Use the command appropriate for the repository and do not run all three. For a locked-down or offline environment, use `--install never`; missing monitor tools are then reported as failed checks instead of being installed.

## Workflow

1. **Discover before selecting tools.** Inspect the repository structure, package/build roots, language stacks, existing check commands and analyzer configurations, and any agent/project instructions. Identify what is actually in scope; never assume a fixed JavaScript/Python-only script covers every repository.
2. **Discover relevant project intent without assuming a documentation framework.** Inspect the repository's own instructions, tracked decisions, source, tests, configuration, and navigation to determine what evidence exists and which sources actually govern the area being reviewed. Repositories may use unconventional names, formats, directories, approval processes, or no design documents at all. Determine each source's applicability, provenance, currency, and authority from repository evidence; do not presume a fixed hierarchy or label vocabulary. Surface conflicts or missing authority rather than inventing rules. Relevant documents may live above package roots.
3. **Select the smallest meaningful analysis scope and available tools.** Prefer the repository's established linters, build scripts and graph analyzers. Use `scripts/code_smell_monitor.py` for supported deterministic checks; use another existing analyzer directly when the bundled runner cannot cover the stack. Install tools only with permitted environment changes.
4. **Execute and assess coverage.** Inspect detector statuses, effective package roots, unresolved imports, omitted source files and raw evidence. Missing or failed checks mean incomplete coverage, never clean findings. Graph-wide checks may cover a wider scope than file-level checks.
5. **Interpret structural findings against real code and the project's own intent.** Distinguish measured facts from universal review candidates; investigate actual module responsibilities before relating a finding to any applicable source. Cite code locations, import/tool evidence, and exact source paths/locations where available. Explain plausible impact, alternatives, and discriminating checks. Distinguish an enforceable current decision from proposed, uncertain, historical, or superseded intent using the repository's own conventions, not preselected status labels.
6. **Report actionable, evidence-backed issues rather than verification claims.** Group repeated symptoms, prioritize consequential candidates, preserve uncertainty, and propose follow-up investigation/verification separately. No semantic interpretation alone constitutes a configured-rule or behavioral violation. Issue creation requires an explicit request.
7. **Re-run objective tools on the same scope after changes** and compare like-for-like reports. Never claim the skill has automatically created requirement mappings, enforced an undocumented design rule, or proved behavior.

**Done when:** Each surfaced issue has observable evidence, a confidence/epistemic label, grounded repository context when available, and the unverified portion stated; coverage gaps and document-authority gaps are visible. A repository with no authoritative requirements can still receive a useful structural report.

## Scope Selection

Prefer this order:

- `--scope file1 file2`: for localized edits.
- `--scope package_or_module_dir`: for a cohesive module or package check.
- `--scope . --changed-only`: for changed tracked files from Git.
- `--scope .`: for architecture, dependency, security, or release-readiness checks.

Do not run whole-repo monitoring just because the script can. Focused reports are easier to inspect and compare.

## Outputs

The script writes reports under `--out` or `.code-smell-monitor/<timestamp>/`:

- `code_smell_report.md`: human-readable summary, category coverage, commands, exit codes, and ranked signals.
- `summary.json`: optional `architecture` results when `--architecture` is requested; stack detection, detector `status` (`clean`, `findings`, `failed`, `unavailable`, `timed_out`), effective analysis scope, category coverage, command metadata, and headline metrics. Nonzero analyzer exit codes can mean findings rather than an execution failure.
- `raw/`: exact tool outputs for auditability.
- Exclude `.code-smell-monitor/` from local Git tracking as needed.

## Tool Policy

Use common external tools instead of hand-rolled pattern matching:

- Python: `ruff`, `radon`, `vulture`, `bandit`, `mypy`.
- JavaScript/TypeScript: project `lint` or `typecheck` scripts, `eslint`, `tsc --noEmit`, `jscpd`, `knip`, `madge`, `depcheck`, and package-manager audit.
- JavaScript/TypeScript dead code: use `knip` for unused files, exports, types, and dependencies. Treat findings as suspected when routing, dynamic imports, registries, plugin hooks, or framework conventions can hide consumers.
- Hard-coded secrets: use Gitleaks or an equivalent repository secret scanner when available. A regex search or a clean result from another tool is not evidence that hard-coded secrets are absent.
- The bundled monitor records `gitleaks` as covered, failed, or unavailable. Treat exit `1` as findings requiring inspection and exit `127` as unavailable coverage.

For nested applications or monorepos, run the monitor once per package root so project config, local binaries, lockfiles, and package scripts resolve in the correct directory. Aggregate the reports only after each package pass has a valid coverage status.

Read `references/tool_matrix.md` when deciding whether to add another tool or interpret a smell category. For cross-repo agent-level interpretation examples and boundary tests, read `references/agent-interpretation.md`.

## Interpretation Rules

- An agent's source-backed architectural interpretation is **not** the same as the optional JSON adapter's path-match association; label them separately.
- Treat proposals and future-state decisions as intent, not automatically as current enforcement policy. Use repository evidence to distinguish known migration debt from newly introduced violations.
- Do not manufacture an authoritative design record, responsibility mapping, requirement, or enforcement contract from filenames, layout, or language/framework conventions.

- Report suspected dead code, not certain dead code, in framework-heavy or plugin-based projects.
- Keep semantic responsibility issues as review prompts unless a tool gives direct evidence.
- Do not hide failed tool commands; failed checks are evidence about project setup.
- Do not claim a complete scan from headline counts alone. Report each smell category as covered, failed, unavailable, or not applicable, with the command and package root used.
- Preserve raw outputs so findings can be checked without rerunning tools.

## Invocation contract

Another skill invokes this one through the versioned Request/Response in [references/call-contract.md](references/call-contract.md) (checkable projection: `contract.json`). It maps each Request field to a CLI flag and defines one result `status` (`complete`, `incomplete`, `blocking_violations`, `error`) from the exit code and `summary.json`, so callers never treat incomplete coverage as a clean result.
