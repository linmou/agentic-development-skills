---
name: auto-skill-test-improve-loop
description: >
  Auto skill test-improve loop — after a real multi-turn skill miss, quarantine
  dependencies, causally diagnose the failure, test a minimum worktree fix, and
  emit RESULTS with matched-environment comparison and cost rate.
---

# Auto Skill Test-Improve Loop

**Leading words:** *ecological case*, *forward test*, *minimum addition*, *RESULTS*, *quarantine*.

Determine whether a real miss warrants a skill edit, prove the **minimum skill fix** when it does, then show RESULTS. Default: run **1→10 without narrative stops**. Human only at **start** (miss) and **promote** (live copy). Redesign only if M3 is required.

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

### 3.5. Dependency closure and environment revision

Before any forward runner or timing, inspect the execution path selected by each case. Recursively resolve every explicitly required peer skill, script, reference, asset, tool, harness capability, and project input to the exact path or interface the runner will use. Record ownership, quarantine/read-only status, a Git revision for clean tracked resources or a content hash when no Git identity exists, and a no-write readiness check in `.eft/<miss_id>/DEPENDENCIES.json`. Replace placeholders such as `<skill-dir>` with one verified absolute path.

Freeze the controlled runnable state as environment revision `E0` in `.eft/<miss_id>/ENVIRONMENT.md`. The revision includes the dependency manifest, harness/model configuration, tool versions, and input identities that can affect behavior or timing. Record the baseline or candidate target-skill identity separately as the experimental treatment; changing only that designated treatment does not change the environment revision. Do not start a forward run when a declared dependency is unresolved, missing, incompatible, mutable without an identity check, or not callable through its required interface.

Static inspection need not predict every dynamic dependency. If a run reveals a new dependency or environment condition, preserve that run as discovery evidence, add the observation and any reproducible repair to a new environment revision, repeat this gate, and use a fresh runner. Never silently repair a running environment or compare behavior or speed across unmatched revisions.

**Done when:** `DEPENDENCIES.json` resolves the declared executable closure, all readiness checks pass without changing the tested artifact, and `ENVIRONMENT.md` records the frozen revision used by the next run.
Detail: `references/ecological-cases.md` § Dependency closure and environment revisions.

### 4. Baseline forward test

Delegate each case to a fresh forward-test subagent; use the same rule for every Step 8 re-run. If a case requires that subagent to spawn further subagents but its model cannot, stop and ask the user to choose the subagent model. The runner must **not** know it is a test; give it the raw probe + prefix only; skill paths = **worktree** paths; cwd = **project_worktree_path** when set. Record pass/fail + artifacts + usage if reported.

Record the frozen environment revision and tested target-skill identity with every score. Measure readiness/setup and recovery separately from the forward-run interval. A behavioral or timing comparison is valid only when the compared runs use the same environment revision and differ only in declared treatments.

**Done when:** every case has a score file under `.eft/<miss_id>/` with its environment revision, tested target-skill identity, and timing boundaries.

### 5. Failure label

For each fail: label + one-line what happened. Repeated skill phrases + daily words only.

**Done when:** `FAILURES.md` (or scores) cover every fail; no invented jargon.  
Detail: `references/failure-labels.md`.

### 6. Causal diagnosis

Invoke `$competing-explanations-causal-research` through its versioned Request/Response contract. Freeze the exact failed outcome, assign evidence roles and timing, generate rival causal models, test them symmetrically, and make a bounded ruling about what most likely produced the missing gold. Do not constrain the potential explanations, mechanisms, relationships, or correction targets to a predefined list or ontology. Treat prior labels and suspected causes only as evidence seeds.

Persist the response and the loop's evidence-grounded interpretation in `ROOT.md`. Do not select a patch target while the diagnosis says that more discriminating evidence is needed or does not support changing the skill. Any selected write target must remain under quarantine.

**Done when:** `ROOT.md` records the frozen outcome, evidence roles, rival models, bounded ruling, material uncertainty, next discriminating evidence, and the reason for the next action and any patch target.
Detail: `references/root-reason.md` § Open-world causal diagnosis.

### 7. Minimum addition ladder

When the diagnosis supports a skill edit, write M0→M3 one line each (scale SoT in `references/root-reason.md`). Default start **M0**. No human rank pick. If the diagnosis supports no skill edit, record the evidence-supported no-patch conclusion instead of inventing a ladder.

**Done when:** `LADDER.md` lists M0–M3 and first rank to try = M0 (or next untried), or `ROOT.md` explicitly justifies `rank: n/a; skill patch: none`.

### 8. Patch loop

Run this patch loop only while the current diagnosis supports a skill edit. An evidence-supported no-patch result may instead require more discriminating evidence or a reproducible environment revision; do not manufacture a skill change to complete the loop.

1. Apply **only** the current rank under `worktree_skill_path` (or home skills-copy). **Refuse** writes under `original_skill_path` / `original_project_root`.  
2. Re-run Step 3.5 after each patch, then re-run the **same** ecological cases in fresh threads with quarantine paths and a frozen environment revision.
3. Write score files + optional tokens under `.eft/<miss_id>/`.  
4. After every failed rerun, invoke `$competing-explanations-causal-research` again with the new trace, score, dependency observations, environment revision, patch diff, and prior diagnosis as evidence seeds. Save the updated diagnosis before deciding what to do next. Do not automatically escalate the patch rank or force the result through a fixed branching rule; use the new evidence and bounded ruling to choose the next action intelligently.
5. Pass gold on all POS and NEG still pass → stop climbing (no “consistency” files).  
6. If a fatter patch was applied first → auto-bisect **down** on the worktree (reset from original → M0 → …; keep smallest pass).  
7. M3 / redesign → stop and ask human.

When a run reveals an environment dependency or repair, preserve it as a discovery run rather than silently converting it into patch evidence. Create a new environment revision and rerun whatever comparisons the causal claim requires under matched conditions. Report setup/recovery cost separately from steady-state forward time.

**Done when:** either (a) the final diagnosis supports the retained minimum patch, `PATCH.diff` exists under `.eft/<miss_id>/` (diff vs **original**), POS gold is true, and NEG still passes; or (b) the final diagnosis supports no skill patch and RESULTS records the observed outcome, remaining issue, and next evidence or action with `PATCH.diff: n/a`. In both cases, causal comparisons use matched environment revisions and live originals remain byte-identical to pre-loop except permitted `.eft` artifacts.

### 9. Multi-debate (deterministic)

```text
if no skill patch → debate: skipped
else if single-file patch and ≤5 lines added and POS pass → debate: skipped
else if fat patch was applied this run → run $review-with-multi-debate on
  "this patch is minimum sufficient for the gold flip"
  fail → strip / lower rank → step 8
else → debate: skipped
```

**Done when:** `DEBATE.md` or audit summary records pass | fail | skipped.

### 10. RESULTS + promote + cleanup

1. Write `.eft/<miss_id>/RESULTS.md` and **print it as the final user answer**. Template + cost: `references/results-report.md`.  
2. Status must include hygiene paths and `promote: pending` when a patch exists, otherwise `promote: n/a`.
3. **On human “promote” only, when a patch exists:** apply `PATCH.diff` hunks to `original_skill_path` (not full tree copy); set promote done; then **cleanup** worktree/copy per `references/ecological-cases.md` § Cleanup.
4. **On human “skip”:** leave live unchanged; cleanup or defer; record in HYGIENE.
5. **When no patch exists:** set promote n/a and cleanup or defer after RESULTS; no promotion decision is needed.

**Done when:** RESULTS sections 1–6 complete; before promote, live original skill files unchanged by this loop.

## Hard gates

| Gate | Do |
|------|-----|
| Evidence | Score **ecological** cases as primary |
| Forward integrity | Raw probe only in runner; gold stays in score sheet |
| **Quarantine first** | No baseline/patch until `HYGIENE.md` and `worktree_skill_path != original_skill_path` |
| **Write fence** | All skill/project edits under worktree or `.eft/…/skills-copy/` only |
| **Dependency closure** | Resolve, identity-pin, and readiness-check the declared executable closure before every measured forward run |
| **Environment identity** | Preserve discoveries; never silently repair a run or compare unmatched environment revisions |
| **Causal diagnosis** | Use `$competing-explanations-causal-research`; do not restrict possible explanations to predefined layers |
| **Re-diagnose failures** | Reopen causal diagnosis after every failed Step 8 rerun before choosing the next action |
| Minimum first | Start with the lowest justified rank; retain only the smallest evidence-supported pass |
| Run complete | RESULTS.md filled; no “done” on chat summary alone |
| Promote | If a patch exists, change the live original only after human OK and apply **PATCH.diff only**; otherwise record n/a |
| Cleanup | After promote or skip: remove/reset worktree (or record deferred) |

## Progressive disclosure

- `references/ecological-cases.md` — cases + **quarantine / dependency closure / environment revisions / promote / cleanup**
- `references/failure-labels.md` — labels  
- `references/root-reason.md` — open-world causal diagnosis, re-diagnosis, ladder, edition
- `references/results-report.md` — RESULTS + matched-environment comparison + cost rate
