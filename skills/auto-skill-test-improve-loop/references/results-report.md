# RESULTS report and cost rate (SoT)

Write **once** at end of the run. Path:

```text
.eft/<miss_id>/RESULTS.md
```

Print the same content as the final user message. Do not ask the human to assemble it.

## Template

```markdown
# Ecological forward-test results

## 1. Issue
- miss_id:
- human probe (verbatim or path):
- caller / callee:
- failure_label:
- root_reason: (one line: cause → missing gold)

## 2. How the agent fixed it
- layer patched: caller | callee | harness
- rank used: M0 | M1 | M2 | M3
- files changed:
- what was added/changed (≤5 bullets):
- what was deliberately not changed:
- key diff (≤20 lines) or path to PATCH.diff:

## 3. Results (observables)
| Case | Baseline | After min patch | Gold check |
|------|----------|-----------------|------------|
| ECO_POS… | FAIL/PASS + one-line | FAIL/PASS + one-line | met? |
| ECO_NEG… | … | … | met? |

## 4. Comparison (fat vs minimum)
| Metric | Baseline | Fat (if tried) | Minimum |
|--------|----------|----------------|---------|
| Ecological POS | | | |
| Files touched | 0 | | |
| Lines +/− | 0 | | |
| Callee body edited | no | | |
| Multi-debate | n/a | | |

## 5. Cost rate
| Cost | Value | Notes |
|------|-------|-------|
| Forward-test runs | N | baseline + each rank re-run |
| Ranks tried | … | |
| Patch size (files / +lines) | | min candidate |
| Fat patch size (if any) | | |
| **Size cost rate** | | see formula |
| **File cost rate** | | see formula |
| Token / model cost | n/a or sum | do not invent |
| Human stops | 0 or 1 (promote) | |

## 6. Status (hygiene)
- original_skill_path:
- worktree_skill_path: (must differ from original)
- original_project_root: (or n/a)
- project_worktree_path: (or n/a)
- isolation_method: git_worktree | full_copy
- HYGIENE.md: path
- promote: pending | done | skipped
- cleanup: pending | done | deferred
- remaining risk: (one line)
```

**Hygiene check before promote:** no loop write landed under `original_skill_path` (or live project when `project_worktree_path` was set).


## Cost rate formulas

```text
size_cost_rate = (files_min + lines_added_min) / max(1, files_fat + lines_added_fat)
file_cost_rate = files_min / max(1, files_fat)
```

If no fat trial: both rates = **1.0**, note `no_fat_trial`.  
Also count: `forward_test_runs`, `ranks_tried`, `human_stops` (target **1** = promote only).

## Rules

- Empty section = incomplete run.  
- Prefer numbers (“+1 line”) over adjectives (“small”).  
- Token costs: harness-reported only, else `n/a`.  
