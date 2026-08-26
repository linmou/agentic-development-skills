#!/usr/bin/env python3
# Create a temporary Markdown handoff template for transferring task context to another agent.

import argparse
import datetime as dt
import os
import re
import tempfile
from pathlib import Path


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug[:64] or "handoff"


def build_document(task: str, workdir: str, session_link: str) -> str:
    now = dt.datetime.now(dt.timezone.utc).astimezone()
    return f"""# Handoff: {task}

Created: {now.isoformat(timespec="seconds")}
Working directory: `{workdir}`
Local session link or locator: {session_link}

## User Request

TODO: State the user request and success criteria in one short paragraph.

## Persistent Pointers

TODO: List working-directory files, diffs, logs, screenshots, commits, or docs that already contain durable context.

## Non-Persistent Context

TODO: Add only decisions, constraints, assumptions, and current conversation context that are not saved elsewhere.

## Work Completed

TODO: Summarize completed edits, generated artifacts, and important command outcomes.

## Validation Evidence

TODO: List tests, reviews, command results, subagent checks, or manual verification that prove the current state.

## Current State

TODO: Say exactly what is done, what remains, and whether anything is blocked.

## Next Actions

1. TODO
2. TODO
3. TODO

## Handoff Validation

Gap-finding subagent: TODO
Continuation subagent: TODO
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a temporary agent handoff Markdown template.")
    parser.add_argument("--task", required=True, help="Short task name for the handoff title and filename.")
    parser.add_argument("--workdir", default=os.getcwd(), help="Working directory relevant to the task.")
    parser.add_argument("--session-link", default="Unavailable in this environment", help="Local session link or locator.")
    parser.add_argument("--output-dir", default=str(Path(tempfile.gettempdir()) / "codex-handoffs"), help="Directory for handoff documents.")
    parser.add_argument("--slug", help="Optional filename slug. Defaults to a slug derived from --task.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"{timestamp}-{slugify(args.slug or args.task)}.md"
    output_path = output_dir / filename
    output_path.write_text(build_document(args.task, str(Path(args.workdir).expanduser().resolve()), args.session_link), encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()
