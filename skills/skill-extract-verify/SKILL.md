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

Optional: `capability` (one line); `out_dir` (default `./.skill-extract-verify/`)

## Steps

1. **Load rubrics** — Read `references/criteria.md`. Read:
   - always: `references/extraction-split-rubric.md` (C1–C3, C4a, C5–C6)
   - if call contract: `references/call-contract-field-rubric.md` (C4b) **and** `references/single-agent-multi-pass-scoring.md`  
   *Done when:* C1–C6 known; if contract, multi-pass A–D known. Do not invent principles.

2. **Gather evidence** — Read both `SKILL.md` files and progressive-disclosure targets. List both trees. Grep: host name in extract; shared protocol/scripts; `$extracted` / subagent; host tokens on callee.  
   For **C4b / write engines**, also open validators, memory templates, and persistence hard gates — not only the call-contract file.  
   *Done when:* every criterion has a path/grep hit or “not found”; storage sources located if extract writes files.

3. **Score topology (C1–C3, C4a, C5–C6)** — Apply `extraction-split-rubric.md`.  
   *Done when:* those criteria have scores, hard gates, evidence, verdicts.

4. **Score C4b with multi-pass (if contract)** — Follow `single-agent-multi-pass-scoring.md` **in order**:
   - **Pass A** — Request inventory + **storage↔contract fill-path crosswalk** (Gap=y ⇒ gate 4 fail)
   - **Pass B** — Strict D1–D7 + hard gates; each Di needs evidence **and** a counterevidence attempt
   - **Pass C** — Contradiction hunt (mandatory if you authored the contract this session or any Di=5)
   - **Pass D** — Lock scores; do not re-raise after C without new artifact text  
   Then apply C4b decision policy.  
   *Done when:* multi-pass output block complete; no all-5s without Pass C log.

5. **Report** — Write `out_dir/skill_extract_verify_report.md` from `references/report-template.md` (include C4b multi-pass block). Chat summary: overall, blocking fails, top 3 fixes.  
   *Done when:* report exists; overall `pass` only if every **blocking** criterion is `pass`.

## Progressive disclosure

| File | Role |
|------|------|
| `references/criteria.md` | Index + short definitions |
| `references/extraction-split-rubric.md` | C1–C3, C4a, C5–C6 |
| `references/call-contract-field-rubric.md` | C4b D1–D7 anchors + hard gates |
| `references/single-agent-multi-pass-scoring.md` | **How** to score (inventory → strict → attack → lock) |
| `references/report-template.md` | Report skeleton |
