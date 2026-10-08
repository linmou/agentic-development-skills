# Issue: Generalize Hard Gate 4 to Output Constructibility

## Problem

Hard Gate 4 currently requires named fill paths for every mandatory storage attribute. That protects persistent artifacts, but makes a storage schema the definition of interface sufficiency. Non-persistent outputs, internal resolution rules, and information hiding are under-specified.

## Proposal

Define Hard Gate 4 as **Output Constructibility**: every mandatory declared output artifact must be constructible from declared inputs, available capabilities, and documented internal resolution rules, or have a meaningful explicit failure condition. A generic failure handler cannot replace a normal construction path.

For persistent extracts, retain a subordinate persistence check that proves mandatory stored attributes can be populated and validated. Storage fields do not become public Request fields automatically.

## Acceptance criteria

- Interface, implementation, and persistence verification levels are distinct.
- Non-persistent outputs receive the same constructibility review as persisted artifacts.
- Missing dependencies, undocumented assumptions, invalid resolver paths, and failure-only paths fail the gate.
- Existing storage-fill-path coverage remains a paired regression: a persisted field that is absent from the public Request but has a documented internal resolver and validation passes C4b/D2 and the subordinate persistence check; the same field with no valid internal population rule fails the persistence check and C4b/D2, without requiring the field to be added to the public Request.
- Rubrics, multi-pass instructions, and report templates use the same output crosswalk vocabulary.
