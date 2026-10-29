# Agentic Development Skills

Intent: store skills for agentic coding, research experiments, and skill development in one public repository, while exposing each skill as an independent directory.
Updated: 2026-10-29
Commit: 0df9e1a (base revision for the auto-exp and experiment-log-writer import)

## Layout

```text
agentic-development-skills/
  skills/<skill-name>/SKILL.md
  scripts/link_skills.sh
```

The repository has one Git history. Each skill remains self-contained under `skills/<name>/`, including optional resources.

Included skills:

- `fast-multi-agent-tdd`
- `code-smell-monitor`
- `diagnose-agentic-coding`
- `diagnose-agentic-behavior`
- `review-with-multi-debate`
- `auto-skill-test-improve-loop`
- `formalize-workflow-state-machine`
- `parallelize-workflow`
- `skill-contract` (formerly `skill-extract-verify`)
- `writing-great-skills`
- `handoff-context`
- `speckit-orchestrate`
- `auto-exp`
- `experiment-log-writer`

`auto-exp` requires `experiment-log-writer`; install both directories together. The dependency is declared in `auto-exp`'s `metadata.requires` and checked against `experiment-log-writer/contract.json`. The writer includes its versioned call contract and experiment log template. Both skills were imported from the local Codex skill collection with their workflow and UI metadata preserved. The `~/.codex/prompts/auto_exp.md` mention in `auto-exp` identifies a legacy invocation trigger; that prompt file is not a runtime dependency.

## Skill contracts

A skill that other skills call can publish `contract.json` (format `skill-contract/1`); callers declare `metadata.requires: <skill>@<range>` and ship call examples under `references/calls/<callee>/`. Check every contract and caller in a skill root with:

```bash
python3 skills/skill-contract/scripts/check_contracts.py skills
python3 skills/skill-contract/scripts/check_contracts.py ~/.codex/skills ~/.claude/skills
```

See `skills/skill-contract/references/contract-format.md`.

## Runtime links

Codex loads skills from `~/.codex/skills`. Build or refresh links with:

```bash
scripts/link_skills.sh ~/.codex/skills
```

The destination is configurable; an optional second argument selects another source checkout:

```bash
scripts/link_skills.sh /path/to/runtime/skills /path/to/agentic-development-skills
```

The linker scans only direct children of `skills/` that contain `SKILL.md`. It is idempotent, never overwrites a real path or conflicting symlink, and rejects destinations inside the source tree.

## GitHub migration

The former `robust-tdd-skills` submodule umbrella has been converted to this flat monorepo. Standalone source repositories are documented in [MIGRATION.md](MIGRATION.md); they are not deleted by this local conversion.

Clone normally:

```bash
git clone https://github.com/linmou/agentic-development-skills.git
```

Then create runtime links from the clone as shown above.
