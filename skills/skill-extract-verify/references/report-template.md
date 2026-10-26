# Skill Extract Verify Report

- **Host**:
- **Extracted**:
- **Capability**:
- **Import path**: yes | no (no ⇒ C4a/C4b `n/a`)
- **Overall**: pass | fail | insufficient_evidence (rule: `criteria.md`)
- **Blocking fails**:

## Criteria

### C1 — Capability, not lifecycle (blocking)
- Scores (identity / orchestration / residue):
- Hard gates:
- Verdict:
- Evidence:
- Fix:

### C2 — One-way dependency (blocking)
- Scores:
- Hard gates:
- Verdict:
- Evidence:
- Fix:

### C3 — Single writer, thin client (blocking)
- Scores:
- Hard gates:
- Verdict:
- Evidence:
- Fix:

### C4a — Contract exists + opaque labels (blocking if imported)
- Scores (existence / schema ownership / opaque labels / third-party):
- Hard gates:
- Verdict: pass | fail | insufficient_evidence | n/a
- Evidence:
- Fix:

### C4b — Field API design (blocking if imported)
Contract path:

**Pass A — Inventory**

Request inventory:

| Field | Class | Required/default | Overlaps? | Precedence | Keep/merge/drop |
|-------|-------|------------------|-----------|------------|-----------------|

Standard Response keys:

Output-construction crosswalk:

| Output artifact | Mandatory condition/profile | Inputs/capabilities | Resolver/path | Validation | Failure condition | Gap? |
|-----------------|-----------------------------|---------------------|---------------|------------|-------------------|------|

Implementation crosswalk:

| Internal artifact | Producer | Dependencies/capabilities | Construction path | Validation | Failure behavior | Gap? |
|-------------------|----------|---------------------------|-------------------|------------|------------------|------|

Conditional persistence crosswalk: n/a | complete | gaps listed

| Stored attribute | Population rule | Validation | In public Request? | Gap? |
|------------------|-----------------|------------|--------------------|------|

Failure-policy evidence (bounded / reachable / capability-consistent trigger; constructible validated failure artifact; normal path present):

**Pass B — Strict scores**
- D1–D7 (evidence + counterevidence per Di):
- Hard gates 1–8:

**Pass C — Attacks**
1. … → held | lowered Di to N

**Pass D — Lock**
- Scores: D1= D2= D3= D4= D5= D6= D7=
- Hard gates 1–8:
- Verdict: pass | fail | insufficient_evidence | n/a
- Smells:
- Fix:

### C5 — Standalone trigger (blocking)
- Scores:
- Hard gates:
- Verdict:
- Evidence:
- Fix:

### C6 — Completeness (non-blocking)
- Checklist / scores:
- Verdict: pass | warn
- Evidence:
- Fix:

## Call map

| From | To | Mechanism | Notes |
|------|-----|-----------|-------|
| host | extracted | subagent / skill name / none | |

## Dual-path risks

-

## Top fixes

1.
