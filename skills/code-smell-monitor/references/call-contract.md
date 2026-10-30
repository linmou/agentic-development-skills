# Call Contract: Code Smell Monitor

**Intent:** Let any caller run scoped smell monitoring and read one result status, without re-deriving meaning from exit codes and coverage fields.

## Version

`1.0.0`. [`../contract.json`](../contract.json) is the checkable projection of this file; callers declare `code-smell-monitor@^1.0.0`. Add optional fields for compatible changes. Removing a field or status, or changing a status rule, is a new major version.

## Request

Each field maps to one CLI flag of `scripts/code_smell_monitor.py`.

| Field | Flag | Class | Required / default | Meaning |
|---|---|---|---|---|
| `repo` | `--repo` | content | optional; `.` | Repository root. |
| `scope` | `--scope` | content | required unless `changed_only`; `.` | Files or directories inside `repo`. Choose the smallest meaningful scope. |
| `changed_only` | `--changed-only` | control | optional; `false` | Replace `scope` with Git-changed files. |
| `install` | `--install` | control | optional; `missing` | `missing` may install Python tools with `pip --user` and fetch JS tools with `npx`, which needs network. `never` reports missing tools as unavailable coverage. |
| `out` | `--out` | output | optional; `<repo>/.code-smell-monitor/<timestamp>/` | Report directory. |
| `architecture` | `--architecture` | control | optional; `false` | Add architecture graph analysis. |
| `architecture_only` | `--architecture-only` | control | optional; `false` | Architecture adapters only; implies `architecture`. |
| `requirements` | `--requirements` | seed | optional; requires `architecture` | Requirement-to-module mapping file. |
| `architecture_max_degree` | `--architecture-max-degree` | control | optional; tool default | Fan-in/out review threshold; positive. |
| `fail_on_tool_error` | `--fail-on-tool-error` | control | optional; `false` | Exit non-zero when coverage is incomplete. Does not change `status`. |

Precedence: `changed_only` replaces `scope`; `architecture_only` implies `architecture`.

### Minimal third-party request

```json
{ "scope": ["src/payments"] }
```

```bash
python3 <skill_dir>/scripts/code_smell_monitor.py --repo . --scope src/payments
```

## Response

| Field | Condition | Meaning |
|---|---|---|
| `status` | always | `complete`, `incomplete`, `blocking_violations`, or `error` (rules below). |
| `exit_code` | always | Process exit code. |
| `out_dir` | unless `error` before analysis | Printed on stdout; holds `summary.json`, `code_smell_report.md`, `raw/`. |
| `coverage` | unless `error` before analysis | `summary.json` `coverage`: `complete` and per-category status. |
| `errors` | always; `[]` when none | stderr lines starting `ERROR` or explaining exit `2`. |

### Status rules

Apply in order; the first match wins.

| Status | Rule |
|---|---|
| `error` | Exit `2`: invalid request (missing repo or scope, scope outside the repo, no files, bad threshold, `requirements` without `architecture`) or failed requirement interpretation. No result is trustworthy. |
| `blocking_violations` | `summary.json` `architecture.enforced_violations` > 0. Only explicitly configured `error` rules count; cycles and high fan-in/out are review candidates, not violations. |
| `incomplete` | `coverage.complete` is `false`, or `architecture.status` is not `covered` when architecture was requested. Findings are real; absence of findings is not evidence of a clean scope. |
| `complete` | Otherwise. Findings may still exist; read the report. |

`fail_on_tool_error` only changes the exit code (to `1` for `incomplete`); use the rules above, not the exit code alone, to tell `incomplete` from `blocking_violations`.

## Writes

This skill alone writes the report directory (`out`, or `<repo>/.code-smell-monitor/<timestamp>/`). With `install: missing` it may also install monitor tools into the user's Python environment; it never installs the target project's dependencies and never edits source files.

## Caller obligations

Read `status` before interpreting findings. Treat `incomplete` as partial evidence, never as clean. Compare two runs only when they used the same request (scope, flags, `install`). Do not edit the report directory.
