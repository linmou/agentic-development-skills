# Storage regression fixture

Intent: known-answer pair for hard gate 4's persistence check. Run skill-contract in `extract` mode on both pairs after editing any rubric, stopping after the C4b audit (do not write `contract.json` into the fixture); if a verdict below changes, the rubric regressed.

Both extracts expose the same public contract and persist a `slug` attribute that is **not** in the public Request. They differ only in whether `slug` has a valid internal population rule.

| Run | host_skill | extracted_skill | Expected |
|-----|------------|-----------------|----------|
| 1 | `host/` | `extract-resolved/` | C1–C3, C4a, C5 pass; persistence crosswalk complete; gate 4 pass; D2 ≥ 4; **C4b pass**; overall **pass**; `slug` stays out of Request |
| 2 | `host/` | `extract-unresolved/` | persistence crosswalk Gap=y on `slug`; gate 4 fail; D2 ≤ 3; **C4b fail**; overall **fail**; Fix must add a population rule, **not** a `slug` Request field |
