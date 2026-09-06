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
- causal_ruling: (bounded explanation of cause → missing gold)
- material uncertainty / next discriminating evidence:
- dependency manifest, comparison environment revision, and tested skill variants:

## 2. How the agent responded
- selected intervention and why the diagnosis supports it:
- rank used: M0 | M1 | M2 | M3 | n/a (no skill patch)
- files changed:
- what was added/changed (≤5 bullets):
- what was deliberately not changed:
- key diff (≤20 lines) or path to PATCH.diff:

## 3. Results (observables)
| Case | Environment revision | Baseline variant/result | Candidate variant/result | Gold check |
|------|----------------------|-------------------------|--------------------------|------------|
| ECO_POS… | E… | id + FAIL/PASS + one-line | id/n/a + FAIL/PASS + one-line | met? |
| ECO_NEG… | E… | … | … | met? |

- dynamic dependencies discovered:
- environment changes and reproducible repairs:
- unmatched runs excluded from causal comparison:

## 4. Comparison (fat vs minimum; n/a when no skill patch was justified)
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
| Readiness/setup time | | outside forward interval |
| Environment discovery/recovery time | | preserve separately |
| Matched forward time | | baseline and candidate under same revision |

## 6. Status (hygiene)
- original_skill_path:
- worktree_skill_path: (must differ from original)
- original_project_root: (or n/a)
- project_worktree_path: (or n/a)
- isolation_method: git_worktree | full_copy
- HYGIENE.md: path
- DEPENDENCIES.json: path
- ENVIRONMENT.md and comparison revision:
- promote: pending | done | skipped | n/a
- cleanup: pending | done | deferred
- remaining risk: (one line)
```

**Hygiene check before promote:** no loop write landed under `original_skill_path` (or live project when `project_worktree_path` was set).


## Cost rate formulas

```text
size_cost_rate = (files_min + lines_added_min) / max(1, files_fat + lines_added_fat)
file_cost_rate = files_min / max(1, files_fat)
```

If no skill patch was justified: both rates = `n/a`. If a minimum patch exists but no fat trial ran: both rates = **1.0**, note `no_fat_trial`.
Also count: `forward_test_runs`, `ranks_tried`, `human_stops` (target **1** = promote only).

## Rules

- Empty section = incomplete run.  
- Prefer numbers (“+1 line”) over adjectives (“small”).  
- Token costs: harness-reported only, else `n/a`.  
- Do not claim a skill-caused behavior or speed difference from unmatched environment revisions or undeclared treatment differences.
- Preserve setup, dependency discovery, and recovery costs even when the steady-state forward clock starts afterward.
