#!/usr/bin/env python3
# Responsible file: scripts/trace_boundary_check.py
# Purpose: verify trace-based boundary checks stay lightweight while still summarizing high-risk runtime effects.

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "trace_boundary_check.py"


def load_module():
    spec = importlib.util.spec_from_file_location("trace_boundary_check", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module from {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def test_select_tracer_prefers_strace_when_available() -> None:
    module = load_module()

    tracer = module.select_tracer(
        tracer_name="auto",
        platform_name="linux",
        which=lambda name: f"/usr/bin/{name}" if name == "strace" else None,
    )

    assert tracer == "strace"


def test_build_trace_command_for_strace_includes_expected_flags() -> None:
    module = load_module()

    command = module.build_trace_command(
        tracer_name="strace",
        trace_path=Path("/tmp/trace.log"),
        target_command=["python", "-m", "pytest", "-q"],
    )

    assert command[:5] == ["strace", "-f", "-o", "/tmp/trace.log", "-e"]
    assert "trace=execve,connect,open,openat,clone,fork,vfork" in command
    assert command[-4:] == ["python", "-m", "pytest", "-q"]


def test_parse_strace_counts_exec_network_process_and_writes() -> None:
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp_dir:
        trace_path = Path(tmp_dir) / "trace.log"
        trace_path.write_text(
            "\n".join(
                [
                    'execve("/usr/bin/python", ["python"], 0x0) = 0',
                    'connect(3, {sa_family=AF_INET, sin_port=htons(443)}, 16) = 0',
                    'openat(AT_FDCWD, "/tmp/out.txt", O_WRONLY|O_CREAT|O_TRUNC, 0666) = 3',
                    'clone(child_stack=0x0, flags=CLONE_VM, child_tidptr=0x0) = 1234',
                    'openat(AT_FDCWD, "/tmp/in.txt", O_RDONLY) = 3',
                ]
            ),
            encoding="utf-8",
        )

        summary = module.parse_trace_file(trace_path=trace_path, tracer_name="strace")

    assert summary["event_counts"]["process_exec"] == 1
    assert summary["event_counts"]["network_connect"] == 1
    assert summary["event_counts"]["process_spawn"] == 1
    assert summary["event_counts"]["filesystem_write"] == 1
    assert summary["high_risk_boundary_crossed"] is True


def test_parse_dtruss_counts_exec_and_write_signals() -> None:
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp_dir:
        trace_path = Path(tmp_dir) / "trace.log"
        trace_path.write_text(
            "\n".join(
                [
                    'execve("/usr/bin/python\\0", 0x7FF7BFEFF5E8, 0x7FF7BFEFF5F8) = 0 0',
                    'open_nocancel("/tmp/out.txt\\0", 0x601, 0x1B6) = 3 0',
                    'connect(0x3, 0x16B5FEE10, 0x10) = 0 0',
                ]
            ),
            encoding="utf-8",
        )

        summary = module.parse_trace_file(trace_path=trace_path, tracer_name="dtruss")

    assert summary["event_counts"]["process_exec"] == 1
    assert summary["event_counts"]["filesystem_write"] == 1
    assert summary["event_counts"]["network_connect"] == 1
    assert summary["high_risk_boundary_crossed"] is True


def test_parse_only_cli_can_assert_clean_trace() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        trace_path = Path(tmp_dir) / "trace.log"
        trace_path.write_text(
            'openat(AT_FDCWD, "/tmp/in.txt", O_RDONLY) = 3\n',
            encoding="utf-8",
        )

        result = run_script(
            "--parse-only",
            str(trace_path),
            "--tracer",
            "strace",
            "--assert-clean",
        )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["high_risk_boundary_crossed"] is False


def test_parse_only_cli_fails_assert_clean_when_risky_boundary_found() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        trace_path = Path(tmp_dir) / "trace.log"
        trace_path.write_text(
            'execve("/usr/bin/python", ["python"], 0x0) = 0\n',
            encoding="utf-8",
        )

        result = run_script(
            "--parse-only",
            str(trace_path),
            "--tracer",
            "strace",
            "--assert-clean",
        )

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["high_risk_boundary_crossed"] is True
