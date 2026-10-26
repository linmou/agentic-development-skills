---
name: skill-extract-verify
description: >
  Audit a skill extraction (host vs extracted skill) for one-way dependency,
  dual writers, and call-contract fitness. Use after extracting a skill, before
  extracting, or when asked if an extract is safe / coupled / over-wide.
---

# Skill Extract Verify

Diagnose whether a **host → extracted** split is a real independent skill.  
Do **not** rewrite either skill unless the user asks after the report.

## Inputs

Required (ask once, then stop only if still missing):

1. `host_skill` — folder with host `SKILL.md`
2. `extracted_skill` — folder with extracted `SKILL.md`

Optional: `capability` (one line); `out_dir` (default `./.skill-extract-verify/`; a local report folder, never commit it)

## Steps

1. **Load base rubrics** — Read `references/criteria.md` and `references/extraction-split-rubric.md`.  
   *Done when:* C1–C6 and the overall verdict rule are known. Do not invent principles.

2. **Gather evidence** — Read both `SKILL.md` files and progressive-disclosure targets. List both trees. Grep: host name in extract; shared protocol/scripts; how the extract is invoked / subagent; host tokens on callee.  
   Decide **import path: yes/no** (host calls the extract through a Request/Response, subagent, or skill name). If yes, also open output schemas, capability declarations, resolvers, validators, and sources for required internal artifacts; if the extract persists artifacts, inspect storage templates and persistence gates as a subordinate check.  
   *Done when:* every criterion has a path/grep hit or “not found”; import path is yes/no; if yes, construction sources are located and persistence is marked applicable or n/a.

3. **Score topology (C1–C3, C4a, C5–C6)** — Apply `extraction-split-rubric.md`. If import path = no, C4a and C4b are `n/a`; skip step 4.  
   *Done when:* those criteria have scores, hard gates, evidence, verdicts.

4. **Score C4b with multi-pass (import path = yes)** — Read `references/call-contract-field-rubric.md` and `references/single-agent-multi-pass-scoring.md`, then follow the passes **in order**:
   - **Pass A** — Request inventory + **output-construction crosswalk** + **implementation crosswalk** for required internal artifacts (any Gap=y ⇒ gate 4 fail); add a conditional persistence crosswalk when applicable
   - **Pass B** — Strict D1–D7 + hard gates; each Di needs evidence **and** a counterevidence attempt
   - **Pass C** — Contradiction hunt (mandatory if you authored the contract this session or any Di=5)
   - **Pass D** — Lock scores; do not re-raise after C without new artifact text  
   Then apply C4b decision policy.  
   *Done when:* output, implementation, and applicable persistence crosswalks are complete; no all-5s without Pass C log.

5. **Report** — Write `out_dir/skill_extract_verify_report.md` from `references/report-template.md`. Set overall with the rule in `criteria.md`. Chat summary: overall, blocking fails, top 3 fixes.  
   *Done when:* report exists and every section of the template is filled or marked `n/a`.

## Progressive disclosure

| File | Role |
|------|------|
| `references/criteria.md` | Index, short definitions, overall verdict rule |
| `references/extraction-split-rubric.md` | C1–C3, C4a, C5–C6 |
| `references/call-contract-field-rubric.md` | C4b D1–D7 anchors + hard gates |
| `references/single-agent-multi-pass-scoring.md` | **How** to score C4b (inventory → strict → attack → lock) |
| `references/report-template.md` | Report format (single output template) |
| `tests/fixtures/storage-regression/` | Known-answer pair for gate 4 persistence; re-run after rubric edits |
