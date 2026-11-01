# Rubric Persistence Rubric (Add/Update for rubric memory)

Use this rubric to decide whether a **constructed** rubric entry should enter project memory.
Entry construction and its quality check belong to skill `rubric-construction`
(Response `check`); this file only judges persistence.

## Scope
- Target memory: `./.co-improvement/learnt/rubrics/` + `index.json`
- Input: `rubric-construction` Response (`entry` + `check`)
- Operation type: `add` or `update`

## Scale
- 1 = poor / missing
- 2-3 = partial / weak
- 4 = good
- 5 = excellent

## Dimensions (score all)
1. Non-Overlap
   - `add`: genuinely new versus existing entries.
   - `update`: materially improves an existing entry without duplicating another.
2. Reuse Value
   - Entry is likely reusable across multiple future loops, not one-off.
3. Durability
   - Stable enough beyond transient phrasing or temporary workflow detail.

## Hard Gates (must pass)
1. Construction check passed
   - `check.verdict == "pass"` from `rubric-construction` (gates G1–G6 + quality dimensions)
2. Non-overlap threshold for append
   - if `Non-Overlap < 4`, do not `append` as a new entry

## Decision Policy
- `append`: pass all hard gates, `Non-Overlap >= 4`, `Reuse Value >= 4`.
- `merge`: construction check passed, but semantic overlap exists and candidate improves precision/examples of an existing entry.
- `skip`: construction check not `pass` after repair, or weak `Reuse Value`.
- `ask_human`: use when `append` and `merge` both look plausible (boundary overlap or unclear scope split).

## Decision Output Template
- Candidate rubric id/title: ...
- Operation type: `add` | `update`
- Construction check: verdict [pass/revise/fail] (+ issues)
- Scores:
  - Non-Overlap: [1-5]
  - Reuse Value: [1-5]
  - Durability: [1-5]
- Hard gate check:
  - Construction check passed: [pass/fail]
  - Non-overlap threshold for append: [pass/fail]
- Proposed decision: `append` | `merge` | `skip` (human confirmation required before any write; authority is `persist-rubrics-context`, not this template)
- Reason: ...
- Merge target (if merge): ...
