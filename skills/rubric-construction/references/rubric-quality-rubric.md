# Rubric Quality Rubric

Intent: judge whether one built rubric entry follows `construction-principles.md`,
so a caller can trust it before scoring with it or storing it.

## Scope
- include: one rubric entry (template shape, or an equivalent markdown rubric)
- exclude: whether the entry is worth storing, or overlaps stored memory — that is
  the caller's persistence decision

## Hard gates
Mechanical (`scripts/validate_rubric_entry.py`):
- G1 `dependencies.intent_refs` and `dependencies.context_refs` non-empty string lists
- G2 `applicability.include` and `applicability.exclude` non-empty string lists
- G3 each defined level has rule, non-empty support examples, non-empty counter pairs
- G4 each counter item is a two-string list `[counter+, counter-]`

Judgment:
- G5 top, middle and bottom anchors have rules; counters target X±1 (P5, P7)
- G6 no level rule relies on an unquantified qualifier (P4)

## Dimensions (scale: 1 fail · 2 weak · 3 meets)
Each row is a one-feature ladder: L2 removes one feature from L3, L1 one from L2.

| Dimension | 3 — meets | 2 — weak | 1 — fail |
|-----------|-----------|----------|----------|
| Grounding (P1) | intent + context refs each name a concrete goal / fact, and the rule visibly serves the goal | refs concrete, but the rule does not visibly serve the goal | refs are restated criterion text, not goal / fact |
| Scope (P2) | exclude names the nearest misapplication | exclude present but generic ("other cases") | exclude is the negation of include |
| Single axis (P3) | one quality; every level rule tests that quality | one quality, but one level rule tests a different feature | two independent qualities in one rule set |
| Rule testability (P4) | every level rule observable, ordered, exclusive | observable, but two adjacent levels overlap | at least one level rule is opinion-only |
| Boundary sharpness (P6–P7) | every counter differs from its support example by one feature | counters exist, some differ by ≥2 features | counters do not land on the neighbor level |

Example ladder (Scope): L3 "exclude: single-step quick edits" for a multi-step
decomposition rubric · L2 "exclude: other tasks" · L1 "exclude: not multi-step tasks".

## Verdict
"All gates" includes set gates S1–S5 (`rubric-set-gates.md`).
- `pass` — all gates pass, every dimension 3
- `revise` — all gates pass, some dimension 2
- `fail` — any gate fails or any dimension 1
