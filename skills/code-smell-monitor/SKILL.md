---
name: code-smell-monitor
description: Build and run objective code quality smell monitoring for a repository. Use when Codex needs scoped, tool-based feedback on complexity, duplication, dead code, dependency coupling, type/static safety, security, dependency health, observability risks, or general maintainability signals for a small module, changed files, a package, or the whole repo.
---

# Code Smell Monitor

## Purpose

Use this skill to produce reproducible code-quality evidence for a repository. The monitor reports signals and suspected risks while leaving contextual judgment to the user.

## Quick Start

Run the bundled monitor from the target repository:

```bash
python3 /Users/admin/.codex/skills/code-smell-monitor/scripts/code_smell_monitor.py --repo . --scope path/to/module path/to/file.py
```

For a full repository pass:

```bash
python3 /Users/admin/.codex/skills/code-smell-monitor/scripts/code_smell_monitor.py --repo . --scope .
```

Use `--install missing` by default. It installs missing common tools for detected stacks. Use `--install never` when the environment must not be changed.

## Workflow

1. Choose the smallest meaningful scope first: changed files, touched module, or package boundary.
2. Run `scripts/code_smell_monitor.py` with that scope.
3. Read `code_smell_report.md` first, then inspect `raw/*.json` or `raw/*.txt` for exact tool output.
4. Treat type/static safety and security findings as higher priority than style-only findings.
5. Escalate to a wider scope only when the change affects shared abstractions, imports, package boundaries, build config, or dependency versions.
6. Re-run the same scoped command after changes and compare summaries.

## Scope Selection

Prefer this order:

- `--scope file1 file2`: for localized edits.
- `--scope package_or_module_dir`: for a cohesive module or package check.
- `--scope . --changed-only`: for changed tracked files from Git.
- `--scope .`: for architecture, dependency, security, or release-readiness checks.

Do not run whole-repo monitoring just because the script can. Focused reports are easier to inspect and compare.

## Outputs

The script writes reports under `--out` or `.codex/code_smell_monitor/<timestamp>/`:

- `code_smell_report.md`: human-readable summary, commands, exit codes, and ranked signals.
- `summary.json`: stack detection, tool availability, command metadata, and extracted headline metrics.
- `raw/`: exact tool outputs for auditability.

## Tool Policy

Use common external tools instead of hand-rolled pattern matching:

- Python: `ruff`, `radon`, `vulture`, `bandit`, `mypy`.
- JavaScript/TypeScript: project `lint` or `typecheck` scripts, `eslint`, `jscpd`, `madge`, `depcheck`, and package-manager audit.

Read `references/tool_matrix.md` when deciding whether to add another tool or interpret a smell category.

## Interpretation Rules

- Report suspected dead code, not certain dead code, in framework-heavy or plugin-based projects.
- Keep semantic responsibility issues as review prompts unless a tool gives direct evidence.
- Do not hide failed tool commands; failed checks are evidence about project setup.
- Preserve raw outputs so findings can be checked without rerunning tools.
