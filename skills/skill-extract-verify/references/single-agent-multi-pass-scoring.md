# Single-agent multi-pass scoring (distilled from multi-debate)

Use this **inside** `$skill-extract-verify` when scoring rubrics (especially **C4b**).  
It replaces the need to spawn three reviewers for routine extract audits, by forcing the **same evidence moves** multi-debate used when it beat a solo extract-verify score.

## What multi-debate caught that solo extract-verify missed

| Episode (persist-rubrics-context) | Solo extract-verify | Multi-debate |
|-----------------------------------|---------------------|--------------|
| Call contract v3 after lean API | C4b **pass**; D2≈5 | D2 **fail/3**; hard gate 4 fail |
| Decisive evidence | Read contract + intent seed rule | **Cross-walked storage REQUIRED keys** (validator / templates) vs **named fill paths** in contract |
| Outcome | False confidence | Forced v4 fill-path inventory → later all D=5 |

### Root reasons (not “need three models”)

1. **Author–auditor collapse** — Same run refined the contract and scored it. Solo scoring optimized for “lean Request” and under-applied hard gate 4 against **disk schema**.  
2. **Incomplete evidence plan** — Gather listed “contract fields,” not “every attribute storage will refuse without.”  
3. **No mandatory counterevidence** — Dimensions got supporting quotes only; no forced “what would make this a 3?”  
4. **Happy-path sufficiency** — Minimal Request works → D2 treated as 5, while anchor 3 is exactly “happy path works; mandatory stored attrs lack fill path.”  
5. **Single stance** — No separate **inventory**, **strict floor**, and **contradiction** passes; one blended charitable read.  
6. **No re-score loop** — No second pass only on weak/high scores after adversary notes.

Multi-agent helped because of **role separation + schema cross-walk + counterevidence**, not because three chat windows are magic.

---

## Single-agent procedure (do in order)

Complete these **three passes** before locking C4b (and use Pass B/C on any other criterion you scored 5 after editing the extract yourself).

### Pass A — Inventory (neutral clerk)

Goal: facts only, no scores yet.

1. List **Request** fields (class, required/default).  
2. List **standard Response** keys.  
3. Build **storage mandatory set** from extract sources (whichever exist):
   - validators (`REQUIRED_*` keys, non-empty list checks)
   - memory/protocol templates
   - persistence hard gates / entry templates  
4. Build **fill-path crosswalk** (required for write engines):

| Stored attribute | Required by (file:line or rule) | Named source in call contract? (required/seed/inference/ask/fail) | Gap? |
|------------------|----------------------------------|-------------------------------------------------------------------|------|
| … | … | yes: … / **NO** | y/n |

5. Note dual fields, aliases, mode fail-closed rules, profile/`include` rules.

*Done when:* every storage-required attribute is a crosswalk row; every Request field is inventoried.  
**If any Gap=y → hard gate 4 cannot pass** until fixed or scored fail.

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

1. Storage key missing from fill-path table  
2. “Inference” claimed but not **named** as source for that attribute  
3. Happy path conflated with D2=5  
4. Dual fields / aliases without winner + retirement  
5. Dead inputs (accepted then ignored)  
6. Session goal → durable field without generalization rule  
7. Standard Response audit-echo stack  
8. Mode matrix vs minimal-call story  
9. Request dump of file schema (layering) or host FSM required enums  
10. You authored the contract this session → **mandatory** Pass C; never lock all-5s without it  

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

### Pass A — Fill-path crosswalk
| Stored attribute | Required by | Contract source | Gap? |
| ... | ... | ... | y/n |

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

Use `$review-with-multi-debate` (true parallel reviewers) when:

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
