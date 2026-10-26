---
name: note-store
description: Store a plain-text note in the local notes store and return its id.
---

# Note Store

## Call contract (v1)

Request:

| Field | Class | Required | Default |
|-------|-------|----------|---------|
| `version` | control | no | `1` |
| `text` | content | yes | — |
| `caller_tag` | opaque | no | `null` (log only, never control) |

Response: `{ "status": "ok" | "error", "note_id": string | null, "errors": [string] }`

Changelog: v1 initial.

Minimal Request: `{ "text": "Ship the beta on Friday." }`

## Stored record (`notes/<note_id>.json`)

| Attribute | Required | Population rule | Validation |
|-----------|----------|-----------------|------------|
| `note_id` | yes | UUIDv4 generated at write | UUID format |
| `text` | yes | Request `text` | non-empty after trim |
| `slug` | yes | first 5 words of `text`, lowercased; every char outside `[a-z0-9]` → `-`; collapse repeated `-`, trim `-` at ends; cut to 50 chars; empty → `note`; if taken, append `-2`, `-3`, … | `^[a-z0-9-]{1,60}$`, unique |
| `created_at` | yes | UTC now, ISO 8601 | ISO 8601 |

## Procedure

1. Validate Request. `version` ≠ 1 → `status=error`, `errors=["unsupported version"]`; empty `text` after trim → `status=error`, `errors=["text is empty"]`. Nothing written.
2. Build the record using the population rules above.
3. Validate the record; any validation failure → `status=error` with the failing attribute in `errors`, nothing written.
4. Write the file; append `{note_id, caller_tag}` to `notes/log.jsonl`; return `status=ok` and `note_id`.
