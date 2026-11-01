---
name: rubric-construction
description: >
  Construct or audit one scoring rubric: grounded in intent and context, scoped with
  include/exclude, testable per-level rules, support examples, and adjacent-level
  counter-example pairs. Use when writing a new rubric or criterion, turning feedback
  or score meanings into a rubric entry, or checking whether an existing rubric
  (in a skill, a review, or project memory) is well constructed — including whether
  it fits its rubric set (overlap, coverage, conflict, aggregation, granularity).
  Returns the entry and a quality check; never writes project memory.
---

# Rubric Construction

## Purpose
Build or audit **one** rubric entry so that two independent scorers given the same
artifact land on the same level, and the set it joins (existing, or built from
scratch) still measures each goal once. Capability only: no persistence, no
decisions about storage, no host lifecycle.

## Call interface
**SoT:** `references/call-contract.md` (version **2**). Standalone chat → map into
`criteria` + `aggregation` (+ `entry` when auditing, `set` for siblings). Always
finish with a Response.

## Procedure
1. **Parse** — `criteria` text, `aggregation`; optional `intents`, `context_refs`,
   `entry`, `set`, `set_intents`, `mode`. `mode=audit` without `entry` → `status=error`;
   no `aggregation` → `status=needs_input`.
2. **Ground** — `dependencies.intent_refs` from `intents` else inferred goals;
   `dependencies.context_refs` from `context_refs` else inferred situation facts.
   Neither inferable → `status=needs_input`, list what is missing.
3. **Construct** (`mode=construct`) — fill `references/rubric-entry-template.md` by
   applying `references/construction-principles.md` P1–P7 in order. With `entry`,
   refine it and keep its `id`.
4. **Check** — run `scripts/validate_rubric_entry.py` (mechanical gates), then score
   `references/rubric-quality-rubric.md` (judgment gates + dimensions) and
   `references/rubric-set-gates.md` (S1–S5 against `set`).
   In `construct`, repair and re-check at most 2 rounds; stop early on `pass` or
   when the gap needs human input (`needs_input`). Rubric text in `audit` gets
   G1–G4 by reading.
5. **Respond** — Response JSON per contract. Stop.

## Rules
1. One entry per call. Several criteria in `criteria` → construct the first, list
   the rest in `issues` as `split:` items.
2. Do not invent examples that contradict the feedback; synthesized examples must
   satisfy the level rule they illustrate.
3. Never write files outside the caller's explicit path; never touch project memory.

## Progressive Disclosure
- `references/construction-principles.md` — P1–P7, how to build
- `references/rubric-entry-template.md` — entry schema + worked examples
- `references/rubric-quality-rubric.md` — how to judge a built entry
- `references/rubric-set-gates.md` — S1–S5, how the entry fits its set
- `references/call-contract.md` — Request/Response v2
- `scripts/validate_rubric_entry.py` — mechanical shape check
