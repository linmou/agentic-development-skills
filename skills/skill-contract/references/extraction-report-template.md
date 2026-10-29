# Skill Contract — Extraction Report

Used in `extract` mode before the contract is built. C4b is recorded in `report-template.md`.

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
- Recorded in the contract report (`report-template.md` § C4b):
- Verdict: pass | fail | insufficient_evidence | n/a

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
