# Intent

Provide exact claim text for mandatory debate audits and lightweight phase gates so agents judge concrete artifacts instead of fuzzy stories.

## Request Map Claim

Claim:
`The requirement re-check defines the user-visible outcome and complete definition of done; the request map imports it, selects the smallest vertical executable slice, and defines a phase-safe TDD path.`

Default handling:
Record this artifact for the Red and cumulative Refactor audits. Do not run `$review-with-multi-debate` for request-map by default.

Suggested criteria:

- requirements are concrete and testable
- non-executable requirements remain outside TDD rather than being postponed
- the chosen slice is the smallest usable vertical executable increment
- the proposed test level matches the behavior under change
- planned paths were classified before Red and any semantic override is recorded
- the next phases can proceed without mixing test and production edits

## Red Claim

Claim:
`The red phase adds only the next failing test; the failure is caused by missing behavior rather than syntax, environment, or unrelated breakage; the saved pre-Red request map traces every constraining clause in the active requirement to behavior-controlling properties and the full family of controls that change the selected path's observable execution; every exclusion quotes source evidence that affirmatively permits it; no exclusion contradicts the active requirement artifacts; and every mapped control has a non-neutral asserted effect that rejects its named shortcut.`

Suggested criteria:

- changed files belong to red
- the test is the smallest useful specification step
- the failure output points to missing behavior
- a pre-Red monitor gate passed the map against these Red criteria, records its digest and the planned tests' clean baseline hashes/status, and still matches the audited map; a changed, inferred, or reconstructed map must be re-gated before any test edit
- every constraining clause in the imported active requirement and definition of done maps there to a property or explicit exclusion
- every independent option, argument, state transition, timer/wait seam, or external call governing a mapped property has a causally observable, asserted non-neutral effect or an exclusion backed by quoted user or repository requirement evidence; a zero, empty, false, no-op, immediate-success, or one-attempt fixture does not exercise the corresponding effect unless that boundary value is itself required
- when the slice reuses an existing policy or mechanism, the map includes every control in that family which changes the selected path's observable sequence, timing, bounds, ordering, or side effects and is constrained by the active requirement; an unconstrained neighboring branch is not a reason to expand Red
- every exclusion names its source and exact quote that affirmatively permits omission or neutralization; an exclusion based on a control being pre-existing, not newly requested, internal, or allegedly not user-visible fails, as does one that contradicts the requirement table, definition of done, another mapped property, or selected execution path
- for every mapped control, the exact targeted test's assertions would fail if the named shortcut were used
- each added scenario distinguishes a separate behavior decision constrained by the active requirement; implementation branches that the requirement does not constrain stay outside Red and rely on existing regression coverage
- no shortcut-mutant production changes are in the active worktree
- no production code was changed

## Green Gate Claim

Claim:
`The green phase changed only production/runtime files, did not edit tests, made the targeted red test pass, and saved the production diff for cumulative review.`

Suggested criteria:

- changed files belong to green
- the targeted red test now passes
- tests remained untouched
- the production diff is saved for the cumulative Refactor audit

Default handling:
Use the monitor scope check, changed-file list, targeted test output, and saved diff. Do not run `$review-with-multi-debate` for Green by default.

## Regression Claim

Claim:
`The regression check ran the full available suite after the green change, and the results show no new unrelated failures or flakiness.`

Suggested criteria:

- targeted tests passed before the full suite
- the full suite was run or the blocker is explicitly documented
- failures, if any, are analyzed rather than ignored
- repeated runs do not show flakiness

Default handling:
Record targeted and full-suite output for the cumulative Refactor audit. Do not run `$review-with-multi-debate` for regression by default.

## Cumulative Refactor Claim

Claim:
`The final production diff from pre-Green to post-Refactor implements only the behavior required by the request map and red tests, avoids speculative logic or hidden fallbacks, preserves passing regression results, and leaves the code simpler or no worse than before.`

Suggested criteria:

- changed files belong to refactor
- the suite stayed green after refactoring
- the cumulative production diff matches the request map and red tests
- the refactor-only diff does not introduce new behavior
- the change reduces duplication, indirection, or naming debt
- hidden fallback, retry, broad rewrite, or unrelated public behavior changes are absent
- no test files were edited
- the executable slice did not displace required non-TDD artifacts or the user-visible definition of done

## Docs Claim

Claim:
`The documentation phase updates only docs relevant to the completed code change, keeps the docs aligned with implemented behavior, and does not edit tests or production code.`

Default handling:
Record the docs artifact for final closeout. Do not run `$review-with-multi-debate` for docs by default.

Suggested criteria:

- changed files belong to docs
- the docs describe behavior that the code now implements
- no production or test files were edited in this phase
- the doc delta is narrow rather than a speculative redesign

## Final Claim

Claim:
`The completed work preserves strict TDD discipline, covers each mapped requirement with passing tests, updates relevant docs after TDD is complete, and clearly reports remaining risks.`

Default handling:
Use this for final closeout. Do not run `$review-with-multi-debate` for final by default.

Suggested criteria:

- every requirement has a passing test
- every non-TDD requirement has its required artifact and acceptance evidence
- the user-visible definition of done is satisfied, not merely the code slice
- red audit, green gate, regression, cumulative refactor audit, and docs artifacts exist when docs were relevant
- phase violations were either absent or corrected explicitly
- remaining risks are concrete and small
