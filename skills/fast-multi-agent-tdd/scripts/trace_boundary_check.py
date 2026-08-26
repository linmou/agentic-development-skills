#!/usr/bin/env python3
# Purpose: run a command under strace or dtruss and summarize whether high-risk runtime boundaries were crossed.

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable


HIGH_RISK_KEYS = (
    "process_exec",
    "process_spawn",
    "network_connect",
    "filesystem_write",
)


def select_tracer(
    *,
    tracer_name: str,
    platform_name: str,
    which: Callable[[str], str | None],
) -> str:
    if tracer_name in {"strace", "dtruss"}:
        return tracer_name
    if tracer_name != "auto":
        raise ValueError(f"Unsupported tracer: {tracer_name}")
    if platform_name.startswith("linux") and which("strace"):
        return "strace"
    if platform_name == "darwin" and which("dtruss"):
        return "dtruss"
    raise RuntimeError("Could not auto-select tracer. Install strace or dtruss, or pass --tracer explicitly.")


def build_trace_command(
    *,
    tracer_name: str,
    trace_path: Path,
    target_command: list[str],
) -> list[str]:
    if tracer_name == "strace":
        return [
            "strace",
            "-f",
            "-o",
            str(trace_path),
            "-e",
            "trace=execve,connect,open,openat,clone,fork,vfork",
            *target_command,
        ]
    if tracer_name == "dtruss":
        return [
            "dtruss",
            "-f",
            "-o",
            str(trace_path),
            *target_command,
        ]
    raise ValueError(f"Unsupported tracer: {tracer_name}")


def _empty_event_counts() -> dict[str, int]:
    return {
        "process_exec": 0,
        "process_spawn": 0,
        "network_connect": 0,
        "filesystem_write": 0,
        "filesystem_open": 0,
    }


def _looks_like_strace_write(line: str) -> bool:
    if "open(" not in line and "openat(" not in line:
        return False
    markers = ("O_WRONLY", "O_RDWR", "O_CREAT", "O_TRUNC", "O_APPEND")
    return any(marker in line for marker in markers)


def _extract_dtruss_flags(line: str) -> int | None:
    if "open(" not in line and "open_nocancel(" not in line and "openat(" not in line:
        return None
    try:
        inner = line.split("(", 1)[1].rsplit(")", 1)[0]
    except IndexError:
        return None
    parts = [part.strip() for part in inner.split(",")]
    if len(parts) < 2:
        return None
    raw = parts[1]
    try:
        return int(raw, 0)
    except ValueError:
        return None


def _looks_like_dtruss_write(line: str) -> bool:
    flags = _extract_dtruss_flags(line)
    if flags is None:
        return False
    write_mask = 0x1 | 0x2 | 0x8 | 0x200 | 0x400
    return bool(flags & write_mask)


def parse_trace_file(*, trace_path: Path, tracer_name: str) -> dict[str, object]:
    event_counts = _empty_event_counts()
    for raw_line in trace_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if "execve(" in line:
            event_counts["process_exec"] += 1
        if "connect(" in line:
            event_counts["network_connect"] += 1
        if "clone(" in line or "fork(" in line or "vfork(" in line or "posix_spawn(" in line:
            event_counts["process_spawn"] += 1
        if "open(" in line or "openat(" in line or "open_nocancel(" in line:
            event_counts["filesystem_open"] += 1
        if tracer_name == "strace" and _looks_like_strace_write(line):
            event_counts["filesystem_write"] += 1
        if tracer_name == "dtruss" and _looks_like_dtruss_write(line):
            event_counts["filesystem_write"] += 1
    crossed = [key for key in HIGH_RISK_KEYS if event_counts[key] > 0]
    return {
        "trace_path": str(trace_path),
        "tracer": tracer_name,
        "event_counts": event_counts,
        "crossed_categories": crossed,
        "high_risk_boundary_crossed": bool(crossed),
    }


def _write_payload(*, payload: dict[str, object], json_out: Path | None) -> None:
    rendered = json.dumps(payload, indent=2, sort_keys=True)
    print(rendered)
    if json_out is not None:
        json_out.write_text(rendered + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tracer", choices=("auto", "strace", "dtruss"), default="auto")
    parser.add_argument("--parse-only", type=Path, default=None)
    parser.add_argument("--assert-clean", action="store_true")
    parser.add_argument("--json-out", type=Path, default=None)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    tracer_name = select_tracer(
        tracer_name=str(args.tracer),
        platform_name=sys.platform,
        which=shutil.which,
    )

    child_returncode = 0
    if args.parse_only is not None:
        trace_path = Path(args.parse_only)
    else:
        command = list(args.command)
        if command and command[0] == "--":
            command = command[1:]
        if not command:
            raise SystemExit("Pass --parse-only TRACE or provide a command after --.")
        with tempfile.NamedTemporaryFile(prefix="trace-boundary-", suffix=".log", delete=False) as handle:
            trace_path = Path(handle.name)
        trace_command = build_trace_command(
            tracer_name=tracer_name,
            trace_path=trace_path,
            target_command=command,
        )
        child = subprocess.run(trace_command, check=False)
        child_returncode = int(child.returncode)

    payload = parse_trace_file(trace_path=trace_path, tracer_name=tracer_name)
    _write_payload(payload=payload, json_out=args.json_out)

    if args.assert_clean and bool(payload["high_risk_boundary_crossed"]):
        return 2
    return child_returncode


if __name__ == "__main__":
    raise SystemExit(main())
