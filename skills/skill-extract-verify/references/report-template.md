# Skill Extract Verify Report

- **Host**:
- **Extracted**:
- **Capability**:
- **Overall**: pass | fail | insufficient_evidence
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
- Verdict:
- Evidence:
- Fix:

### C4b — Field API design (blocking hard gates if imported)
- Multi-pass A–D complete: y/n (see `single-agent-multi-pass-scoring.md`)
- Pass A fill-path crosswalk (gaps):
- Pass B strict D1–D7 + gates:
- Pass C attacks (held / lowered):
- Lock D1–D7:
- Hard gates 1–8:
- Verdict:
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
- Verdict:
- Evidence:
- Fix:

## Call map

| From | To | Mechanism | Notes |
|------|-----|-----------|-------|
| host | extracted | subagent / $name / none | |

## Dual-path risks

-

## Top fixes

1.
