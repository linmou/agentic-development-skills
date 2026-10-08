# Single-agent multi-pass scoring (distilled from multi-debate)

Use this **inside** `skill-extract-verify` when scoring rubrics (especially **C4b**).  
It replaces the need to spawn three reviewers for routine extract audits, by forcing the **same evidence moves** multi-debate used when it beat a solo extract-verify score.

## What multi-debate caught that solo extract-verify missed

| Episode (persist-rubrics-context) | Solo extract-verify | Multi-debate |
|-----------------------------------|---------------------|--------------|
| Call contract v3 after lean API | C4b **pass**; D2≈5 | D2 **fail/3**; hard gate 4 fail |
| Decisive evidence | Read contract + intent seed rule | **Cross-walked mandatory outputs** (dependencies, resolvers, validation, failure conditions); persistence attributes are subordinate when applicable |
| Outcome | False confidence | Required output and implementation crosswalk → later all D=5 |

### Root reasons (not “need three models”)

1. **Author–auditor collapse** — Same run refined the contract and scored it. Solo scoring optimized for “lean Request” and under-applied hard gate 4 against output dependencies and internal resolution.  
2. **Incomplete evidence plan** — Gather listed “contract fields,” not every mandatory output and its construction evidence.  
3. **No mandatory counterevidence** — Dimensions got supporting quotes only; no forced “what would make this a 3?”  
4. **Happy-path sufficiency** — Minimal Request works → D2 treated as 5, while an edge output still lacks a dependency, resolver, validation path, or meaningful failure condition.  
5. **Single stance** — No separate **inventory**, **strict floor**, and **contradiction** passes; one blended charitable read.  
6. **No re-score loop** — No second pass only on weak/high scores after adversary notes.

Multi-agent helped because of **role separation + schema cross-walk + counterevidence**, not because three chat windows are magic.

---

## Single-agent procedure (do in order)

Complete these **four passes** before locking C4b (and use Pass B/C on any other criterion you scored 5 after editing the extract yourself).

### Pass A — Inventory (neutral clerk)

Goal: facts only, no scores yet.

1. List **Request** fields (class, required/default).  
2. List **standard Response** keys.  
3. Build the **mandatory output set** from the contract and declared profiles, including status/error artifacts:
   - output schemas and profile rules
   - capability declarations and internal resolvers
   - validators and failure rules  
4. Build the **output-construction crosswalk** with columns for output artifact, mandatory condition/profile, inputs/capabilities, internal resolver/path, validation, failure condition, and gap.

| Output artifact | Mandatory condition/profile | Inputs/capabilities | Resolver/path | Validation | Failure condition | Gap? |
|-----------------|-----------------------------|---------------------|--------------|------------|-------------------|------|
| … | … | … | … | … | … | y/n |

5. Build a separate **implementation crosswalk** for every required internal artifact needed to construct or validate a mandatory output, even when it is neither public nor persisted. Record the artifact, producer, dependencies/capabilities, construction path, validation, failure behavior, and gap.

| Internal artifact | Producer | Dependencies/capabilities | Construction path | Validation | Failure behavior | Gap? |
|-------------------|----------|---------------------------|-------------------|------------|------------------|------|
| … | … | … | … | … | … | y/n |

6. If persistence applies, add a subordinate crosswalk for mandatory stored attributes and their internal population/validation rules. Do not require storage fields in the public contract solely because they are persisted.
7. Note dual fields, aliases, mode fail-closed rules, profile/`include` rules, and undocumented assumptions. For each explicit failure condition, record the bounded trigger, why it is reachable from declared inputs/capabilities, why it is capability-consistent, and how the failure Response/artifact is constructed and validated. A failure-only or generic catch-all path is not sufficient; the normal construction path must also be present.

*Done when:* every mandatory output and required internal artifact is a crosswalk row; every Request field is inventoried; persistence is marked applicable or n/a; every explicit failure condition has the required evidence.  
**If any output or implementation Gap=y, or a persistence gap exists when applicable, hard gate 4 cannot pass** until fixed or scored fail.

### Constructibility regression matrix

| Case | Persistence | Expected result |
|------|-------------|-----------------|
| Declared input and capability construct a non-persistent output | n/a | Gate 4 passes; no storage crosswalk required |
| Internal storage field is populated by a documented resolver and validated | applicable | Interface passes; subordinate persistence check passes; storage field need not be public |
| Required output depends on an unavailable or undeclared capability | either | Gate 4 fails |
| Resolver path or assumption is undocumented/invalid | either | Gate 4 fails |
| Meaningful bounded failure condition exists and normal path remains constructible | either | Gate 4 may pass |
| Generic catch-all failure is the only path | either | Gate 4 fails |
| Persistent validator requires an attribute with no valid internal population rule | applicable | Persistence check fails; Gate 4 fails |

### Pass B — Strict floors (reject unsupported excellence)

Goal: apply anchors and hard gates **pessimistically**.

1. Score D1–D7 with anchors; **start from 4 max** unless anchor-5 language is **explicitly** satisfied in the contract text.  
2. Mark each hard gate pass/fail with one evidence cite.  
3. For any Di you want ≥4, write **one counterevidence attempt** (even if weak).  
4. If counterevidence is unanswered by contract text → lower score or fail the related gate.

*Done when:* scores + gates filled; every Di has ≥1 evidence and ≥1 counterevidence attempt (or “none found after X checks”).

### Pass C — Contradiction hunt (disconfirm)

Goal: try to **break** Pass B, especially scores of 5 and gates marked pass.

Attack checklist (from multi-debate failure patterns):

1. Mandatory output missing from the construction table  
2. Dependency or capability assumed but not declared  
3. Resolver path claimed but not documented or invalid  
4. Explicit failure condition is generic, while no normal construction path exists  
5. Failure trigger is unbounded, unreachable, or inconsistent with the declared capability  
6. Failure Response/artifact cannot be constructed or validated  
7. Required internal artifact lacks a producer, dependency, validation, or failure behavior  
8. Persistence attribute lacks an internal population/validation rule when persistence applies  
9. Happy path conflated with D2=5  
10. Dual fields / aliases without winner + retirement  
11. Dead inputs (accepted then ignored)  
12. Session goal → durable field without generalization rule  
13. Standard Response audit-echo stack  
14. Mode matrix vs minimal-call story  
15. Request dump of file schema (layering) or host FSM required enums  
16. You authored the contract this session → **mandatory** Pass C; never lock all-5s without it  

For each successful attack: lower the dimension and flip hard gates if needed.

*Done when:* Pass C log lists attacks tried + outcome (held / lowered).

### Pass D — Lock (only after A–C)

1. Final D1–D7 and hard gates.  
2. C4b verdict per decision policy.  
3. If any Di was revised in Pass C, do **not** re-raise it in the same turn without new contract text.

---

## Output block (paste into extract-verify report under C4b)

```text
## C4b multi-pass (single agent)

### Pass A — Output-construction crosswalk
| Output artifact | Mandatory condition/profile | Inputs/capabilities | Resolver/path | Validation | Failure condition | Gap? |
| ... | ... | ... | ... | ... | ... | y/n |

Conditional persistence crosswalk: n/a | complete | gaps listed
Implementation crosswalk: complete | gaps listed
Failure-policy evidence: bounded/reachable/capability-consistent trigger; constructible validated failure artifact; normal path present

Request inventory: (n fields)
Standard Response keys: ...

### Pass B — Strict scores
D1–D7: ...
Hard gates 1–8: ...
Counterevidence notes: ...

### Pass C — Attacks
1. ... → held | lowered Di to N
...

### Lock
Scores: D1=… … D7=…
Hard gates: ...
Verdict: pass|fail|insufficient_evidence
Smells: ...
Fix: ...
```

---

## When to still use full multi-debate

Use `review-with-multi-debate` (true parallel reviewers) when:

- C4b is blocking and Pass C leaves **unresolved** tension (you can argue both ways at ≥0.8 confidence)
- User demands independent audits on disk
- You both authored and must certify “all dimensions = 5”

Otherwise this single-agent multi-pass is the default inside extract-verify.

---

## Mapping multi-debate roles → passes

| Multi-debate role | Single-agent pass |
|-------------------|-------------------|
| (implicit) evidence gatherer | Pass A inventory + crosswalk |
| audit1 strict | Pass B |
| audit3 contradiction hunter | Pass C |
| audit2 charitable | **Not** a separate pass — charity only after C; never skip C |
| aggregator / re-round | Pass D lock; optional re-run C only on disputed dims |
