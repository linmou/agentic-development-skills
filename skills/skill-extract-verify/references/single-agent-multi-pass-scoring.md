# Single-agent multi-pass scoring (C4b)

Intent: one auditor gets the benefits of a multi-reviewer debate (role separation, output crosswalk, forced counterevidence) without spawning reviewers. A one-shot charitable read tends to equate "minimal Request works" with sufficiency and miss unconstructible outputs, especially when the auditor also wrote the contract.

Fill results into the C4b section of `report-template.md`; table columns are defined there.

---

## Procedure (do in order)

Complete these **four passes** before locking C4b (and use Pass B/C on any other criterion you scored 5 after editing the extract yourself).

### Pass A — Inventory (neutral clerk)

Goal: facts only, no scores yet.

1. List **Request** fields (class, required/default).  
2. List **standard Response** keys.  
3. Build the **mandatory output set** from the contract and declared profiles, including status/error artifacts:
   - output schemas and profile rules
   - capability declarations and internal resolvers
   - validators and failure rules  
4. Build the **output-construction crosswalk**: one row per mandatory output artifact.
5. Build a separate **implementation crosswalk** for every required internal artifact needed to construct or validate a mandatory output, even when it is neither public nor persisted.
6. If persistence applies, add the subordinate **persistence crosswalk** for mandatory stored attributes and their internal population/validation rules. Do not require storage fields in the public contract solely because they are persisted.
7. Note dual fields, aliases, mode fail-closed rules, profile/`include` rules, and undocumented assumptions. For each explicit failure condition, record the bounded trigger, why it is reachable from declared inputs/capabilities, why it is capability-consistent, and how the failure Response/artifact is constructed and validated. A failure-only or generic catch-all path is not sufficient; the normal construction path must also be present.

*Done when:* every mandatory output and required internal artifact is a crosswalk row; every Request field is inventoried; persistence is marked applicable or n/a; every explicit failure condition has the required evidence.  
**If any output or implementation Gap=y, or a persistence gap exists when applicable, hard gate 4 cannot pass** until fixed or scored fail.

### Constructibility regression matrix

| Case | Persistence | Expected result |
|------|-------------|-----------------|
| Declared input and capability construct a non-persistent output | n/a | Gate 4 passes; no storage crosswalk required |
| Internal storage field absent from the public Request is populated by a documented resolver and validated | applicable | C4b passes, D2 ≥ 4, persistence check passes; field stays out of the public Request |
| Required output depends on an unavailable or undeclared capability | either | Gate 4 fails |
| Resolver path or assumption is undocumented/invalid | either | Gate 4 fails |
| Meaningful bounded failure condition exists and normal path remains constructible | either | Gate 4 may pass |
| Generic catch-all failure is the only path | either | Gate 4 fails |
| Same field and public contract, but no valid internal population rule | applicable | Persistence check fails; C4b and D2 fail; do not repair by adding the field to the Request |

Rows 2 and 7 have a known-answer fixture: `tests/fixtures/storage-regression/`.

### Pass B — Strict floors (reject unsupported excellence)

Goal: apply anchors and hard gates **pessimistically**.

1. Score D1–D7 with anchors; **start from 4 max** unless anchor-5 language is **explicitly** satisfied in the contract text.  
2. Mark each hard gate pass/fail with one evidence cite.  
3. For any Di you want ≥4, write **one counterevidence attempt** (even if weak).  
4. If counterevidence is unanswered by contract text → lower score or fail the related gate.

*Done when:* scores + gates filled; every Di has ≥1 evidence and ≥1 counterevidence attempt (or “none found after X checks”).

### Pass C — Contradiction hunt (disconfirm)

Goal: try to **break** Pass B, especially scores of 5 and gates marked pass.

Attack checklist:

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
2. C4b verdict per decision policy in `call-contract-field-rubric.md`.  
3. If any Di was revised in Pass C, do **not** re-raise it in the same turn without new contract text.

---

## When to still use full multi-debate

Use `review-with-multi-debate` (true parallel reviewers) when:

- C4b is blocking and Pass C leaves **unresolved** tension (you can argue both ways at ≥0.8 confidence)
- User demands independent audits on disk
- You both authored and must certify “all dimensions = 5”

Otherwise this single-agent multi-pass is the default inside extract-verify.
