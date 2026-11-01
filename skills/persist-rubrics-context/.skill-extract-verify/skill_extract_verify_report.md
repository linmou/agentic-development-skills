# Skill Extract Verify Report

- **Host**: `/Users/admin/.codex/skills/co-improvement-adapt`
- **Extracted**: `/Users/admin/.codex/skills/persist-rubrics-context`
- **Capability**: Persist reusable human feedback as project context/rubric memory (write engine)
- **Overall**: **fail**
- **Blocking fails**: **C4b** (call-contract field API design)

## Criteria

### C1 — Capability, not lifecycle (blocking)
- Scores (identity / orchestration / residue): **5 / 5 / 5**
- Hard gates: all **pass**
- Verdict: **pass**
- Evidence:
  - Extract purpose: write engine for `contexts/` + `rubrics/` (`persist-rubrics-context/SKILL.md`).
  - Host owns State 0–4, `REVIEW_OK` / `PERSIST_OK` / `REFLECT_OK` (`co-improvement-adapt/SKILL.md`).
  - Host learn path is subagent only; State 3 is audit gate, not write engine.
- Fix: none.

### C2 — One-way dependency (blocking)
- Scores (host→extract / no reverse / no host tokens on callee): **5 / 5 / 5**
- Hard gates: all **pass**
- Verdict: **pass**
- Evidence:
  - Host: `subagent($persist-rubrics-context)` on learn interrupt + State 3; adapter `persist-learnings-skill.md`; progressive disclosure to callee contract.
  - Grep extract tree: **no** `co-improvement-adapt` / `$co-improvement-adapt` in skill body/contract/memory (tests assert this).
  - Extract: “do not issue host tokens (`PERSIST_OK`, `REVIEW_OK`)” — prohibition only, does not collect them. Description mentions `REVIEW_OK` as a *non-wait* trigger cue (standalone-usable).
- Fix: none required. Optional: soften description “REVIEW_OK” mention to “section-end gate” if grepping host tokens is noisy.

### C3 — Single writer, thin client (blocking)
- Scores (side effects / thin client / audit / no second engine): **5 / 5 / 5 / 5**
- Hard gates: all **pass**
- Verdict: **pass**
- Evidence:
  - Write assets only under extract: `memory-protocol.md`, `validate_rubric_memory.py`, bootstrap script.
  - Host tests (`test_memory_boundary.py`) assert host has **no** local `memory-protocol.md` / `validate_rubric_memory.py`.
  - Host adapter: Request → subagent → merge `learning_log_row` → resume; State 3 re-invokes for pending flush / missed scan, then host issues `PERSIST_OK`.
  - Host **reads** learnt memory at start (allowed); writes only via extract.
- Fix: none.

### C4a — Contract exists + opaque labels (blocking if imported)
- Scores (existence / schema ownership / opaque labels / third-party): **5 / 5 / 5 / 5**
- Hard gates: all **pass**
- Verdict: **pass**
- Evidence:
  - Callee SoT: `references/call-contract.md` **version 2**; defaults documented; host points to it and says it does not redefine Response schemas.
  - Host maps `caller_tag` / `correlation_id` as opaque; adapter text: “write skill does not interpret these strings.”
  - Callee coupling rules: tags not control enums; minimal third-party Request is only `project_root` + `human_feedback`.
  - Host *examples* use `learn-interrupt` / `state3-*` as **caller-owned** tags only (not callee required enums).
- Fix: none for C4a.

### C4b — Field API design (blocking hard gates if imported)
- Contract path: `persist-rubrics-context/references/call-contract.md` (v2)

#### Field inventory

| Field | Class | Needed? | Overlaps? | Precedence | Keep/merge/drop |
|-------|-------|---------|-----------|------------|-----------------|
| `project_root` | content | y | — | — | keep |
| `human_feedback` | content | y | can carry goals/situation | primary content | keep |
| `intents` | seed | optional y | vs feedback goals; vs durable intent_refs | policy + infer | keep (seed only) |
| `context_hints` | seed | weak | vs feedback + disk contexts | **weak** for context_refs | **merge/drop** (prefer disk+feedback) |
| `domain_hint` | seed | weak | vs infer-from-content | unspecified if conflict | **drop** or infer-only |
| `intent_seed_policy` | control | weak | restates default rule in 3 modes | n/a | **drop** (one default rule) |
| `correlation_id` | opaque | y | dual with section_id | correlation wins | keep |
| `section_id` | opaque | legacy | = correlation_id | alias | keep alias one version, retire |
| `caller_tag` | opaque | y | — | — | keep |
| `decision_mode` | control | y | — | — | keep |
| `pre_decision` | control | y w/ predecided | — | — | keep |
| `output_profile` | output | y | vs include | profile then include | keep |
| `include` | output | y | vs profile | — | keep |
| `learning_log_path` | output | optional | — | — | keep |
| Response `intent_resolution` (standard) | output | audit | vs candidate keywords + field_build | — | demote to full |
| Response `field_build` (full) | output | debug | audit echo | — | keep full only |
| Response `learning_log_row.section_id` | opaque | legacy | = correlation_id | duplicate | retire path |

#### Scores D1–D7
- **D1 Necessity: 3** — Core write fields solid; `intent_seed_policy` is a 3-mode enum for one default rule; `domain_hint` and `context_hints` optional bloat; `intent_resolution` in **standard** profile is audit weight.
- **D2 Sufficiency: 4** — Minimal `project_root` + `human_feedback` works; default `provided_then_infer` fills intent fields; Response has status/writes/validation/log row.
- **D3 Non-overlap: 3** — Situation channel triple: feedback + `context_hints` + disk; goal channel dual: `intents` + feedback; id dual: `section_id`/`correlation_id` (winner documented); standard Response can echo intent story via resolution + candidate keywords.
- **D4 Clarity: 4** — Roles mostly clear; good minimal + seeded examples; inference rule for goals is clear. Residual: session “active goals” vs durable `intent_refs` naming.
- **D5 Consistency: 3** — `context_hints` “not auto-persisted” but can land in durable `context_refs`; session `intents` seed durable keywords/refs with only a soft “purpose not rule text” rule (no hard “generalize local run goals”); `infer_only` accepts then ignores `intents` (dead input); `provided_only` + empty intents fights “minimal call always valid” narrative for that mode.
- **D6 Layering: 5** — Request is call I/O not full file schema; host tokens not required; callee owns schema; host adapter packs/merges.
- **D7 Evolvability: 3** — Version 2 + changelog present; `section_id` alias has winner but **no retirement timeline**; dual id on every `learning_log_row` forever.

#### Hard gates
| # | Gate | Result |
|---|------|--------|
| 1 | Minimal call works | **pass** |
| 2 | No host control enums | **pass** |
| 3 | No silent dual meaning (ids) | **pass** (winner documented) |
| 4 | Write fill path for mandatory attrs | **pass** (infer intents; disk/feedback for situation) |
| 5 | Precedence if ≥2 inputs | **fail / weak** — intent policy stated; **context_hints vs disk vs feedback** for merge/`context_refs` not ordered |
| 6 | D1 ≥ 3 | **pass** (3) |
| 7 | D2 ≥ 4 | **pass** |
| 8 | D5 ≥ 3 | **pass** (3); not D5=1 |

- Verdict: **fail** (hard gate 5 weak/fail; D1/D3/D5 = 3 so not “all D1–D6 ≥ 4”; multi-dimension smell not smell-only exception)
- Smells: policy enum inflation; seed surface fat; standard `intent_resolution`; alias soup; session→durable intent stamp risk
- Fix:
  1. Drop or non-normative-ize `intent_seed_policy` → single rule: use `intents` if non-empty else infer.
  2. Drop `domain_hint`; infer domain from content.
  3. Drop `context_hints` **or** state precedence: `human_feedback` claim > disk contexts for merge match > hints only as non-durable steering, never copied into `context_refs` unless also decided as a context write.
  4. Add durable-intent rule: generalize session goals before writing `intent_refs`/`intent_keywords`.
  5. Move `intent_resolution` to `full` profile; keep one correlation id long-term (`section_id` alias retirement note).

### C5 — Standalone trigger (blocking)
- Scores (description / runnable alone): **5 / 5**
- Hard gates: all **pass**
- Verdict: **pass**
- Evidence:
  - Description: mid co-review, writing conventions, save/remember, parent subagent — works without naming host skill.
  - Full procedure + contract + memory protocol runnable standalone / free-form chat mapped to `human_feedback`.
- Fix: none.

### C6 — Completeness (non-blocking)
- Checklist / scores: **5** (assets on callee; host adapter; no host write engine; reverse-dep clean; contract on callee)
- Verdict: **pass**
- Evidence: extract owns scripts/references for write; host `persist-learnings-skill.md` thin client; boundary tests on host.
- Fix: none. Optional: ecological cases still describe older host co-review text — not a dual writer.

## Call map

| From | To | Mechanism | Notes |
|------|-----|-----------|-------|
| co-improvement-adapt | persist-rubrics-context | subagent(`$persist-rubrics-context`) | learn-interrupt, state3-pending-flush, state3-missed-scan |
| co-improvement-adapt | persist-rubrics-context | path refs | SKILL progressive disclosure + adapter SoT |
| any third party | persist-rubrics-context | direct / subagent | minimal Request supported |

## Dual-path risks

- **None observed for writes.** Host reads learnt JSON; only extract writes.
- Residual: generated *local skills* from adapt may bootstrap helper copies of memory docs (`bootstrap_memory_artifacts.sh`) — helpers, not a second write engine, if generated skill still routes writes through `$persist-rubrics-context` (`local-skill-output.md`).

## Top fixes

1. **Slim call-contract v2.1 / v3 field surface** — remove `intent_seed_policy`, `domain_hint`; decide keep/drop `context_hints` with hard precedence (C4b D1/D3/gate 5).
2. **Durable vs session intent rule** — when seeding `intent_refs`/`intent_keywords`, require generalized goals (C4b D5).
3. **Demote audit fields** — `intent_resolution` (and dual `section_id` on every log row) out of standard path; document alias retirement (C4b D3/D7).

---

## Summary scores

| Criterion | Verdict | Blocking? |
|-----------|---------|-----------|
| C1 Capability vs lifecycle | pass | yes |
| C2 One-way dependency | pass | yes |
| C3 Single writer / thin client | pass | yes |
| C4a Contract + opaque labels | pass | yes |
| C4b Field API (D1–D7) | **fail** | yes |
| C5 Standalone trigger | pass | yes |
| C6 Completeness | pass | no |

**Overall: fail** — extraction topology is sound; **call-contract field API (C4b)** is the blocking gap.
