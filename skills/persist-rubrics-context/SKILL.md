---
name: persist-rubrics-context
description: >
  Persist reusable human feedback as project memory under .co-improvement/learnt
  (contexts and rubrics). Use immediately when feedback states durable constraints,
  project facts, writing/genre conventions, score meanings, examples, negative
  examples, or generalizable override reasons — including mid co-review or while
  another writing task is open. Also use when the human says save/remember/persist,
  or when a parent workflow spawns a subagent for a learn interrupt / memory write.
  Do not wait for section end, REVIEW_OK, or finishing the manuscript edit first.
  Multi-rule feedback that should apply to future runs is in scope even if the human
  also asks to revise the current draft.
---

# Persist Rubrics & Context

## Purpose
Turn human feedback into durable project memory:
- **contexts** → `./.co-improvement/learnt/contexts/`
- **rubrics** → `./.co-improvement/learnt/rubrics/` + `index.json`

Write engine with a stable call contract. No parent-skill dependency. Callers import one-way.

## Call interface

**SoT:** `references/call-contract.md` (version **4**).

1. Accept Request: required `project_root` + `human_feedback`; optional `intents`; opaque `correlation_id` / `caller_tag`; decision + output controls.
2. Run procedure; construct **all** storage-mandatory fields per contract **Write fill paths**.
3. Emit Response JSON (`version: 4`), projected by `output_profile` / `include`.
4. Do not advance caller lifecycle; do not issue host tokens (`PERSIST_OK`, `REVIEW_OK`, etc.).

Defaults if omitted: `intents=[]`, `caller_tag=standalone`, `decision_mode=interactive`, `output_profile=standard`, `include=null`.

## Non-Negotiable Rules
1. Require at least one candidate learning. If none: respond exactly "No reusable rubric or context detected. Provide a criterion, project fact, constraint, or say skip." and `status=no_candidate`.
2. **Never write memory without an explicit human decision** among `append | merge | skip` (unless `predecided` + valid `pre_decision`, or `propose_only` which never writes).
3. `decision_mode=predecided` with missing/invalid `pre_decision` → `status=error`, no write.
4. If human defers under `interactive`, `status=pending` and **do not write**.
5. Never ask the human to hand-edit JSON; AI writes after decision.
6. After rubric writes, run `scripts/validate_rubric_memory.py` → Response `validation` (fail-closed on invalid memory).
7. Always finish with a Response per call-contract.
8. **Invocation priority:** if chat mixes reusable constraints with draft edits, run this procedure for reusable parts first.

## Triggers
- New/revised **rubrics** (criteria, scores, thresholds, exclusions)
- New/revised **contexts** (facts, constraints, stakeholders, scope)
- Writing/genre conventions for this project or similar artifacts
- Generalizable score-override reasons; reusable examples / negative examples
- Explicit save/remember/persist
- Parent memory-write Request (any opaque `caller_tag`)

### Non-triggers
- One-off wording with no reusable rule
- Pure process chat / gate tokens alone
- Feedback only for the current sentence and not for later runs

When uncertain: propose candidate → `append | merge | skip | defer`.

## Procedure
1. Parse Request (free-form chat → `human_feedback` + defaults). Compat: lone legacy `section_id` → `correlation_id`. Ignore unknown/removed fields. Extract reusable candidates even if draft edit also requested.
2. Restate each candidate; classify `context` vs `rubric`.
3. **Intent rule** (contract): seed from `intents` if non-empty else infer from feedback; generalize to durable goals.
4. **Situation rule** (contract): feedback claim → disk contexts → infer domain/tags.
5. Map paths under `./.co-improvement/learnt/`.
6. **Build every storage-mandatory field** using contract **Write fill paths**. Context: statement/scope/keywords here. Rubric: entry body via skill **`rubric-construction`** (subagent or skill call; Request packed per fill paths), then keywords + index row here.
7. Evaluate with `references/context-persistence-rubric.md` or `references/rubric-persistence-rubric.md`.
8. Propose `append | merge | skip`.
9. Apply `decision_mode` with fail-closed rules.
10. On decided append/merge: bootstrap if needed; write via `references/memory-protocol.md`; validate; repair or error if invalid.
11. Project Response (`version: 4`); optional `learning_log_path` append.
12. Stop.

## Progressive Disclosure
- `references/call-contract.md` — Request/Response v4 + write fill paths
- `references/memory-protocol.md` — storage execution
- `references/context-persistence-rubric.md`
- `references/rubric-persistence-rubric.md`
- Rubric construction (entry schema, principles, quality check): skill `rubric-construction`
