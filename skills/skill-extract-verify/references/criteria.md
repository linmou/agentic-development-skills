# Extraction criteria (index)

**Overall:** `pass` only if every **blocking** criterion is `pass`.  
Non-blocking fails are listed but do not force overall `fail`.  
`insufficient_evidence` on a blocking criterion blocks overall `pass`.

## Detailed rubrics (score here)

| Criterion | Detailed rubric | What it covers |
|-----------|-----------------|----------------|
| C1, C2, C3, C4a, C5, C6 | `extraction-split-rubric.md` | Split topology, coupling, thin client, **opaque labels**, standalone, completeness |
| C4b | `call-contract-field-rubric.md` | **Field API design** D1–D7 (necessary, sufficient, non-overlap, clear, consistent, layered, evolvable) |

`criteria.md` is the **index + short definitions**.  
Score anchors, hard gates, and output templates live only in the rubric files (single source of truth).

---

## Short definitions

### C1 — Capability, not lifecycle (blocking)
Extract = reusable **capability**. Host = **when** to call, gates, host tokens.

### C2 — One-way dependency (blocking)
Host → extract only. No reverse host import. No host tokens issued by extract.

### C3 — Single writer, thin client (blocking)
Extract owns domain writes. Host: Request → invoke → Response → resume. Audit may re-invoke; must not dual-write.

### C4 — Call contract (blocking if imported)
- **C4a** — Contract exists + defaults + schema ownership + **opaque labels** (log-only tags; not control) + third-party callability → `extraction-split-rubric.md`  
- **C4b** — Field API quality (D1–D7) → `call-contract-field-rubric.md`  
  - **How to score:** `single-agent-multi-pass-scoring.md` (inventory/crosswalk → strict → contradiction → lock).  
  - **Opaque labels ≠ field API.** Opaque = coupling. D1–D7 = interface design.  
  - **Gate 4:** name fill paths for **storage-mandatory** attrs; do not equate “minimal Request works” with D2=5.

### C5 — Standalone trigger (blocking)
Extract description and procedure work without the host.

### C6 — Completeness (non-blocking)
Assets moved, host is adapter, no second write engine, grep clean, contract on callee if imported.

---

## Evidence checklist (gather step)

| Look for | Where |
|----------|--------|
| Capability vs state language | both `SKILL.md` |
| Host → extract invoke | host skill + adapters |
| Reverse host name | extract tree (grep) |
| Dual protocols/scripts | both `references/`, `scripts/` |
| Contract + fields | extract call-contract + C4b multi-pass |
| Storage mandatory attrs (write engines) | validators, templates, persistence hard gates |
| Host redefines schema | host adapter |
