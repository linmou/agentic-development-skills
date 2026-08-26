---
name: auto-skill-test-improve-loop
description: >
  Auto skill test-improve loop — after a real multi-turn skill miss, auto-bisect a
  minimum worktree fix and emit RESULTS (fix, comparison, cost rate).
disable-model-invocation: true
---

# Auto Skill Test-Improve Loop

**Leading words:** *ecological case*, *forward test*, *minimum addition*, *RESULTS*, *quarantine*.

Turn a real miss into a **proven minimum skill fix**, then show RESULTS. Default: run **1→10 without narrative stops**. Human only at **start** (miss) and **promote** (live copy). Redesign only if M3 is required.

**Quarantine (required):** isolate skill (and project if probes write) in a worktree or full copy **before** any baseline or patch. Live originals are read-only until human promote. SoT: `references/ecological-cases.md` § Quarantine.

**Edition:** only *minimum addition* that flips gold observables. Ladder SoT: `references/root-reason.md`.

## Steps

### 1. Capture the miss

Store under `.eft/<miss_id>/`: verbatim probe, prefix source, callee path, caller path if split.

**Done when:** `MISS.md` lists miss_id, probe path, callee, caller, **original_skill_path** (absolute), **original_project_root** (or n/a).

### 2. Quarantine (worktree hygiene)

**Before any forward test or edit:**

1. Create isolation of the skill under test: `git worktree add` **or** full copy → `worktree_skill_path`.  
2. If probes/gold write project files (drafts, scores, learnt/): isolate project → `project_worktree_path` as runner cwd.  
3. If the patch target is a **home** skill (`~/.codex/skills/…` or `$CODEX_HOME/…`): copy that package under `.eft/<miss_id>/skills-copy/` and patch **only** the copy.  
4. Write `.eft/<miss_id>/HYGIENE.md` (template in `references/ecological-cases.md`).

**Done when:** `HYGIENE.md` exists and `worktree_skill_path != original_skill_path` (verify true). No tool write has targeted `original_*` paths.

### 3. Build ecological cases

≥1 positive + ≥1 negative. Session-like probe (verbatim); gold = **observables** only; no gold leakage into runner prompts. Fields: `id`, `setup`, `probe`, `gold`, `precondition`, `harness`, **skill_path_in_runner** = worktree skill, **project_cwd_in_runner** if set.

**Done when:** case files under `.eft/<miss_id>/cases/`; POS and NEG present; paths point at quarantine.  
Detail: `references/ecological-cases.md`.

### 4. Baseline forward test

Fresh agent thread per case; runner must **not** know it is a test; raw probe + prefix only; skill paths = **worktree** paths; cwd = **project_worktree_path** when set. Record pass/fail + artifacts + usage if reported.

**Done when:** every case has a score file under `.eft/<miss_id>/`.

### 5. Failure label

For each fail: label + one-line what happened. Repeated skill phrases + daily words only.

**Done when:** `FAILURES.md` (or scores) cover every fail; no invented jargon.  
Detail: `references/failure-labels.md`.

### 6. Root reason

One primary layer: harness | caller | callee | goal conflict | false done. Cause → missing gold. File to patch first (**under worktree only**).

**Done when:** `ROOT.md` states primary layer, one-line root reason, target path(s) under quarantine.  
Detail: `references/root-reason.md` § Layer checklist.

### 7. Minimum addition ladder

Write M0→M3 one line each (scale SoT in `references/root-reason.md`). Default start **M0**. No human rank pick.

**Done when:** `LADDER.md` lists M0–M3 and first rank to try = M0 (or next untried).

### 8. Patch loop

1. Apply **only** the current rank under `worktree_skill_path` (or home skills-copy). **Refuse** writes under `original_skill_path` / `original_project_root`.  
2. Re-run the **same** ecological cases (fresh threads; quarantine paths).  
3. Write score files + optional tokens under `.eft/<miss_id>/`.  
4. Fail gold → escalate one rank; re-apply from 8.1.  
5. Pass gold on all POS and NEG still pass → stop climbing (no “consistency” files).  
6. If a fatter patch was applied first → auto-bisect **down** on the worktree (reset from original → M0 → …; keep smallest pass).  
7. M3 / redesign → stop and ask human.

**Done when:** smallest passing rank recorded; `PATCH.diff` under `.eft/<miss_id>/` (diff vs **original**); POS gold true; NEG still pass; live originals still byte-identical to pre-loop (except `.eft` artifacts if stored outside).

### 9. Multi-debate (deterministic)

```text
if single-file patch and ≤5 lines added and POS pass → debate: skipped
else if fat patch was applied this run → run $review-with-multi-debate on
  "this patch is minimum sufficient for the gold flip"
  fail → strip / lower rank → step 8
else → debate: skipped
```

**Done when:** `DEBATE.md` or audit summary records pass | fail | skipped.

### 10. RESULTS + promote + cleanup

1. Write `.eft/<miss_id>/RESULTS.md` and **print it as the final user answer**. Template + cost: `references/results-report.md`.  
2. Status must include hygiene paths and `promote: pending`.  
3. **On human “promote” only:** apply `PATCH.diff` hunks to `original_skill_path` (not full tree copy); set promote done; then **cleanup** worktree/copy per `references/ecological-cases.md` § Cleanup.  
4. **On human “skip”:** leave live unchanged; cleanup or defer; record in HYGIENE.

**Done when:** RESULTS sections 1–6 complete; before promote, live original skill files unchanged by this loop.

## Hard gates

| Gate | Do |
|------|-----|
| Evidence | Score **ecological** cases as primary |
| Forward integrity | Raw probe only in runner; gold stays in score sheet |
| **Quarantine first** | No baseline/patch until `HYGIENE.md` and `worktree_skill_path != original_skill_path` |
| **Write fence** | All skill/project edits under worktree or `.eft/…/skills-copy/` only |
| Minimum first | Lowest untried rank only; escalate on ecological fail |
| Run complete | RESULTS.md filled; no “done” on chat summary alone |
| Promote | Live original only after human OK; apply **PATCH.diff only** |
| Cleanup | After promote or skip: remove/reset worktree (or record deferred) |

## Progressive disclosure

- `references/ecological-cases.md` — cases + **quarantine / promote / cleanup**  
- `references/failure-labels.md` — labels  
- `references/root-reason.md` — layers, ladder, edition  
- `references/results-report.md` — RESULTS + cost rate  
