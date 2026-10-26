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
| `slug` | yes | — | `^[a-z0-9-]{1,60}$`, unique |
| `created_at` | yes | UTC now, ISO 8601 | ISO 8601 |

## Procedure

1. Validate Request. Empty `text` after trim → `status=error`, `errors=["text is empty"]`, nothing written.
2. Build the record.
3. Validate the record; any validation failure → `status=error` with the failing attribute in `errors`, nothing written.
4. Write the file; return `status=ok` and `note_id`.
