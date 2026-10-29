---
name: auto-exp
description: Run automatic research experiment loops from a user prompt. Use when the user asks for automatic experiments, autonomous experiment iteration, hypothesis testing, or work based on ~/.codex/prompts/auto_exp.md; enforce a dedicated auto_experiments folder, experiment log, branch isolation, per-iteration commits, and reproducible commands.
metadata:
  requires: experiment-log-writer@^1.0.0
---

# Auto Experiment

## Core Intent

Run experiments as traceable scientific work, not as one-off scripts. Keep every iteration reproducible: what question was asked, what hypothesis was tested, what changed, what command ran, what result appeared, and what commit records it.

## Start Gate

Before changing files or running the experiment, ask only for missing information needed to proceed:

- Research question or target phenomenon, unless the user already specified it.
- Success metric or evaluation signal.
- Allowed runtime, model/API/GPU constraints, and whether GPU-consuming work is permitted.

If these details are already supplied, proceed to workspace setup without another general question.

## Workspace Setup

1. Inspect the repository guidance closest to the target code or experiment area.
2. Check the current branch, worktrees, and working-tree status. Tell the user if the current worktree is dirty and summarize the existing changes; a new worktree will not automatically contain uncommitted changes.
3. For every new experiment, ask whether to create a new worktree on `auto-experiment/<short-topic>` or continue on an existing `auto-experiment/` branch in its worktree. Name the available branch when one exists. Wait for the choice before changing files or running the experiment.
4. Use the chosen worktree. Do not commit pre-existing changes unless the user identifies them as part of the experiment.
5. Create a new experiment folder under `auto_experiments/`. Use a date plus short topic, for example `auto_experiments/2026-05-22-emotion-defection/`.
6. Put all experiment-specific scripts, configs, raw outputs, summaries, and logs in that folder unless existing project conventions require a closer location.

Filesystem placement does not imply Git tracking. Apply the policy below before generating large artifacts.

Do not silently change experiment config values to make a run succeed. Fail loudly and record the failure.

## Git Artifact Policy

Keep Git focused on the compact instructions, provenance, and conclusions of the experiment. Track:

- Experiment code, scripts, configs, and prompts that define the run.
- The experiment log with exact commands, changed factors, metrics, and interpretation.
- Compact summaries, histories, selected or candidate skills, and model metadata.
- Source-data identifiers, selection rules, hashes, and manifests for externally stored artifacts.

Exclude reproducible or operational bulk from Git while retaining it locally or in artifact storage:

- Materialized datasets and splits that can be deterministically rebuilt from an identified source.
- Raw predictions, conversations, per-item prompts, result payloads, rollouts, and intermediate optimization directories.
- Trainer/model/console logs, GPU or metrics traces, caches, preflight responses, and resumable runtime state.
- Credentials, private endpoints, user data, and other sensitive material; never commit these.

Remember to use `.gitignore` for repository-wide generated artifacts like large scale exp output folders. Use `.git/info/exclude` only for intentionally local, machine-specific noise such as ad hoc GPU traces. Add rules before running the experiment. If an artifact is already tracked, remove it from the index without deleting the local file; do not rewrite history merely to reduce a pending merge.

Do not discard unique scientific evidence. When raw artifacts are required but unsuitable for Git, store them durably and record their location, content hash, generation command, run/config identifier, file count, and size in the experiment log. Ask the user before omitting evidence that is neither reproducible nor stored elsewhere.

## Experiment Log

Use `$experiment-log-writer` to create and update `auto_experiments/<date-topic>/experiment_log.md`. Read its `references/call-contract.md` before the first call. The writer owns the log template, field meanings, and all log edits; this skill owns experiment execution and the decision to call the writer.

Call the writer with a `plan` entry before the first run and an `iteration` entry after each run, including failed or partial runs. Supply observed facts: changed factors, exact planned and executed commands, working directory, environment reference, exit status, input/config identifiers, metrics, decision reasoning, interpretation, and artifact locations. For externally stored raw evidence, supply a stable results address or manifest with generation command, run identifier, location, content hash, file count, and size. Pass representative input-output pairs when outputs are qualitative. Use a `correction` entry for later corrections; do not edit the log directly.

Inspect the writer's response. If it reports missing information needed for a faithful record, gather it and call the writer again before committing. Never invent a command, result, timestamp, or artifact address to fill a gap.

## Iteration Loop

For each iteration:

1. Propose the specific hypothesis.
2. Implement the minimum experiment code/config needed.
3. Run the command needed to produce evidence.
4. Check whether the result supports the hypothesis.
5. Revise the hypothesis or plan if results do not match.
6. Invoke `$experiment-log-writer` with the iteration facts and inspect its response.
7. Run relevant tests or validation commands.
8. Commit the iteration.

Use simple scripts and simple shell commands. Avoid complex shell logic; put real logic in Python or the project language with tests when needed.

## Commit Discipline

Commit each completed iteration separately. Before committing:

1. Review nearby Markdown docs or `claude_doc` folders to decide whether documentation needs updates.
2. Include doc updates when the experiment creates or changes reusable behavior.
3. Review `git status`, the staged diff summary, and tracked files matching ignore rules. Stop if generated bulk dominates the commit.
4. Stage only relevant files.
5. Use a commit message that names the iteration and hypothesis, for example `auto-exp: test emotion prompt defection hypothesis`.

The commit containing an iteration log cannot contain its own hash. Record each completed iteration commit hash in the final report. If a later log update needs to cite that commit, pass it to `$experiment-log-writer` as `iteration_commit` in a correction or subsequent analysis entry; do not edit the log directly.

Do not delete files except temporary test scripts created during the current work, unless the user explicitly permits deletion.

## Final Report

End with:

- Experiment folder path
- Branch name
- Iteration commits
- Key evidence that the request was met, including commands run and important output/log paths
- Current conclusion and any unresolved risks
