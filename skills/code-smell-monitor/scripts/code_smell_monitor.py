#!/usr/bin/env python3
# Purpose: Run scoped, tool-based code smell monitoring for a repository and preserve objective reports.

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


PYTHON_TOOLS = {
    "ruff": ["ruff"],
    "radon": ["radon"],
    "vulture": ["vulture"],
    "bandit": ["bandit"],
    "mypy": ["mypy"],
}

PYTHON_PIP_PACKAGES = {
    "ruff": "ruff",
    "radon": "radon",
    "vulture": "vulture",
    "bandit": "bandit",
    "mypy": "mypy",
}

NODE_NPX_PACKAGES = {
    "eslint": "eslint",
    "jscpd": "jscpd",
    "madge": "madge",
    "depcheck": "depcheck",
    "tsc": "typescript",
}

PY_EXTENSIONS = {".py"}
JS_EXTENSIONS = {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts"}
IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "coverage",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run scoped code smell monitor tools.")
    parser.add_argument("--repo", default=".", help="Repository root.")
    parser.add_argument("--scope", nargs="+", default=["."], help="Files or directories to inspect, relative to repo.")
    parser.add_argument("--out", default="", help="Output directory. Defaults to .codex/code_smell_monitor/<timestamp>.")
    parser.add_argument("--install", choices=["missing", "never"], default="missing", help="Install missing common tools for detected stacks.")
    parser.add_argument("--changed-only", action="store_true", help="Replace scope with git changed files under the repo.")
    parser.add_argument("--fail-on-tool-error", action="store_true", help="Exit non-zero when any tool cannot run cleanly.")
    return parser.parse_args()


def run_command(cmd: list[str], cwd: Path, timeout: int = 300) -> dict[str, Any]:
    started = time.time()
    try:
        completed = subprocess.run(
            cmd,
            cwd=str(cwd),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        return {
            "cmd": cmd,
            "exit_code": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "duration_seconds": round(time.time() - started, 3),
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "cmd": cmd,
            "exit_code": 124,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or f"Timed out after {timeout} seconds",
            "duration_seconds": round(time.time() - started, 3),
            "timed_out": True,
        }


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def repo_files(repo: Path, scope_paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for scope in scope_paths:
        if scope.is_file():
            files.append(scope)
            continue
        if not scope.exists():
            continue
        for root, dirs, names in os.walk(scope):
            dirs[:] = [item for item in dirs if item not in IGNORED_DIRS]
            for name in names:
                path = Path(root) / name
                try:
                    path.relative_to(repo)
                except ValueError:
                    continue
                files.append(path)
    return sorted(set(files))


def relative_args(repo: Path, paths: list[Path]) -> list[str]:
    values: list[str] = []
    for path in paths:
        try:
            values.append(str(path.relative_to(repo)))
        except ValueError:
            values.append(str(path))
    return values


def git_changed_files(repo: Path) -> list[Path]:
    result = run_command(["git", "diff", "--name-only", "HEAD"], repo, timeout=60)
    if result["exit_code"] != 0:
        return []
    paths: list[Path] = []
    for line in result["stdout"].splitlines():
        candidate = repo / line.strip()
        if candidate.exists() and candidate.is_file():
            paths.append(candidate)
    return paths


def detect_stack(repo: Path, files: list[Path]) -> dict[str, bool]:
    names = {path.name for path in repo.iterdir()} if repo.exists() else set()
    suffixes = {path.suffix for path in files}
    return {
        "python": bool(PY_EXTENSIONS & suffixes) or bool({"pyproject.toml", "setup.py", "requirements.txt"} & names),
        "javascript": bool(JS_EXTENSIONS & suffixes) or "package.json" in names,
        "typescript": bool({".ts", ".tsx", ".mts", ".cts"} & suffixes) or "tsconfig.json" in names,
    }


def package_json(repo: Path) -> dict[str, Any]:
    data = load_json(repo / "package.json")
    return data if isinstance(data, dict) else {}


def package_manager(repo: Path) -> str:
    if (repo / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (repo / "yarn.lock").exists():
        return "yarn"
    return "npm"


def executable_exists(name: str) -> bool:
    return shutil.which(name) is not None


def install_python_tools(repo: Path, tools: list[str]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    missing = [tool for tool in tools if not executable_exists(tool)]
    if not missing:
        return results
    packages = [PYTHON_PIP_PACKAGES[tool] for tool in missing]
    results.append(run_command([sys.executable, "-m", "pip", "install", "--user", *packages], repo, timeout=600))
    return results


def npx_cmd(package: str, binary: str) -> list[str]:
    return ["npx", "--yes", "-p", package, binary]


def write_raw(raw_dir: Path, name: str, result: dict[str, Any]) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / f"{name}.stdout.txt").write_text(result["stdout"], encoding="utf-8")
    (raw_dir / f"{name}.stderr.txt").write_text(result["stderr"], encoding="utf-8")
    meta = {key: value for key, value in result.items() if key not in {"stdout", "stderr"}}
    (raw_dir / f"{name}.meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")


def maybe_json_file(raw_dir: Path, name: str, result: dict[str, Any]) -> Any:
    output_path = raw_dir / f"{name}.stdout.txt"
    parsed = load_json(output_path)
    if parsed is not None:
        (raw_dir / f"{name}.json").write_text(json.dumps(parsed, indent=2), encoding="utf-8")
    return parsed


def run_python_checks(repo: Path, paths: list[str], raw_dir: Path, install_mode: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    install_results: list[dict[str, Any]] = []
    if install_mode == "missing":
        install_results = install_python_tools(repo, list(PYTHON_TOOLS))

    commands = [
        ("ruff", ["ruff", "check", "--output-format", "json", *paths]),
        ("radon_cc", ["radon", "cc", "-s", "-j", *paths]),
        ("radon_mi", ["radon", "mi", "-j", *paths]),
        ("vulture", ["vulture", *paths, "--min-confidence", "80"]),
        ("bandit", ["bandit", "-q", "-r", *paths, "-f", "json"]),
        ("mypy", ["mypy", *paths]),
    ]
    results: list[dict[str, Any]] = []
    for name, cmd in commands:
        if not executable_exists(cmd[0]):
            result = {"cmd": cmd, "exit_code": 127, "stdout": "", "stderr": f"{cmd[0]} not found", "duration_seconds": 0, "timed_out": False}
        else:
            result = run_command(cmd, repo, timeout=600)
        write_raw(raw_dir, name, result)
        maybe_json_file(raw_dir, name, result)
        results.append({"name": name, **result})
    return install_results, results


def node_runner(repo: Path, tool: str, args: list[str], install_mode: str) -> list[str] | None:
    local_bin = repo / "node_modules" / ".bin" / tool
    if local_bin.exists():
        return [str(local_bin), *args]
    if executable_exists(tool):
        return [tool, *args]
    if install_mode == "never":
        return None
    return [*npx_cmd(NODE_NPX_PACKAGES[tool], tool), *args]


def run_node_script(repo: Path, script: str) -> list[str]:
    manager = package_manager(repo)
    if manager == "pnpm":
        return ["pnpm", "run", script]
    if manager == "yarn":
        return ["yarn", script]
    return ["npm", "run", script]


def audit_command(repo: Path) -> list[str]:
    manager = package_manager(repo)
    if manager == "pnpm":
        return ["pnpm", "audit", "--json"]
    if manager == "yarn":
        return ["yarn", "npm", "audit", "--json"]
    return ["npm", "audit", "--json"]


def run_js_checks(repo: Path, paths: list[str], raw_dir: Path, has_typescript: bool, install_mode: str) -> list[dict[str, Any]]:
    package = package_json(repo)
    scripts = package.get("scripts", {})
    scripts = scripts if isinstance(scripts, dict) else {}

    commands: list[tuple[str, list[str] | None, int]] = []
    if "lint" in scripts:
        commands.append(("package_lint", run_node_script(repo, "lint"), 600))
    if paths:
        commands.append(("eslint", node_runner(repo, "eslint", ["--format", "json", *paths], install_mode), 600))
        commands.append(("jscpd", node_runner(repo, "jscpd", ["--reporters", "json", "--output", str(raw_dir / "jscpd_report"), *paths], install_mode), 600))
        commands.append(("madge_circular", node_runner(repo, "madge", ["--circular", "--json", *paths], install_mode), 600))
    commands.append(("depcheck", node_runner(repo, "depcheck", ["--json"], install_mode), 600))
    commands.append(("package_audit", audit_command(repo), 600))
    if "typecheck" in scripts:
        commands.append(("package_typecheck", run_node_script(repo, "typecheck"), 600))
    elif has_typescript:
        commands.append(("tsc_no_emit", node_runner(repo, "tsc", ["--noEmit"], install_mode), 600))

    results: list[dict[str, Any]] = []
    for name, cmd, timeout in commands:
        if cmd is None:
            result = {"cmd": [name], "exit_code": 127, "stdout": "", "stderr": f"{name} not found", "duration_seconds": 0, "timed_out": False}
        else:
            result = run_command(cmd, repo, timeout=timeout)
        write_raw(raw_dir, name, result)
        maybe_json_file(raw_dir, name, result)
        results.append({"name": name, **result})
    return results


def extract_headlines(raw_dir: Path) -> dict[str, Any]:
    headlines: dict[str, Any] = {}

    ruff = load_json(raw_dir / "ruff.json")
    if isinstance(ruff, list):
        headlines["ruff_findings"] = len(ruff)
        headlines["ruff_top_codes"] = top_counts(item.get("code", "unknown") for item in ruff if isinstance(item, dict))

    radon_cc = load_json(raw_dir / "radon_cc.json")
    if isinstance(radon_cc, dict):
        blocks: list[dict[str, Any]] = []
        for file_name, values in radon_cc.items():
            if isinstance(values, list):
                for item in values:
                    if isinstance(item, dict):
                        blocks.append({"file": file_name, "name": item.get("name"), "complexity": item.get("complexity"), "rank": item.get("rank")})
        blocks.sort(key=lambda item: item.get("complexity") or 0, reverse=True)
        headlines["highest_complexity"] = blocks[:10]

    bandit = load_json(raw_dir / "bandit.json")
    if isinstance(bandit, dict):
        findings = bandit.get("results", [])
        headlines["bandit_findings"] = len(findings) if isinstance(findings, list) else 0

    eslint = load_json(raw_dir / "eslint.json")
    if isinstance(eslint, list):
        error_count = 0
        warning_count = 0
        for item in eslint:
            if isinstance(item, dict):
                error_count += int(item.get("errorCount", 0) or 0)
                warning_count += int(item.get("warningCount", 0) or 0)
        headlines["eslint_errors"] = error_count
        headlines["eslint_warnings"] = warning_count

    madge = load_json(raw_dir / "madge_circular.json")
    if isinstance(madge, list):
        headlines["circular_dependencies"] = len(madge)
        headlines["circular_dependency_samples"] = madge[:10]

    depcheck = load_json(raw_dir / "depcheck.json")
    if isinstance(depcheck, dict):
        headlines["unused_dependencies"] = depcheck.get("dependencies", [])
        headlines["missing_dependencies"] = depcheck.get("missing", {})

    return headlines


def top_counts(values: Any) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for value in values:
        counts[str(value)] = counts.get(str(value), 0) + 1
    return [{"name": key, "count": value} for key, value in sorted(counts.items(), key=lambda item: item[1], reverse=True)[:10]]


def write_report(out_dir: Path, summary: dict[str, Any], results: list[dict[str, Any]], install_results: list[dict[str, Any]]) -> None:
    lines: list[str] = []
    lines.append("# Code Smell Monitor Report")
    lines.append("")
    lines.append(f"- repo: `{summary['repo']}`")
    lines.append(f"- scope: `{', '.join(summary['scope'])}`")
    lines.append(f"- detected stacks: `{', '.join(name for name, enabled in summary['stack'].items() if enabled) or 'none'}`")
    lines.append(f"- output: `{summary['out_dir']}`")
    lines.append("")
    lines.append("## Headline Signals")
    if summary["headlines"]:
        for key, value in summary["headlines"].items():
            rendered = json.dumps(value, indent=2) if isinstance(value, (list, dict)) else str(value)
            lines.append(f"- `{key}`: {rendered}")
    else:
        lines.append("- No structured headline metrics extracted. Inspect raw outputs.")
    lines.append("")
    lines.append("## Tool Results")
    for result in results:
        lines.append(f"- `{result['name']}` exit `{result['exit_code']}` in `{result['duration_seconds']}`s: `{' '.join(result['cmd'])}`")
    if install_results:
        lines.append("")
        lines.append("## Installation Commands")
        for result in install_results:
            lines.append(f"- exit `{result['exit_code']}`: `{' '.join(result['cmd'])}`")
    lines.append("")
    lines.append("## Review Prompts")
    lines.append("- Check highest-complexity functions before extracting abstractions.")
    lines.append("- Treat dead-code reports as suspected when routing, decorators, plugins, or dynamic imports exist.")
    lines.append("- Investigate circular dependencies before moving shared code.")
    lines.append("- Keep security/dependency findings separate from maintainability findings.")
    lines.append("- Re-run the same scope after changes and compare this report with the new one.")
    lines.append("")
    (out_dir / "code_smell_report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    repo = Path(args.repo).resolve()
    if not repo.exists():
        print(f"repo does not exist: {repo}", file=sys.stderr)
        return 2

    if args.changed_only:
        scoped_paths = git_changed_files(repo)
    else:
        scoped_paths = [(repo / item).resolve() for item in args.scope]

    files = repo_files(repo, scoped_paths)
    if not files:
        print("no files found for scope", file=sys.stderr)
        return 2

    stack = detect_stack(repo, files)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    out_dir = Path(args.out).resolve() if args.out else repo / ".codex" / "code_smell_monitor" / timestamp
    raw_dir = out_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    scope_args = relative_args(repo, scoped_paths)
    py_paths = relative_args(repo, [path for path in scoped_paths if path.is_dir() or path.suffix in PY_EXTENSIONS])
    js_paths = relative_args(repo, [path for path in scoped_paths if path.is_dir() or path.suffix in JS_EXTENSIONS])

    install_results: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []

    if stack["python"] and py_paths:
        py_install_results, py_results = run_python_checks(repo, py_paths, raw_dir, args.install)
        install_results.extend(py_install_results)
        results.extend(py_results)
    if stack["javascript"]:
        results.extend(run_js_checks(repo, js_paths, raw_dir, stack["typescript"], args.install))

    summary = {
        "repo": str(repo),
        "scope": scope_args,
        "out_dir": str(out_dir),
        "stack": stack,
        "install_mode": args.install,
        "headlines": extract_headlines(raw_dir),
        "results": [{key: value for key, value in item.items() if key not in {"stdout", "stderr"}} for item in results],
        "install_results": [{key: value for key, value in item.items() if key not in {"stdout", "stderr"}} for item in install_results],
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_report(out_dir, summary, results, install_results)

    print(str(out_dir))
    if args.fail_on_tool_error and any(item["exit_code"] not in (0,) for item in results + install_results):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
