---
name: skill-contract
description: >
  Build a versioned call contract for a callee skill and verify every local
  caller against it: declared version ranges, request fit, field provenance,
  status handling, single-writer ownership, and the impact of a contract
  change. Use when one skill calls another, after extracting a skill, before
  changing a callee's Request/Response, or when asked whether skills are safely
  coupled.
---

# Skill Contract

Make a callee's interface a checked artifact instead of prose, then prove the local callers fit it.
Write only contract artifacts (`contract.json`, call examples, and a prose contract when the callee has none and the user agrees). Do not rewrite caller or callee procedures unless the user asks after the report.

## Modes

| Mode | Use when | Inputs |
|------|----------|--------|
| `build` | A callee has no `contract.json`, or its prose contract changed | `callee` folder |
| `verify` (default) | Checking one callee's callers, or every contract in local storage | skill roots; optional `callee` |
| `impact` | Before changing a callee's contract | skill roots; `callee`; proposed `contract.json` |
| `extract` | A capability was just split out of a host skill | `host_skill`, `extracted_skill` |

Skill roots are folders whose direct children are skills, for example `~/.codex/skills` and `~/.claude/skills`. Ask once for anything missing. `out_dir` defaults to `./.skill-contract/`; never commit it.

## Steps

1. **Load the format** — Read `references/contract-format.md`.
   *Done when:* contract, `metadata.requires`, call examples and the schema subset are known.

2. **Extract** (`extract` only) — Read `references/criteria.md` and `references/extraction-split-rubric.md`, score C1–C3, C4a, C5–C6 on the host/extract pair and record them with `references/extraction-report-template.md`. If C2 or C3 fail, report and stop: a contract does not fix a reversed or dual-writer split.
   *Done when:* the extraction report exists; continue to step 3 with the extracted skill as callee and the host as its first caller.

3. **Build** (`build` and `extract`) — Write `<callee>/contract.json` as the checkable projection of the callee's prose contract. Every request field, status and owned store comes from callee text; never add a field because a caller happens to send it. Add a prose contract first if none exists, and mark `high_stakes` using `references/trace-check.md`.
   Then audit the result as a separate pass: read `references/call-contract-field-rubric.md` and `references/single-agent-multi-pass-scoring.md` and run C4b Passes A–D on the contract you just wrote. Pass C is mandatory because you authored it.
   *Done when:* `contract.json` exists, agrees with the prose contract, and C4b is locked.

4. **Mechanical check** — Run
   `python3 scripts/check_contracts.py <root>... [--callee NAME] [--proposed FILE] --json`
   (`--proposed` in `impact` mode). It checks contracts, dual writers, version ranges, request examples against the schema, provenance coverage, unmentioned statuses and undeclared callers.
   *Done when:* the JSON output is saved to `out_dir`; every `error` and `insufficient` finding is listed for the report.

5. **Semantic pass per caller** — Read `references/caller-verify-rubric.md`. For each declared or suspected caller, score V1–V7 against the caller's SKILL.md and references. The script's warnings are leads, not verdicts.
   *Done when:* every caller has V1–V7 verdicts with evidence, including undeclared callers the script flagged.

6. **Impact** (`impact` only) — List each caller that breaks under the proposed contract, why, and the smallest fix: caller change, callee MAJOR bump, or keeping the old behaviour.
   *Done when:* every failing example and range mismatch maps to one caller and one fix.

7. **Optional trace check** — Only for `high_stakes` callees and only if the user wants it: follow `references/trace-check.md` on local agent sessions. Otherwise state in the report that it was suggested and not run.
   *Done when:* the trace section is filled or marked `not run`.

8. **Report** — Write `out_dir/skill_contract_report.md` from `references/report-template.md`. Chat summary: verdict, blocking findings, top 3 fixes.
   *Done when:* every template section is filled or `n/a`.

## Verdict

`fail` if the script reports any `error` or any blocking V criterion fails; else `insufficient_evidence` if the script reports `insufficient` or a blocking V criterion lacks evidence; else `pass`. Warnings and the trace suggestion never change the verdict on their own.

## Progressive disclosure

| File | Role |
|------|------|
| `references/contract-format.md` | `contract.json`, `metadata.requires`, call examples, schema subset, explicit Request block |
| `references/caller-verify-rubric.md` | V1–V7 per-caller semantic checks |
| `references/call-contract-field-rubric.md` | C4b D1–D7 field API rubric (build audit) |
| `references/single-agent-multi-pass-scoring.md` | How to score C4b without grading your own work |
| `references/trace-check.md` | Optional session-trace tier for high-stakes callees |
| `references/criteria.md`, `references/extraction-split-rubric.md` | Extract mode C1–C6 |
| `references/report-template.md`, `references/extraction-report-template.md` | Report formats |
| `scripts/check_contracts.py` | Mechanical checks; tests in `tests/` |
| `tests/fixtures/storage-regression/` | Known-answer pair for C4b gate 4; re-run after rubric edits |
