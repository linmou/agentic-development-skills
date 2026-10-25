# Call-Contract Field Rubric (C4b — API design)

Use when the extracted skill exposes a Request/Response (or equivalent) for host or third-party import.

## Scope
- Target: callee call contract (Request fields, Response fields, defaults, modes, examples, version)
- **In scope for hard gate 4:** every mandatory declared output artifact, including status/error outputs, plus required internal implementation artifacts needed to construct or validate those outputs. If the extract persists artifacts, also inspect mandatory stored attributes as a subordinate persistence check; storage fields are not automatically API fields.
- Not in scope: host lifecycle UX
- Not in scope: **opaque labels alone** — that is C4a coupling (see `extraction-split-rubric.md`). This rubric scores **field API quality**.

## How to score (required)

Do **not** one-shot D1–D7 after skimming the contract.  
Run **`references/single-agent-multi-pass-scoring.md`** (Pass A inventory/crosswalk → B strict → C contradiction → D lock).

**Lesson baked in:** solo extract-verify once marked C4b pass while multi-debate found an unconstructible required artifact. Pass A exists to make output dependencies, resolution rules, and conditional persistence checks mechanical.

## Scale
- 1 = poor / missing
- 2–3 = partial / weak
- 4 = good
- 5 = excellent

Score **all** dimensions D1–D7.  
**Do not award 5** unless Pass C listed attacks and none held.

---

## Dimensions

### D1 — Necessity (minimal surface)
Does every Request (and default-profile Response) field earn its place?

| Score | Anchor |
|-------|--------|
| 1 | Many fields unused, decorative, or required without a capability reason |
| 3 | Core fields justified; some optional bloat or a policy enum that restates one default rule |
| 5 | Each field is content, seed, control, output, or opaque bookkeeping; no debug-only fields in default/`standard` profile; no enum that only renames “use seed if present else infer” |

### D2 — Sufficiency (capability-complete)
Can a third caller complete the capability with required fields + defaults?

| Score | Anchor |
|-------|--------|
| 1 | Required set cannot complete the job; missing control or content; Response is prose-only |
| 3 | Happy path works; an edge output has missing dependencies, an undocumented resolution rule, or an internal/persistence artifact lacks a valid construction path |
| 5 | Required + defaults construct every mandatory output from declared inputs, available capabilities, and internal resolution rules. Any failure path has a bounded, reachable, capability-consistent trigger and a constructible failure Response; Response carries status, writes/errors, and optional log row for thin hosts |

### D3 — Non-overlap (one job per field)
Are fields orthogonal, with precedence when channels meet?

| Score | Anchor |
|-------|--------|
| 1 | Dual fields for the same slot with no winner; triple channels for one meaning; default Response echoes the same story 3 ways |
| 3 | Mild overlap; aliases exist; precedence partial or only in examples |
| 5 | One job per field; aliases document winner + deprecation; multi-source attributes have stated precedence; default Response is not an audit echo stack |

### D4 — Clarity (names, defaults, examples)
Would a stranger map fields to roles without host folklore?

| Score | Anchor |
|-------|--------|
| 1 | Names ambiguous or host-shaped; no defaults; examples only show host FSM tags as required shape |
| 3 | Mostly clear; some seed vs stored confusion; one minimal example missing |
| 5 | Names match role (goal vs situation vs rule; seed vs stored; control vs opaque); defaults explicit; examples include a **minimal** third-party Request and optionally one seeded Request |

### D5 — Consistency (no contradictions)
Do modes, narrative, and persistence rules agree?

| Score | Anchor |
|-------|--------|
| 1 | Dead inputs (accepted then ignored); “not persisted” seeds silently become durable; minimal-call story contradicts mode matrix; session goals forced into durable fields with no rule |
| 3 | One mild inconsistency documented or rare |
| 5 | No dead fields; persistence rules match seed language; mode matrix matches minimal-call claim; ephemeral vs durable inputs distinguished with a generalization rule when needed |

### D6 — Layering (contract vs storage vs host)
Is the boundary at the right abstraction?

| Score | Anchor |
|-------|--------|
| 1 | Request is a dump of full domain file schema; host tokens required; host redefines Response fields |
| 3 | Mostly layered; occasional storage leakage or host-shaped optional fields |
| 5 | Request is call I/O not file schema (unless skill job is schema edit); host tokens/states not required enums; callee owns schema; host adapter only packs/merges |

### D7 — Evolvability
Can the API change without silent breakage?

| Score | Anchor |
|-------|--------|
| 1 | No version; breaking renames undocumented; dual names forever with no winner |
| 3 | Version present; changelog thin; aliases without retirement path |
| 5 | Version + changelog on field changes; alias winner + retirement path; additive optionals preferred over silent breaks |

---

## Hard gates (must pass for C4b pass when contract is the import path)

1. **Minimal call works** — required fields + defaults complete capability, or documented fail-closed  
2. **No host control enums** — third party need not know host state names as required API  
3. **No silent dual meaning** — same slot, two fields → documented winner  
4. **Output constructibility** — every mandatory declared output artifact has a documented path from declared inputs, available capabilities, and internal resolution rules, or a meaningful explicit failure condition. Normal construction must remain possible; generic catch-all failure cannot substitute for a normal path. The implementation crosswalk must also cover every required internal artifact needed to construct or validate an output, including its producer, dependencies/capabilities, validation, and failure behavior.  
   - Build the Pass A output crosswalk from the contract, capability declarations, resolvers, and validators.  
   - Build a separate implementation crosswalk for required internal artifacts. An internal artifact may remain private and need not appear in the public Request, but it must have an identified producer, declared dependencies/capabilities, validation rule, and failure behavior.  
   - If persistence applies, add a subordinate persistence crosswalk proving mandatory stored attributes can be populated and validated by valid internal rules. Storage fields need not appear in the public Request.  
   - An explicit failure condition is meaningful only when its trigger is bounded, reachable from documented inputs/capabilities, and consistent with the capability boundary; the failure Response/artifact must itself be constructible and validated.  
   - Missing dependencies, undocumented assumptions, invalid paths, generic failure-only handling, or a failure condition without a constructible normal path fail this gate.  
   - Happy-path minimal Request is gate 1, **not** gate 4.  
5. **Precedence** — if ≥2 inputs can fill one attribute, order is stated  
6. **Necessity floor** — D1 ≥ 3 (catastrophic bloat still fails even if hard gates 1–5 pass)  
7. **Sufficiency floor** — D2 ≥ 4  
8. **Consistency floor** — D5 ≥ 3; if D5 = 1, fail regardless of other scores  

---

## Decision policy

| Verdict | When |
|---------|------|
| **pass** | All hard gates pass; D1–D6 ≥ 4; D7 ≥ 3 with version/alias plan; multi-pass A–D complete |
| **fail** | Any hard gate fails, or any of D1–D5 ≤ 2, or third-party use unsafe, or an output, implementation, or applicable persistence crosswalk has Gap=y |
| **insufficient_evidence** | No contract / cannot enumerate mandatory outputs, required internal artifacts, or applicable persistence requirements / multi-pass A incomplete |
| **smell-only** (still pass if gates ok) | D1 or D3 = 3 only from mild bloat/audit-echo/long aliases with a winner — list under Fix, do not alone fail |

**Anti-pattern:** awarding D2=5 because “minimal call works” while mandatory output or applicable persistence paths remain unresolved.

---

## Field classes (Request inventory)

| Class | Role | Example |
|-------|------|---------|
| content | Primary material to process | `human_feedback` |
| seed | Optional help to fill callee-derived fields | `intents` |
| control | Decision / write behavior | `decision_mode` |
| output | What to return or side-log | `output_profile`, `include` |
| opaque | Caller bookkeeping only (never domain control) | `caller_tag`, `correlation_id` |

---

## Decision output template

Use the multi-pass block in `single-agent-multi-pass-scoring.md`, or:

```text
C4b — Call-contract field API
Contract path: ...
Multi-pass: A/B/C/D complete: y/n
Output crosswalk gaps: none | list...
Implementation crosswalk gaps: none | list...
Failure-policy evidence: bounded/reachable/capability-consistent trigger; constructible validated failure artifact; normal path present
Conditional persistence gaps: n/a | none | list...
Request inventory:
  | Field | Class | Needed? | Overlaps? | Precedence | Keep/merge/drop |
Scores (after Pass C):
  D1–D7: ...
Hard gates 1-8: ...
Pass C attacks held: ...
Verdict: pass | fail | insufficient_evidence
Smells: ...
Fix: ...
```

---

## Common failure patterns

1. Host-shaped leftovers as required API  
2. Fat seed surface (multiple “situation” or “goal” channels, no precedence)  
3. Policy enum inflation (three modes = one default rule)  
4. Session goals stamped into durable memory fields with no generalization  
5. Audit echo in standard Response (resolution + tags + field_build)  
6. Alias soup (`section_id` + `correlation_id` both first-class forever)  
7. **Happy-path D2** — minimal call works; mandatory outputs or applicable persistence attributes still lack construction paths (**multi-debate killer**)
8. **Author–auditor collapse** — scorer just wrote the contract; skips contradiction pass
