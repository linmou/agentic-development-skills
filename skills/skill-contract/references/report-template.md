# Skill Contract Report

- **Mode**: build | verify | impact | extract
- **Callee(s)**:
- **Skill roots scanned**:
- **Contract version** (current → proposed):
- **Verdict**: pass | fail | insufficient_evidence (rule: `SKILL.md` § Verdict)
- **Blocking findings**:
- **Extraction report**: path | n/a

## Contract (build)

- `contract.json` path:
- Prose contract path:
- Agreement with prose (fields, statuses, writes, conditional rules left to prose):
- `high_stakes`: true | false — reason:

### C4b — Field API design

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

## Mechanical check

- Command:
- Output file:
- Verdict:

| Severity | Skill | Code | Message | Disposition |
|----------|-------|------|---------|-------------|

## Callers

| Caller | Declared range | Examples | V1 | V2 | V3 | V4 | V5 | V6 | V7 | Verdict |
|--------|----------------|----------|----|----|----|----|----|----|----|---------|

For each caller:

### <caller>
- V1–V6 evidence (path + quote) and the counterexample looked for:
- V7 notes:
- Fix:

## Impact (impact mode)

| Caller | Breaks? | Reason | Smallest fix |
|--------|---------|--------|--------------|

- Version bump required: none | MINOR | MAJOR — reason:

## Trace check (optional)

- Status: run | suggested, not run | n/a (not high_stakes)
- Sessions read (folders, count):
- Calls: matched / stale / reconstructed:
- Unsourced fields:
- Mishandled statuses:
- New fixtures or examples added:

## Top fixes

1.
