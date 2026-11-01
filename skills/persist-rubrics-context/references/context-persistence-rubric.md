# Context Persistence Rubric (Add/Update for `contexts/`)

Use this rubric before adding or updating project context memory entries.

## Scope
- Target memory: `./.co-improvement/learnt/contexts/**/*.json`
- Entry shape: context JSON template in `references/memory-protocol.md`
- Operation type: `append` | `merge` | `skip` | `ask_human`

## Scale
- 1 = poor / missing
- 2-3 = partial / weak
- 4 = good
- 5 = excellent

## Dimensions (score all)
1. Non-Overlap
   - `append`: genuinely new context versus existing context files.
   - `merge`: same core context, but candidate improves precision.
2. Project Relevance
   - Context is directly useful for this project, not generic advice.
3. Reuse Value
   - Likely useful across multiple future loops.
4. Clarity
   - Statement is concrete and unambiguous.
5. Scope Fit
   - `scope.include` and `scope.exclude` are explicit and usable.
6. Stability
   - Context is stable enough beyond one-off incidents.

## Hard Gates (must pass)
1. Required fields complete
   - `id`, `statement`, `intent_keywords`, `context_keywords`, `scope`, `lifecycle`
2. Scope boundaries present
   - `scope.include` and `scope.exclude` are non-empty lists
3. Keywords present
   - `intent_keywords` and `context_keywords` are non-empty string lists
4. Statement quality
   - concrete, reusable, and testable in future review decisions
5. Non-overlap threshold for append
   - if `Non-Overlap < 4`, do not `append`

## Decision Policy
- `append`: pass all hard gates, `Non-Overlap >= 4`, `Reuse Value >= 4`.
- `merge`: pass hard gates, overlap exists, and candidate sharpens an existing context.
- `skip`: fail any hard gate, or weak `Project Relevance` / `Reuse Value`.
- `ask_human`: use when `append` and `merge` are both plausible.

## Decision Output Template
- Candidate context id: ...
- Scores:
  - Non-Overlap: [1-5]
  - Project Relevance: [1-5]
  - Reuse Value: [1-5]
  - Clarity: [1-5]
  - Scope Fit: [1-5]
  - Stability: [1-5]
- Hard gate check:
  - Required fields complete: [pass/fail]
  - Scope boundaries present: [pass/fail]
  - Keywords present: [pass/fail]
  - Statement quality: [pass/fail]
  - Non-overlap threshold for append: [pass/fail]
- Proposed decision: `append` | `merge` | `skip` | `ask_human` (human confirmation required before any write; authority is `persist-rubrics-context`, not this template)
- Reason: ...
- Merge target (if merge): ...
