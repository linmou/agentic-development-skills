# Memory Protocol (JSON-First: Context + Rubric)

Purpose: define where project memory lives, how it is written, how memory is retrieved, and how human feedback updates both context and rubric memory.

## Scope
- Context root: `./.co-improvement/learnt/contexts/`
- Context entries: `./.co-improvement/learnt/contexts/<domain>/<context-id>.json`
- Rubric root: `./.co-improvement/learnt/rubrics/`
- Rubric index: `./.co-improvement/learnt/rubrics/index.json`
- Rubric entries: `./.co-improvement/learnt/rubrics/<domain>/<rubric-id>.json`
- Rubric quality evaluation (proposal only): `references/rubric-persistence-rubric.md`
- Context quality evaluation (proposal only): `references/context-persistence-rubric.md`
- Human decision authority for `append | merge | skip`: `persist-rubrics-context` procedure (not these rubrics)
- Consistency checker: `scripts/validate_rubric_memory.py`

## 1) Context Memory Branch (No Index)
### Storage
1. Store context as JSON files under `./.co-improvement/learnt/contexts/`.
2. Do not create `contexts/index.json`.
3. Keep one context entry per file.
4. Context memory is project-wide and should be considered as a whole.

### Write
Precondition: a Learning Log row with `status=decided` and human decision `append | merge | skip` already recorded by `persist-rubrics-context` (or an equivalent host gate). This section **executes** that decision; it does **not** choose for the human.

1. Build candidate JSON from the decided Learning Log candidate (wording concrete and reusable).
2. Evaluate shape with `references/context-persistence-rubric.md` only for validation quality; do not override the human decision.
3. Execute the human decision:
   - `append`: create one new context file.
   - `merge`: update an existing context file when it is the same core context.
   - `skip`: do not write.
4. Refuse to write if status is `pending` or decision is missing.

### Retrieve (Initial Version)
1. Read all JSON files under `./.co-improvement/learnt/contexts/` recursively.
2. Drop malformed files.
3. Return all valid contexts (no index and no keyword filtering in initial version).

## 2) Rubric Memory Branch (Indexed)
### Storage
1. Use `index.json` as router and rubric JSON files as source of truth.
2. Store full rubric content only in rubric entry files, not in `index.json`.
3. Keep one rubric entry per file.
4. `id` must be unique across active rows in `index.json`.
5. Keep `index.json` minimal fields only:
   - `id`
   - `path`
   - `status` (`active` or `deprecated`)
   - `intent_keywords`
   - `context_keywords`
   - `applicability_summary`
6. Do not use `priority`.
7. Do not use `version` in `index.json`; index routes to latest maintained active entry.
8. Do not use `supersedes` in `index.json`.

### Write
Precondition: Learning Log `status=decided` with human decision `append | merge | skip` from `persist-rubrics-context`. Decision authority is not here.

1. Take the rubric entry from the `rubric-construction` Response (schema owned there).
2. Judge persistence with `rubric-persistence-rubric.md`; do not override the human decision.
3. Execute the human decision in one change set:
   - `append`:
     - create one new rubric JSON file under `rubrics/<domain>/`
     - add one `active` object to `index.json`
   - `merge`:
     - update refined rubric JSON file as latest for existing rubric `id`
     - update matching `index.json` object fields (`path`, keywords, applicability summary) if needed
     - keep exactly one `active` object per `id`
   - `skip`:
     - do not write
4. Reject malformed candidates.
5. Refuse to write if status is `pending` or decision is missing.
6. Run consistency check after each write:
   - `python3 <persist_rubrics_context_skill_dir>/scripts/validate_rubric_memory.py --project-root <project_root>`

### Retrieve
Input:
- current intent list
- current context snapshot
- all project contexts from Context Memory Branch

Steps:
1. Load `index.json` first.
2. Keep objects where `status = active`.
3. Enforce latest-only invariant:
   - for each `id`, keep exactly one active object.
4. Apply coarse prefilter using `intent_keywords` and `context_keywords`.
5. Load only filtered rubric files by `path`.
6. Drop malformed entries or missing-file rows.
7. Apply semantic filters from rubric content:
   - `applicability.include` / `applicability.exclude`
   - `dependencies.context_refs` / `dependencies.intent_refs`
8. Return selected rubrics with one-line selection reason each.

## 3) Call boundary + write execution
Write path authority: skill `persist-rubrics-context` only. Callers invoke via `references/call-contract.md` (Request / Response). Callers may re-spawn this skill and collect their own audit tokens; callers do not write learnt JSON themselves.

For each run:
1. Accept Request (defaults apply for omitted optional fields).
2. Propose candidates; apply `decision_mode` (interactive / predecided / propose_only).
3. Execute decided `append | merge` writes in this protocol; `skip` / pending write nothing.
4. Emit Response JSON per call-contract (project with `output_profile` / `include`).
5. `learning_log_row` in the Response is produced by this skill; durable multi-call session logs are the caller’s problem unless `learning_log_path` was set.

## Validation Checklist (Before Write)
- Context files are valid JSON and include required keys.
- `index.json` active `id` values are unique.
- `index.json` `path` values are valid and existing.
- `index.json` contains no `priority` key.
- `index.json` contains no `version` key.
- `index.json` contains no `supersedes` key.
- Rubric file passes `rubric-construction` gates G1–G4 (`validate_rubric_entry.py`, run by the validator) and its `id` matches the index row.

## Context Entry JSON Minimal Template
```json
{
    "id": "CTX-TEAM-FATIGUE-RISK",
    "statement": "Long multi-step tasks increase fatigue risk and reduce human review quality.",
    "intent_keywords": ["decomposition", "review quality"],
    "context_keywords": ["long task", "fatigue"],
    "scope": {
        "include": ["multi-step tasks"],
        "exclude": ["single-step quick edits"]
    },
    "lifecycle": {
        "sunset_condition": ""
    }
}
```

## `index.json` Minimal Template (Rubrics)
```json
[
    {
        "id": "RUB-TASK-DECOMPOSITION",
        "path": "./.co-improvement/learnt/rubrics/workflow/rub-task-decomposition.json",
        "status": "active",
        "intent_keywords": ["task split", "role mapping"],
        "context_keywords": ["long task", "fatigue risk"],
        "applicability_summary": "use for multi-step workflows; exclude one-shot tasks"
    }
]
```

## Notes
- JSON is single source of truth; AI can render readable summaries for HITL review.
- Context branch is intentionally index-free in initial version; retrieval reads all contexts.
- Human decision authority for `append | merge | skip` lives in `persist-rubrics-context` SKILL procedure, not in this Write section.
- Use `context-persistence-rubric.md` / `rubric-persistence-rubric.md` for candidate quality evaluation only.
- Rubric entry schema source: `rubric-construction/references/rubric-entry-template.md`.
- If index metadata conflicts with rubric file content, trust rubric file content and repair index.
