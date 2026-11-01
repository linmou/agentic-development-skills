# Skill Extract Verify Report

- **Host**: `~/.agents/skills/persist-rubrics-context`
- **Extracted**: `~/.agents/skills/rubric-construction`
- **Capability**: construct or audit one scoring rubric entry (grounding, scope, testable levels, examples, counter pairs) and return it with a quality check; no persistence
- **Import path**: yes (host SKILL step 6 + call-contract rubric branch invoke `rubric-construction` by skill name / subagent; host validator imports `validate_rubric_entry`)
- **Overall**: pass (rule: `criteria.md`) — after in-audit fixes listed under C2 and C4b Pass C
- **Blocking fails**: none
- Date: 2026-10-26 · auditor also authored the split (Pass C mandatory, done)

## Criteria

### C1 — Capability, not lifecycle (blocking)
- Scores (identity / orchestration / residue): 5 / 5 / 4
- Hard gates: 1 pass · 2 pass · 3 pass
- Verdict: pass
- Evidence: extract `SKILL.md` Purpose "Capability only: no persistence, no decisions about storage"; host keeps decision modes, append/merge/skip, index (`rubric-persistence-rubric.md`, `memory-protocol.md` §2 Write step 1 "Take the rubric entry from the `rubric-construction` Response").
- Fix: residue 4 — host contract **Intent rule** item 4 still defines `intent_refs` wording; extract P1 defines it too. Keep host rule as "goals to pass as `intents`" only.

### C2 — One-way dependency (blocking)
- Scores: 5 / 5 / 5
- Hard gates: 1 pass · 2 pass · 3 pass
- Verdict: pass
- Evidence: `grep -rn -e persist-rubrics-context -e "\.co-improvement" -e learnt rubric-construction` → clean. Host refs: `SKILL.md` step 6, `call-contract.md` rubric branch, `memory-protocol.md`, `validate_rubric_memory.py` import, `bootstrap_memory_artifacts.sh`.
- Fixed during audit: template storage path `./.co-improvement/learnt/...`, host-integration tests in extract (moved to host `tests/test_validator_delegation.py`), host name in extract changelog.
- Fix: none.

### C3 — Single writer, thin client (blocking)
- Scores (side effects / thin client / audit / no second engine): 5 / 4 / 5 / 4
- Hard gates: 1 pass · 2 pass · 3 pass · 4 pass
- Verdict: pass
- Evidence: extract writes nothing (SKILL Rule 3); host fill path "`rubric-construction` Response `entry`, written unchanged"; host validator no longer contains rubric-body checks — imports `validate_entry`.
- Fix: no-second-engine 4 — `bootstrap_memory_artifacts.sh` snapshots the extract template + validator into projects; intended (standalone copy), but snapshots go stale on extract edits.

### C4a — Contract exists + opaque labels (blocking if imported)
- Scores (existence / schema ownership / opaque labels / third-party): 5 / 5 / 5 / 5
- Hard gates: 1 pass · 2 pass · 3 pass · 4 pass
- Verdict: pass
- Evidence: `rubric-construction/references/call-contract.md` v1 with defaults; no opaque labels exist (none needed); minimal example `{"criteria": "..."}`; host maps fields, does not redefine them.
- Fix: none.

### C4b — Field API design (blocking if imported)
Contract path: `rubric-construction/references/call-contract.md`

**Pass A — Inventory**

Request inventory:

| Field | Class | Required/default | Overlaps? | Precedence | Keep/merge/drop |
|-------|-------|------------------|-----------|------------|-----------------|
| `criteria` | content | required | — | lowest (inference) | keep |
| `intents` | seed | `[]` | `entry.dependencies.intent_refs` | seed > entry > inference | keep |
| `context_refs` | seed | `[]` | `entry.dependencies.context_refs` | seed > entry > inference | keep |
| `entry` | content | `null` | seeds (above) | middle | keep |
| `mode` | control | `construct` | — | — | keep |

Standard Response keys: `skill`, `version`, `status`, `entry`, `check{verdict,gates,dimensions,issues}`, `missing`, `errors`

Output-construction crosswalk:

| Output artifact | Mandatory condition/profile | Inputs/capabilities | Resolver/path | Validation | Failure condition | Gap? |
|-----------------|-----------------------------|---------------------|---------------|------------|-------------------|------|
| `status` | always | Request validity, grounding | SKILL steps 1–2, 4 | status table | `audit` w/o `entry` → `error` | n |
| `entry` | `status=ok` | criteria, seeds, entry | fill-path table + P1–P7 | `validate_rubric_entry.py` G1–G4 | not constructible → `needs_input` | n |
| `check.gates` | `status=ok` | entry | script (G1–G4), reading (G5–G6; G1–G4 for rubric text) | `rubric-quality-rubric.md` | — | n |
| `check.dimensions` / `verdict` | `status=ok` | entry | quality rubric 3-level table | verdict rule | 2 repair rounds then return as is | n |
| `missing` | `needs_input` | grounding step | SKILL step 2 | non-empty when `needs_input` | — | n |
| `errors` | `error` | Request | SKILL step 1 | — | — | n |

Implementation crosswalk:

| Internal artifact | Producer | Dependencies/capabilities | Construction path | Validation | Failure behavior | Gap? |
|-------------------|----------|---------------------------|-------------------|------------|------------------|------|
| G1–G4 result | `validate_rubric_entry.validate_entry` | entry JSON | function / CLI | 13 unit tests | issue list, exit 1 | n |
| G5–G6 + dimensions | agent judgment | quality rubric | rubric ladder rows | none mechanical | `revise`/`fail` verdict | n (judgment by design) |

Conditional persistence crosswalk: n/a (extract never persists)

Failure-policy evidence: `error` trigger bounded (audit without entry) and reachable; `needs_input` trigger bounded (grounding not inferable) with `missing` list; normal path present for both; repair loop bounded at 2 rounds.

**Pass B — Strict scores**
- D1 5: each field has a class + job; counter: `mode` could be implied by `entry` presence → no, `construct` with `entry` = refine, distinct from `audit`.
- D2 4: all outputs constructible; counter: G5/G6 have no mechanical validator → judgment, held at 4.
- D3 4: precedence stated; counter: refine with seeds overwrites entry refs silently → documented order, held.
- D4 4: names match role, minimal + refine examples; counter: no `audit` example.
- D5 4: counter: "never emit partial entry as ok" vs `audit` returning invalid entry with `ok` → audit is check-only, `check.verdict` carries it; held.
- D6 4: callee owns schema, host stores unchanged; counter: host adds `intent_keywords` to stored file outside extract schema → validator ignores extra keys; held.
- D7 4: version 1 + changelog; counter: no alias plan needed yet.
- Hard gates 1–8: pass.

**Pass C — Attacks**
1. Refine with both `intents` and `entry` → which wins? → was undefined; fixed (precedence line), D3 held at 4.
2. Audit a markdown rubric (e.g. skill-extract-verify rubrics) → `entry` was JSON-only; fixed (rubric text allowed, G1–G4 by reading), D2 held at 4.
3. Repair loop termination → was unbounded; fixed (2 rounds), D5 held at 4.
4. Host passes `needs_input` through? → host contract maps to ask / `status=error`; held.

**Pass D — Lock**
- Scores: D1=5 D2=4 D3=4 D4=4 D5=4 D6=4 D7=4
- Hard gates 1–8: pass
- Verdict: pass
- Smells: none at D1/D3=3
- Fix: add an `audit` Request example.

### C5 — Standalone trigger (blocking)
- Scores: 5 / 5
- Hard gates: 1 pass · 2 pass
- Verdict: pass
- Evidence: description names rubric writing/auditing in any skill, review, or memory; no host mention; procedure needs only extract files.
- Fix: none.

### C6 — Completeness (non-blocking)
- Checklist / scores: assets moved 5 (template, entry validator, construction rubric) · host adapter 5 · copies removed 4 (bootstrap snapshot) · grep clean 5 · contract 5
- Verdict: pass
- Evidence: host `references/` no longer has `rubric-entry-template.md`; `co-improvement-adapt/tests/test_memory_boundary.py` updated to the new path.
- Resolved 2026-10-26: P5 now writes anchors 5/3/1 and implies 4/2 (human decision: less review effort); worked examples comply.

## Call map

| From | To | Mechanism | Notes |
|------|-----|-----------|-------|
| host SKILL step 6 | extracted | skill name / subagent | Request packed per host fill paths |
| host `validate_rubric_memory.py` | extracted `validate_rubric_entry.py` | Python import (sibling dir, or bootstrap copy beside it) | id-match stays in host |
| host `bootstrap_memory_artifacts.sh` | extracted template + validator | file copy | snapshot |

## Dual-path risks

- Bootstrap snapshots drift from the extract after edits.
- Host Intent rule vs extract P1 both describe `intent_refs` wording.

## Top fixes

1. Trim host Intent rule item 4 to "goals passed as `intents`"; let P1 own `intent_refs` wording.
2. Add an `audit` example to the extract contract.

## Evidence of tests

- `rubric-construction/tests`: 13 OK (G1–G4 edge cases, CLI exit codes, numeric level sort).
- `persist-rubrics-context/tests`: 16 OK (incl. delegation: valid passes, gate failure surfaces, id mismatch, bootstrapped copy runs isolated).
- `co-improvement-adapt/tests/test_memory_boundary.py`: OK.
- mypy: no issues (4 files).
