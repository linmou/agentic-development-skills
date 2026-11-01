# Call Contract — `persist-rubrics-context`

Version: **4**

Stable interface between any **caller** and this **write engine**.  
Callers import one-way. This skill does not depend on any parent skill.

**Scope:** propose + (optionally) write **context** and **rubric** memory under `./.co-improvement/learnt/`.  
**Out of scope:** host lifecycle, host tokens, full retrieve orchestration (see `memory-protocol.md`).

## Roles

| Role | Owns | Does not own |
|------|------|--------------|
| **Callee** | Candidates, **entry field construction** (fill paths below), decisions, JSON writes, validation, Response schema | Host FSM, host tokens, multi-call session log lists |
| **Caller** | When to invoke, Request packing, which Response fields to keep | Memory layout, validators, inventing Response schema |

**Defaults:** omit optional fields → defaults below.  
**Opaque labels:** `caller_tag` and `correlation_id` are log-only; never control flow.

---

## Request

| Field | Required | Default | Class | Notes |
|-------|----------|---------|-------|-------|
| `project_root` | yes | — | content | Root containing `.co-improvement/learnt/` |
| `human_feedback` | yes* | — | content | Verbatim feedback; sole free-form content channel (claim + optional “about what”) |
| `intents` | no | `[]` | seed | Optional durable **goal** strings (not one-off task titles) |
| `correlation_id` | no | `null` | opaque | Caller log id only |
| `caller_tag` | no | `"standalone"` | opaque | Caller log label only |
| `decision_mode` | no | `"interactive"` | control | `interactive` \| `predecided` \| `propose_only` |
| `pre_decision` | no | `null` | control | Required when `decision_mode=predecided`: `append` \| `merge` \| `skip` |
| `output_profile` | no | `"standard"` | output | Named include preset (see projection) |
| `include` | no | `null` | output | If non-null, **replaces** profile defaults entirely (final field set) |
| `learning_log_path` | no | `null` | output | If set, append one JSONL line of `learning_log_row` after Response build |

\*Standalone free-form chat → map into `human_feedback`.

### Not in Request (do not send)

| Name | Status |
|------|--------|
| `context_hints`, `domain_hint`, `intent_seed_policy` | Removed (v3); ignored if sent |
| `section_id` | Removed (v4); if sent **without** `correlation_id`, copy once into `correlation_id` then discard (compat shim, not a second field) |

Unknown other fields: ignore.

### Decision modes (fail-closed)

| Mode | Decider | Writes | Fail-closed |
|------|---------|--------|-------------|
| `interactive` | Human in-run | on append/merge | Defer → `pending`, no write |
| `predecided` | `pre_decision` | on append/merge | If `pre_decision` missing/invalid → `status=error`, no write |
| `propose_only` | none | never | Candidates stay `pending` |

`pre_decision` applies to **all** candidates in the Request unless the value is an object `{ "candidate_id": "append|merge|skip", ... }` (optional map form). Scalar form applies the same decision to every candidate.

### Response projection

1. Start from `output_profile` defaults (table below).  
2. If `include` is a non-null list → **replace** that set with `include` (not merge).  
3. Always compute full internal result; only project listed keys into the Response.  
4. `learning_log_path` does not change Response shape; it side-writes the same `learning_log_row` object if that object was computed (even when not included in Response).

| Profile | Default `include` |
|---------|-------------------|
| `minimal` | `status`, `candidates`, `writes`, `errors` |
| `standard` | `status`, `candidates`, `writes`, `validation`, `learning_log_row`, `errors` |
| `full` | standard + `proposals`, `raw_validator_log`, `intent_resolution`, `field_build` |
| `custom` | exactly `include` (must be non-empty list or `status=error`) |

**Standard Response is not an audit echo stack:** `candidates` is the operational list; `learning_log_row` is the **session-log projection of the primary decided candidate** (first decided, else first pending) for thin hosts—not a second decision channel. `intent_resolution` / `field_build` appear only under `full`.

---

## Write fill paths (storage-mandatory fields)

Callee **must** populate every attribute required by storage templates / `validate_rubric_memory.py` before a successful write.  
Sources (only these): `required` Request · `seed` Request · `inference` from `human_feedback` (+ disk where noted) · `construct` (`rubric-construction` Response) · `ask` (interactive) · `fail` (error / no write).

This table is the hard-gate-4 inventory. It does **not** add Request fields (keeps layering: Request stays call I/O).

### All entries

| Stored attribute | Branch | Source | Rule |
|------------------|--------|--------|------|
| `id` | both | inference | Stable id from content slug (`CTX-…` / `RUB-…`); merge keeps existing id |
| `lifecycle` | both | inference | Object; `sunset_condition` string (may be `""`) |
| Domain folder path | both | inference | From content topic keywords (e.g. workflow, writing); not a Request field |

### Context branch (`contexts/**/*.json`)

| Stored attribute | Source | Rule |
|------------------|--------|------|
| `statement` | inference | One concrete reusable claim from `human_feedback` |
| `intent_keywords` | seed → inference | See **Intent rule** |
| `context_keywords` | inference | Short situation tags from the claim (what world/state the fact is about)—not goals |
| `scope.include` | inference | Where the fact applies (non-empty list) |
| `scope.exclude` | inference | Where it does not apply (non-empty list) |

### Rubric branch (`rubrics/**/*.json` + index row)

Entry body is built by skill **`rubric-construction`** (its `call-contract.md` v2; spawn a
subagent or invoke the skill). This skill packs its Request and stores its `entry`:
`criteria` ← reusable part of `human_feedback`; `intents` ← **Intent rule** goals;
`context_refs` ← **Situation rule** facts; `entry` ← existing file on merge;
`set` ← active rubrics in the same domain folder (minus the merge target);
`aggregation` ← `"reported separately"`.
`needs_input` → ask (interactive) or `status=error` (other modes); no write. A set-gate
`needs_input` whose fix is `merge` with a sibling → propose `merge` into that sibling.

| Stored attribute | Source | Rule |
|------------------|--------|------|
| `id`, `title`, `applicability.*`, `dependencies.*`, `decision_rule.*`, `lifecycle` | construct | `rubric-construction` Response `entry`, written unchanged |
| `intent_keywords` (file + index) | seed → inference | **Intent rule** |
| `context_keywords` (file not required; **index** yes) | inference | Situation tags for index routing |
| `applicability_summary` (index) | inference | One-line summary of `entry.applicability` |
| `path` / `status` (index) | inference | Path under domain; `status=active` on append |

### Intent rule (seed → inference)

1. If Request `intents` non-empty → primary seeds.  
2. Else → infer goals from `human_feedback` (purpose served, not criterion text).  
3. **Generalize** to durable goals (reusable across runs). Reject sole use of one-off titles (“Finish B1 today”).  
4. `intent_refs` = goal sentence(s); `intent_keywords` = short tokens from those goals + feedback.

### Situation rule (for `context_refs` / merge / non-overlap)

Precedence:

1. Claim in `human_feedback` (and derived `statement`)  
2. Existing disk contexts under `project_root`  
3. Infer remaining situation tags / domain from content  

Only decided `append`/`merge` persist. No parallel hint channel.

### Validation fail-closed

After any rubric write (and recommended after context write): run `scripts/validate_rubric_memory.py`.  
If validation fails → do not leave partial index/file inconsistent; report `validation.ok=false` and fix or `status=error`. Missing any table attribute above is a construction bug (infer again or fail)—never write partial invalid JSON knowingly.

---

## Examples

### Minimal

```json
{
  "project_root": "/path/to/project",
  "human_feedback": "Always prefer short commit messages under 50 chars."
}
```

### Seeded goals

```json
{
  "project_root": "/path/to/project",
  "human_feedback": "Always prefer short commit messages under 50 chars.",
  "intents": ["Keep git history easy to scan during review."],
  "correlation_id": "task-42",
  "caller_tag": "interactive-session"
}
```

### Predecided merge

```json
{
  "project_root": "/path/to/project",
  "human_feedback": "Merge into fatigue context: long multi-step tasks reduce review quality.",
  "intents": ["Protect human review quality on long tasks."],
  "decision_mode": "predecided",
  "pre_decision": "merge"
}
```

---

## Response

```json
{
  "skill": "persist-rubrics-context",
  "version": 4,
  "status": "decided",
  "candidates": [
    {
      "id": "c1",
      "branch": "context",
      "summary": "Prefer short commit messages under 50 chars.",
      "proposed": "append",
      "decision": "append",
      "status": "decided"
    }
  ],
  "writes": [
    {"action": "append", "path": "./.co-improvement/learnt/contexts/workflow/ctx-short-commits.json"}
  ],
  "validation": {"ran": false, "ok": true, "summary": "n/a (context only)"},
  "learning_log_row": {
    "timestamp": "2026-07-14T12:00:00Z",
    "correlation_id": "task-42",
    "caller_tag": "interactive-session",
    "candidate_summary": "Prefer short commit messages under 50 chars.",
    "branch": "context",
    "status": "decided",
    "decision": "append",
    "paths_touched": ["./.co-improvement/learnt/contexts/workflow/ctx-short-commits.json"]
  },
  "errors": []
}
```

### `status`

| Value | Meaning |
|-------|---------|
| `decided` | ≥1 candidate final; writes applied if append/merge |
| `pending` | Waiting on human, or `propose_only` |
| `no_candidate` | Not reusable |
| `error` | Fail-closed; see `errors` |

### `learning_log_row` fields

`timestamp`, `correlation_id`, `caller_tag`, `candidate_summary`, `branch`, `status`, `decision`, `paths_touched`  
No `section_id` field.

### `full` only

- `intent_resolution`: `{ "source": "provided"|"inferred"|"mixed"|"none", "intents_used": [...] }`  
- `field_build`: per-candidate map of stored attributes → source used (`seed`/`inference`/…)  
- `proposals`, `raw_validator_log`

---

## Coupling rules

1. Caller builds Request; never reimplements memory-protocol or validators.  
2. Callee never names a parent skill; never issues host tokens.  
3. Opaque labels are not control enums.  
4. Multi-call session logs are caller-owned; row shape is callee-owned.  
5. Callee may read learnt memory under `project_root`; only this skill writes it.  
6. Version bumps + changelog on contract changes.

## Compatibility

| Caller | Behavior |
|--------|----------|
| Minimal v1–v3 Request | Valid; fill paths apply |
| `intents` | Valid seed |
| Removed seeds / `section_id` alone | Ignored or shimmed as above |
| Expects `learning_log_row.section_id` | Use `correlation_id` |
| Expects `intent_resolution` in standard | Use `full` or `include` |

## Changelog

- **4** (rev 2026-11-01) — `rubric-construction` v2: pass domain siblings as `set` for set gates S1–S5.
- **4** (rev 2026-10-26) — Rubric entry body delegated to `rubric-construction`; Request/Response unchanged.
- **4** — Full write fill-path inventory for all storage-mandatory fields; remove active `section_id`; fail-closed predecided; `include` replaces profile defaults; clarify candidates vs learning_log_row; Response `version: 4`.  
- **3** — Lean seeds; intent single rule; situation precedence.  
- **2** / **1** — Superseded.
