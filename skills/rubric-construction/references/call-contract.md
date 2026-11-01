# Call Contract — `rubric-construction`

Version: **2**

Stable interface between any caller and this capability. Callee never writes
project memory and never names a caller.

## Request

| Field | Required | Default | Class | Notes |
|-------|----------|---------|-------|-------|
| `criteria` | yes | — | content | Criterion text, score meanings, examples, override reasons |
| `intents` | no | `[]` | seed | Goal sentences → `dependencies.intent_refs` (else inferred) |
| `context_refs` | no | `[]` | seed | Situation facts → `dependencies.context_refs` (else inferred) |
| `entry` | no | `null` | content | Existing entry: refine (`construct`, JSON) or check (`audit`, JSON or rubric text) |
| `set` | no | `[]` | content | Sibling entries the entry joins (JSON or rubric text); `[]` = first entry of a new set |
| `set_intents` | no | `[]` | seed | Goals the whole set serves, for S2 (else union of `intents` and siblings' `intent_refs`) |
| `aggregation` | yes | — | content | How set scores combine: hard gate, weights, or `"reported separately"` |
| `mode` | no | `"construct"` | control | `construct` \| `audit`; `audit` requires `entry` |

Precedence per field: seed > `entry` (refine base) > inference from `criteria`.
Unknown fields: ignore.

## Entry fill paths

| Field | Source | Rule |
|-------|--------|------|
| `id` | `entry.id` → inference | `RUB-<SLUG>` from title; refine keeps existing id |
| `title` | inference | Name of the one quality scored (P3) |
| `applicability.*` | inference | P2 |
| `dependencies.intent_refs` | seed → inference | P1; durable goals, not task titles |
| `dependencies.context_refs` | seed → inference | P1; facts, not goals |
| `decision_rule.*` | inference | P4–P7; levels only as the criteria justify, plus any P5 requires |
| `lifecycle.sunset_condition` | inference | String, may be `""` |

Any field not constructible → `status=needs_input` with `missing`; never emit a
partial entry as `ok`.

## Response

```json
{
  "skill": "rubric-construction",
  "version": 1,
  "status": "ok",
  "entry": {"id": "RUB-SHORT-COMMITS", "...": "..."},
  "check": {
    "verdict": "pass",
    "gates": {"G1": "pass", "G2": "pass", "G3": "pass", "G4": "pass", "G5": "pass", "G6": "pass",
              "S1": "pass", "S2": "pass", "S3": "pass", "S4": "pass", "S5": "pass"},
    "dimensions": {"grounding": 3, "scope": 3, "single_axis": 3, "rule_testability": 3, "boundary_sharpness": 3},
    "issues": []
  },
  "missing": [],
  "errors": []
}
```

| `status` | Meaning |
|----------|---------|
| `ok` | `entry` built (or audited) and `check` filled |
| `needs_input` | Human must supply items in `missing`; `entry` is `null` |
| `error` | Invalid Request (e.g. `audit` without `entry`); see `errors` |

`audit` returns the given `entry` unchanged plus `check`. Rubric text (not template
JSON) is checked against G1–G4 by reading, not by the script; `check.issues` says so.
`construct` may return `ok` with verdict `revise`/`fail` after 2 repair rounds; the
caller decides whether that is usable.
Set gates S1–S5 (`rubric-set-gates.md`) sit in `check.gates` beside G1–G6 and count
toward `verdict` like any gate. A set failure whose fix touches a sibling →
`needs_input` naming the sibling id and the fix (merge, split, drop). `set` entries
are never changed.

## Examples

```json
{"criteria": "Commit subject under 50 chars; imperative mood; no trailing period.",
 "aggregation": "reported separately"}
```

```json
{"criteria": "Tighten level 3 boundary.", "entry": {"id": "RUB-SHORT-COMMITS", "...": "..."},
 "set": [{"id": "RUB-COMMIT-SCOPE", "...": "..."}], "aggregation": "hard gate: every entry >= 3"}
```

## Changelog
- **2** — Set gates S1–S5 in every check: `set`, `set_intents`, required `aggregation`.
- **1** — Initial; extracted from a memory-write skill's rubric fill paths.
