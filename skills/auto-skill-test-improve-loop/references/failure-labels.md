# Failure labels

A **failure label** is a short name for what went wrong on a case. It is for humans and for the next patch loop—not a private scoring dialect.

## Quality tests (all must pass)

1. **Repeated in skill** — Prefer leading words, hard-gate phrases, or wording that shows up on multiple steps of the skill under test (or its caller).  
2. **Daily glue only** — Extra words are ordinary English: skipped, rewrote, without, before, checked, never ran.  
3. **No new concepts** — Do not mint tokens like `no_skill_no_unit`, `prose_only_v2`, `FT-fail-A`.  
4. **Disambiguation** — If a skill noun is overloaded in English (`unit`, `move`, `block`, `state`), do **not** use it bare. Use the **full repeated phrase** from the skill, or drop it and name the **procedure that failed** instead.  
5. **Reader test** — Someone who read the skill once should map the label to the right step without a glossary.

## Prefer procedure names over structural jargon

| Weak (ambiguous / one-off) | Stronger (if those phrases actually repeat in *that* skill) |
|----------------------------|---------------------------------------------------------------|
| unit / move / block | open co-review, learn-screen, learn interrupt, hard gate name from skill |
| no_skill_no_X | never ran `$skill-name` / skipped learn interrupt |
| prose_only_* | rewrote draft without \<repeated skill step\> |

If the skill under test does not repeat a phrase, **do not invent one**—describe with daily words + the skill’s `$name` or path.

## Pattern

```text
<what agent did in daily words> without <repeated skill obligation>
```

or

```text
skipped <repeated skill step>
```

## Examples (illustrative—only use if those phrases exist in the skill you evaluate)

| Good | Why |
|------|-----|
| rewrote open co-review draft without learn-screen | procedure + daily words |
| checked learnt/ without running $persist-rubrics-context | observable + skill name |
| skipped learn interrupt | repeated host phrase |
| skill not listed in session skill list | harness precondition, plain |

| Bad | Why |
|-----|-----|
| no_skill_no_unit | invented; `unit` overloaded |
| prose_only_no_skill_load | invented compound |
| grain-fail | jargon, not a repeated procedure name |

## One-line “what happened”

Always pair the label with one sentence of surface fact:

```text
failure_label: skipped learn interrupt
what_happened: agent edited the draft and never opened $persist-rubrics-context/SKILL.md
```
