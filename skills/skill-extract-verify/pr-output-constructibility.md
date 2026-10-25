# PR Proposal: Generalize Hard Gate 4 to Output Constructibility

## Summary

Replace the storage-specific definition of Hard Gate 4 with an output-construction invariant while preserving storage checks for extracts that persist artifacts.

## Implementation

- Update C4b and D2 to require construction evidence for every mandatory declared output, including status and error artifacts.
- Add dependency, capability, resolver, validation, and meaningful-failure evidence to the Pass A crosswalk.
- Make persistence fill-path verification conditional and subordinate; keep missing storage paths as failures when persistence applies.
- Expand Pass C contradiction attacks for missing dependencies, undocumented assumptions, invalid paths, and generic failure-only handling.
- Update the skill procedure, criteria index, and report template.

## Validation

Verify all three levels independently: the agent interface crosswalk (declared outputs), the implementation crosswalk (internal artifacts and their producers/validators), and the conditional persistence crosswalk (stored attributes only when applicable).

Preserve the storage regression as an explicit pair. For a persisted field that is absent from the public Request, a documented internal resolver plus validation must yield **C4b pass, D2 at least 4, and persistence check pass**; the field remains hidden from the public contract. With the same public contract but no valid internal population rule, the persistence check must fail and **C4b and D2 must fail**, rather than being repaired by exposing the storage field as a Request input.

Then run conceptual cases for a constructible non-persistent output, a missing dependency, an invalid resolver, an undocumented assumption, a meaningful bounded failure condition with a normal path, and generic failure-only handling. Record the crosswalk row, evidence, and expected C4b/D2/persistence verdict for each case.
