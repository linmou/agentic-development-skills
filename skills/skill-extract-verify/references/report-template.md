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
- Pass A output-construction crosswalk (gaps):
- Agent-interface output evidence (declared outputs -> inputs/capabilities/resolution):
- Agent-implementation evidence (internal artifacts -> producer/dependencies/validation):
- Failure-policy evidence (bounded/reachable/capability-consistent trigger -> constructible validated failure artifact):
- Conditional persistence crosswalk (n/a when non-persistent):
- Storage regression pair (hidden field + valid resolver: C4b/D2/persistence; no resolver: C4b/D2/persistence):
- Pass B strict D1–D7 + gates:
- Pass C attacks (held / lowered):
- Lock D1–D7:
- Hard gates 1–8 (including Output Constructibility):
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
| host | extracted | subagent / skill name / none | |

## Dual-path risks

-

## Top fixes

1.
