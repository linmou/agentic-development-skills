# Rubric Construction Principles

Intent: a rubric is useful only if two scorers given the same artifact land on the
same level, and the level means something for a goal the project cares about.
Apply P1–P7 in order when building; `rubric-quality-rubric.md` judges the result.

## P1 — Ground before you write
State the goal the rubric serves (`intent_refs`) and the facts that make that goal
matter here (`context_refs`). If you cannot state both in one sentence each, do not
build the rubric yet.

## P2 — Bound the scope
`applicability.include` says where it applies; `applicability.exclude` names the
nearest case where someone would wrongly apply it. Both non-empty.

## P3 — One feature axis per rubric
A rubric scores one quality. If two criteria can move independently (an artifact can
be high on one, low on the other), they are two rubrics. Within a rubric set, no two
rubrics score the same evidence.

## P4 — Observable level rules
Each `score_X_rule` names an observable condition: presence, count, threshold, or a
named failure. Qualifiers like "good", "mostly", "some", "mild" are allowed only when
quantified ("≥4 of 5 subtasks mapped"). Level rules are ordered and mutually exclusive.

## P5 — Write anchors, imply the levels between
Write rules only for the anchors: top, middle and bottom (5 / 3 / 1 on a 1–5 scale).
Levels between anchors (4, 2) stay implied: "between its two neighboring anchors".
This keeps human review to three rules; counter examples (P7) pin the implied levels.

## P6 — One support example per anchor
For each anchor write one support example that satisfies its rule.

## P7 — Pin every boundary with counter pairs
For each anchor X store `[counter+, counter-]` pairs: `counter+` scores X+1, `counter-`
scores X-1 (usually implied levels), each differing from the X support example by one
feature. Use `N/A` at the top and bottom of the scale. Add `fail_fast` only for a
condition that makes scoring pointless.
