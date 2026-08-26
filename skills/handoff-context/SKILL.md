---
name: handoff-context
description: Create compact task handoff documents for another agent to continue from local artifacts rather than hidden chat context. Use at the end of a session, before context compaction, before transferring work to a new agent, or when asked to summarize current task state into a temporary handoff with links to the local session, working directory files, decisions, commands, validation evidence, blockers, and next actions. Includes a validation loop where fresh subagents read only the handoff document and report missing context before finalizing it.
---

# Handoff Context

## Overview

Create a handoff document in a temporary directory that lets a fresh agent continue the task from persistent evidence. Keep it short: write only the context that is not already persisted in working-directory files, and point to files, diffs, logs, or session links whenever those are enough.

## Workflow

### 1. Create the Draft

Use the helper script to create a dated Markdown template:

```bash
python3 /Users/admin/.codex/skills/handoff-context/scripts/create_handoff.py \
  --task "short task name" \
  --workdir "$PWD" \
  --session-link "local session link or locator"
```

If no session link is available, write `Unavailable in this environment` and add the best locator you do have, such as current working directory, branch, commit, terminal transcript path, or Codex session file path. Do not invent a URL.

### 2. Fill Only Non-Persistent Context

Write enough for continuation, not a transcript. Prefer pointers over copied content.

Include:

- User request and success criteria.
- Local session link or locator.
- Working directory, relevant repositories, branches, and commit ids if available.
- Files changed or created, with absolute paths when useful.
- Key decisions and why they were made.
- Commands run and the result that matters.
- Tests, validation, screenshots, logs, or review evidence.
- Current state: what is done, what is pending, what is blocked.
- Next actions in execution order.

Exclude:

- Full chat history.
- Large file contents already saved in the working directory.
- Repeated command output unless the exact output is the evidence.
- Speculation that a new agent cannot verify.
- Background facts that are obvious from linked files.

### 3. Validate With a Gap-Finding Subagent

Start a fresh subagent with only the handoff document path and this request:

```text
Read this handoff document and the local files it points to. Without using any other conversation context, report the minimum missing information that prevents you from continuing the task. If you can continue, say so and list the next three actions.
```

If the subagent finds gaps, update the handoff document with only the missing non-persistent context or better pointers to persistent files. Repeat once if the first update materially changes the handoff. Stop when remaining gaps are normal execution uncertainty, not missing context.

### 4. Validate With a Continuation Subagent

Start a second fresh subagent with only the revised handoff document path and this request:

```text
Read this handoff document and the local files it points to. Without using any other conversation context, explain the current task state, identify the next concrete action, and name the evidence you would inspect before editing.
```

Accept the handoff only if the second subagent can state the task, current state, relevant files, validation evidence, and next action without asking for hidden chat context.

### 5. Close Out

Report the handoff document path and the two validation outcomes. If the user needs another agent to continue immediately, provide the handoff path as the first thing that agent should read.

## Quality Bar

- A fresh agent can continue from the handoff plus referenced files.
- The document is shorter than the hidden conversation it replaces.
- Every important claim is either linked to a persistent file, backed by a validation result, or explicitly marked as an unresolved assumption.
- The document does not copy large artifacts that already exist on disk.
- The document distinguishes completed work from planned work.
