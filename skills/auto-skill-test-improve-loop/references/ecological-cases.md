# Ecological cases and quarantine (hygiene)

## What “ecological” means

The case looks like **real work**: conversation already in progress, human speaks in their own words, agent has the same kinds of context the product injects (system, project rules, skill list, prior turns). Success must depend on transferable skill behavior, not on a test proctor.

## Against lab cases

| Lab (weak primary) | Ecological (primary) |
|--------------------|----------------------|
| “Use `$skill` at `/path` with this feedback” | Resume multi-turn work; human message is the probe |
| Gold answers in the prompt | Gold only in meta score sheet |
| Empty or toy cwd | Real project root / realistic files |
| Single turn always | Prefix + probe (or full multi-turn seed) |

Lab explicit invoke is allowed as a **control**: “when forced in, does the body work?” It never alone proves auto-invoke or caller discipline.

## Case record

```text
id: ECO-<n>_<short>
harness: codex | grok | claude | cursor | headless | any
setup: how context is built (resume session, plant prefix, multi-turn seed)
prefix_source: session id / file / “fresh multiturn turn1…”
probe: verbatim human text (or path to fixture)
precondition:
  skill_discoverable: yes/no/unknown
  notes: e.g. skill missing from injected list
gold_observables:
  - must load <skill>/SKILL.md (tool read), not only path string in a skill list
  - must / must not write path X
  - must emit contract field Y / ask Z
negative: true if skill must NOT run
skill_path_in_runner: <worktree skill path — never live original>
project_cwd_in_runner: <project worktree path if probes write files>
```

## Building the prefix

1. Prefer **cut a real transcript** before the miss turn.  
2. Else **seed multi-turn**: turn 1 establishes state the skill would have; turn 2 is the probe.  
3. Keep synthetic harness blocks if the product uses them (skill catalogs, project rules)—they are part of ecology.  
4. Record whether the target skill appears in whatever **discoverability surface** that harness uses (injected list, `$` menu, plugin registry).

## Gold observables (examples of good checks)

- Tool **read** of `…/SKILL.md` for the target skill (count path-in-catalog separately)  
- Order: required skill step **before** competing write (draft, commit, etc.)  
- Contract Response / required human decision words the skill already names  
- Negative: no load + no forbidden write  

Avoid gold that needs mind-reading (“agent understood friction”).

## Cross-harness mapping

| Idea | Codex-like | Grok-like | Others |
|------|------------|-----------|--------|
| Transcript SoT | rollout / session log | `chat_history.jsonl` | product session export |
| Skill discovery | available skills in context | Available Skills block | slash menu / system skills list |
| Multi-turn | resume / continue | `-r` / fork / multi `-p` | product resume |
| Fresh thread | new session id | new session id | new chat |
| FS isolation | `git worktree add` or full copy | same | copy/clone |

Method stays the same; only file paths and CLI flags change. Put harness-specific paths in the **case**, not in this skill’s core steps.

---

## Quarantine / worktree hygiene (SoT)

### Why

Fresh agent threads isolate **conversation**, not the **filesystem**. Ecological probes and patch loops write real files (skill drafts, project drafts, `learnt/`). Without quarantine, a failed loop breaks the skill or project the human still uses.

### What to isolate

| Surface | Isolate? | How |
|---------|----------|-----|
| **Skill under test** (caller and/or callee body you may patch) | **Always** | `git worktree add` of the repo that owns it, **or** full directory copy |
| **Project cwd** (when gold or probes write drafts, scores, learnt/) | **Required if probes write** | Same: worktree or copy of the project; runner cwd = that path |
| **Home global skills** (e.g. `~/.codex/skills/foo`) when **patching** them | **Required** | Copy skill dir to worktree (e.g. `.eft/<miss_id>/skills-copy/foo/`); patch the copy only |
| Home skills when only **loading/running** as callee (no patch) | Read live OK | Do not edit live home path |

### Layout

```text
original_skill_path     (live, day-to-day)     ← never write in the auto loop
original_project_root   (live project, if any) ← never write if project_worktree set

        │  git worktree add  OR  cp -R
        ▼

worktree_skill_path     ← all skill patches + skill paths in runner prompts
project_worktree_path   ← runner cwd when probes write project files (optional if no writes)

        │  human: promote
        ▼

apply PATCH.diff only → original_skill_path (and original_project only if human OK’d project edits)
```

### Create quarantine (before any baseline or patch)

1. Record **absolute** `original_skill_path` (and `original_project_root` if probes touch a project).  
2. Create sibling path, e.g.  
   - git: `git worktree add <repo>-eft-<miss_id> HEAD` (or a new branch)  
   - else: `cp -R <original> <original>-eft-<miss_id>`  
3. Set `worktree_skill_path` = skill path **inside** that tree (must be ≠ original).  
4. If probes write project files: set `project_worktree_path` ≠ `original_project_root`; runner cwd = project worktree.  
5. If root layer is **callee** under home skills: copy callee package into `.eft/<miss_id>/skills-copy/<name>/` and treat that as the only patch target; runner may still *read* live for discovery tests only if case says so — default: load from copy when testing a callee patch.  
6. Write `.eft/<miss_id>/HYGIENE.md` with all paths.

**Check:** every path you will `write`/`edit` during the loop is under a worktree or `.eft/` artifact dir — never under `original_*`.

### During forward test and patch

| Do | Do not |
|----|--------|
| Point skill path in prompts at `worktree_skill_path` | Point at live original skill |
| Use `project_worktree_path` as cwd when writing drafts | Write Discussion/`learnt/` into live project when worktree exists |
| Put scores, PATCH.diff, RESULTS under `.eft/<miss_id>/` (may live inside project worktree) | Edit live original “to save a step” |
| Bisect by resetting **worktree** skill files from original, then re-apply rank | Bisect on live |

### Promote (only after human OK)

1. Source of truth: `.eft/<miss_id>/PATCH.diff` (or listed file list + unified diff vs original).  
2. Apply **only those hunks** to `original_skill_path` (and only listed project files if human OK’d project-side promote).  
3. Do not copy entire worktree over live (avoids residue).  
4. Record `promote: done` + timestamp in RESULTS / HYGIENE.  
5. If human says skip: `promote: skipped`; leave live unchanged.

### Cleanup (after promote or skip)

1. Remove or reset the skill worktree/copy (`git worktree remove` or `rm -rf` the copy).  
2. Remove project worktree if created solely for this miss (keep if human still needs it — note in HYGIENE).  
3. Keep `.eft/<miss_id>/` artifacts (RESULTS, scores, PATCH.diff) unless human asks to delete.  
4. Record `cleanup: done | deferred` in HYGIENE.md.

### HYGIENE.md template

```text
miss_id:
original_skill_path:
worktree_skill_path:
original_project_root: (or n/a)
project_worktree_path: (or n/a)
home_callee_copy: (path or n/a)
isolation_method: git_worktree | full_copy
created_at:
promote: pending | done | skipped
cleanup: pending | done | deferred
verify: worktree_skill_path != original_skill_path  (required true)
```

### Failure modes

| Failure | Fix |
|---------|-----|
| Patched live original mid-loop | Stop; restore from git/backup; re-quarantine; treat as process fail |
| Runner used live skill path | Re-run cases with worktree path only |
| Project pollution on live | Prefer restore live from VCS; re-run with project_worktree |
| Left worktrees forever | Cleanup step after promote/skip |
