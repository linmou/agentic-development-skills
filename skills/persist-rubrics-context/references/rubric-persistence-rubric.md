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
Overlap with stored rubrics is not scored here: `rubric-construction` gate S1 judges
it against the same-domain `set`.
1. Reuse Value
   - Entry is likely reusable across multiple future loops, not one-off.
2. Durability
   - Stable enough beyond transient phrasing or temporary workflow detail.

## Hard Gates (must pass)
1. Construction check passed
   - `check.verdict == "pass"` from `rubric-construction` (gates G1–G6, S1–S5 + quality grades)

## Decision Policy
- `append`: hard gate passes, `Reuse Value >= 4`.
- `merge`: S1 fix is `merge` into one sibling, and the candidate improves that entry's precision/examples; rebuild with that sibling as `entry`.
- `skip`: construction check not `pass` after repair, or weak `Reuse Value`.
- `ask_human`: S1 fix names several siblings, or proposes split/drop of a stored entry.

## Decision Output Template
- Candidate rubric id/title: ...
- Operation type: `add` | `update`
- Construction check: verdict [pass/revise/fail] (+ issues)
- Scores:
  - Reuse Value: [1-5]
  - Durability: [1-5]
- Hard gate check:
  - Construction check passed: [pass/fail] (+ S1 fix, if any)
- Proposed decision: `append` | `merge` | `skip` (human confirmation required before any write; authority is `persist-rubrics-context`, not this template)
- Reason: ...
- Merge target (if merge): ...
