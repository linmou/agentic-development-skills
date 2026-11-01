# Rubric Set Gates

Intent: a rubric is never scored alone. When a new entry joins an existing set, or a
set is built from scratch one entry at a time, the set must still measure each goal
once, cover every goal, and combine as declared. Per-entry quality is
`rubric-quality-rubric.md`; this file judges the new entry against its `set`.

## Scope
- include: the new entry plus every sibling in `set` (empty `set` = first entry
  of a set built from scratch)
- exclude: domain gates the caller adds for its own set; scale calibration across
  entries

## Gates (semantic; each `pass` | `fail`)
- S1 Non-overlap — the entry scores no evidence or quality a sibling already scores.
  Containment counts both ways: the entry's whole scale is one clause of a sibling
  level rule, or a sibling's whole scale is one clause of the entry's.
- S2 Coverage — the entry's `intent_refs` map to a set intent (no orphan). Set
  intents still served by no entry are listed in `issues` as `uncovered:` items;
  they do not fail the gate.
- S3 No conflict — where applicability overlaps a sibling's, no observable feature
  is rewarded by the entry and penalized by the sibling, or the reverse.
- S4 Aggregation — `aggregation` states how set scores combine (hard gate, weights,
  or reported separately) and gives the entry a role in it.
- S5 Granularity — the smallest artifact part a scorer must read to decide the
  entry's level (e.g. sentence < paragraph < section < whole artifact) is within
  one step of the siblings serving the same intent. Fail example: "abstract states
  one contribution" beside "paper argues its thesis coherently" under one intent.

With an empty `set`, S1, S3 and S5 pass trivially; S2 and S4 still apply.

## Repair
Fix inside the entry when possible: narrow `applicability` or the level rule (S1, S3),
re-target the evidence span (S5). When the fix touches a sibling (merge, split, drop)
or needs a set intent or `aggregation` from the human → `needs_input`.
