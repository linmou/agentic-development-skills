# Extraction Split Rubric (C1–C3, C4a, C5–C6)

Use when diagnosing a **host skill → extracted skill** split.  
For **C4b field API design**, use `call-contract-field-rubric.md` (different concern).

## Scope
- Target: host + extracted skill folders (SKILL.md, adapters, contracts, scripts, references)
- Operation: audit only (do not rewrite unless user asks after report)
- Verdict units: criteria C1–C6 in `criteria.md`

## Scale
- 1 = poor / missing
- 2–3 = partial / weak
- 4 = good
- 5 = excellent

Score every dimension under the criterion you are judging.  
**Blocking criteria** fail overall extract if hard gates fail (see each section).

---

## C1 — Capability, not lifecycle (blocking)

### Dimensions
1. **Capability identity** — Extract names a reusable job (what it does), not a host state.
2. **Orchestration ownership** — Host still owns when to call, gates, host tokens.
3. **No inline residue** — Host does not keep the full capability procedure after claiming extraction.

| Score | Capability identity | Orchestration ownership | No inline residue |
|-------|---------------------|-------------------------|-------------------|
| 1 | Only “State N of host X” | Extract issues host tokens / advances sections | Host still is the write/capability engine |
| 3 | Mixed capability + host vocabulary | Host mostly owns timing; some leakage | Partial duplicate procedure |
| 5 | Clear standalone capability | Host owns when/gates/tokens only | Host is thin client or pure orchestrator |

### Hard gates
1. Extract description/procedure usable without host loop  
2. Host owns host tokens and section advance  
3. Host does not inline the full extracted capability as primary path  

### Decision
- **pass:** all hard gates; all dimensions ≥ 4  
- **fail:** any hard gate fail, or any dimension ≤ 2  

---

## C2 — One-way dependency (blocking)

### Dimensions
1. **Host → extract reference** — Host names `$extracted`, path, or subagent.
2. **No reverse import** — Extract tree does not name the host skill as a dependency.
3. **No host tokens on callee** — Extract does not collect/issue host checkpoint tokens.

| Score | Host→extract | No reverse import | No host tokens on callee |
|-------|--------------|-------------------|---------------------------|
| 1 | No invoke path | Extract requires host by name/states | Callee issues PERSIST_OK / REVIEW_OK / … |
| 3 | Invoke present but informal | Historical host name in comments only | Tokens mentioned only as “do not issue” |
| 5 | Clear subagent/`$name` path | Grep clean of host skill name as dependency | Callee never owns host tokens |

### Hard gates
1. Host references extract  
2. Extract does not reverse-import host by name as required path  
3. Extract does not issue host tokens  

### Decision
- **pass:** all hard gates; dimensions ≥ 4 (dimension 2 may be 3 if only historical notes and user accepts — still prefer fail if name appears in active procedure)  
- **fail:** any hard gate fail  

---

## C3 — Single writer, thin client (blocking)

### Dimensions
1. **Side-effect ownership** — Domain writes/validators/protocols live on extract.
2. **Thin client shape** — Host: build Request → invoke → merge Response → resume.
3. **Audit without dual write** — Host may re-invoke extract then issue host token; must not reimplement writes.
4. **No second engine** — Host does not ship a full second copy of write protocols/scripts as primary.

| Score | Side effects | Thin client | Audit | No second engine |
|-------|--------------|-------------|-------|------------------|
| 1 | Both write same memory | Host reimplements capability | “Fallback” writes inline | Duplicate protocol/scripts both primary |
| 3 | Mostly extract; host edge writes | Adapter mostly thin | Audit sometimes inlines | Stale copies remain unused |
| 5 | Extract owns domain side effects | Clean Request/Response adapter | Audit only re-invokes | Single write engine on extract |

### Hard gates
1. No dual writers for the same domain memory  
2. Host invoke path exists (subagent or `$extracted`)  
3. Audit/fallback does not implement domain writes without calling extract  
4. Extract does not advance host sections  

### Decision
- **pass:** all hard gates; dimensions ≥ 4  
- **fail:** any hard gate fail, or dual writer observed  

---

## C4a — Contract exists + opaque labels (blocking if imported)

**Opaque labels** means: fields such as `caller_tag` / correlation ids are **caller log stamps**. The callee must not require host FSM values in them and must not branch control logic on them.  
This is **coupling hygiene**, not field API design (C4b).

### Dimensions
1. **Contract existence** — Versioned Request/Response (or equivalent) on callee; optionals have defaults.
2. **Schema ownership** — Host does not redefine Response/Request field meanings.
3. **Opaque labels** — Correlation tags are log-only; no host-state required enums for control.
4. **Third-party callability** — Required API usable without host FSM vocabulary.

| Score | Existence | Schema ownership | Opaque labels | Third-party |
|-------|-----------|------------------|---------------|-------------|
| 1 | Vague prose only | Host invents incompatible fields | Callee branches on host tags | Required host states |
| 3 | Partial schema | Minor host extensions | Tags documented but examples host-only | Possible with folklore |
| 5 | Versioned contract + defaults | Host packs/merges only | Tags ignored for control | Minimal third-party Request works |

### Hard gates
1. Contract artifact exists on callee when import path exists  
2. Host does not redefine callee schema  
3. Callee does not require host FSM enums for control  
4. Opaque labels are not control switches  

### Decision
- **pass:** all hard gates; dimensions ≥ 4  
- **fail:** any hard gate fail  
- **N/A:** no import/subagent path (document and skip C4a/C4b blocking)

Then score **C4b** with `call-contract-field-rubric.md`.

---

## C5 — Standalone trigger (blocking)

### Dimensions
1. **Description independence** — Frontmatter works without naming the host as required context.
2. **Runnable alone** — Human/agent can run `$extracted` on the capability with only extract docs.

| Score | Description | Runnable alone |
|-------|-------------|----------------|
| 1 | Only “part of host X” | Cannot run without host procedure |
| 3 | Mentions host as example only | Runnable with effort |
| 5 | Standalone triggers and purpose | Clear standalone path |

### Hard gates
1. Description does not require host to understand the skill  
2. Extract SKILL procedure is runnable without host steps  

### Decision
- **pass:** hard gates; dimensions ≥ 4  
- **fail:** any hard gate fail  

---

## C6 — Completeness (non-blocking)

### Dimensions
1. Assets moved to callee  
2. Host rewritten as adapter  
3. Host write-engine copies removed  
4. Reverse-dep grep clean  
5. Contract on callee if imported  

| Score | Meaning |
|-------|---------|
| 1 | Extraction claimed complete; major items missing |
| 3 | Partial move; leftovers documented or harmless |
| 5 | Checklist complete for the claimed extract |

### Hard gates
None for overall `pass` (non-blocking).  
If user claimed “complete extract” and score ≤ 2 on assets/adapter/copies → report as **fail** under C6 still non-blocking for overall unless user policy says otherwise; default: **warning**.

### Decision
- **pass:** most checklist items true (note misses)  
- **fail (warning):** claimed complete but major gaps  
- Always list misses in report  

---

## Combined decision output template

```text
Extraction split scores
C1 Capability vs lifecycle: dims [...] hard gates [...] → pass|fail
C2 One-way dependency: ...
C3 Single writer / thin client: ...
C4a Contract + opaque labels: ...
C4b Field API: (see call-contract-field-rubric output)
C5 Standalone trigger: ...
C6 Completeness: ... (non-blocking)

Overall: pass | fail | insufficient_evidence
Blocking fails: ...
Top fixes:
1. ...
```

---

## Evidence map

| Criterion | Primary evidence |
|-----------|------------------|
| C1 | Both SKILL.md purpose/procedure; host state machine |
| C2 | Grep host name in extract; token language; host invoke lines |
| C3 | Write paths; adapters; duplicate scripts/protocols; audit gates |
| C4a | call-contract; host adapter; Request examples |
| C4b | `call-contract-field-rubric.md` on contract fields |
| C5 | Extract frontmatter description; standalone procedure |
| C6 | File trees; grep; adapter vs inlined protocol |
