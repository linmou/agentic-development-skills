# Intent

Define what the benchmark should reward for `fast-multi-agent-tdd`.

## Focus

Benchmark three things separately:

- trigger accuracy, especially non-necessary trigger cases
- workflow discipline after trigger
- output quality after trigger

Do not collapse these into one vague pass or fail judgment. A skill can trigger correctly but still produce a bloated workflow, or it can have a good workflow but trigger when it should stay silent.

## Trigger Dimensions

For non-trigger evals, check:

- the skill does not attach itself to pure review, explanation, or diagnosis requests
- the response does not inject red-green-refactor, monitor-agent setup, or phase audits when no implementation was requested
- the response stays inside the actual user intent

## Workflow Dimensions

Each positive eval should check these dimensions where relevant:

- a requirement re-check defines the complete user-visible outcome before selecting a methodology
- mixed requests classify executable behavior separately from guidance, rubrics, data, research, and recorded results
- TDD applies only to the executable rows in the requirement map
- the first executable slice is the smallest vertical slice that contributes to the complete outcome
- planned paths are preflighted against phase contracts before Red
- phase scope is published at each transition from a Git snapshot containing the scope artifact; the old caller-supplied `--changed` interface is not used
- phase order is explicit: request map, red, green, regression, production refactor, test refactor
- red starts with the next failing test
- green does not edit tests
- refactor starts only after green plus regression are clean
- the full available suite is required after code changes
- the monitor agent stays non-editing and performs phase-boundary checks
- Red hands off to `$review-with-multi-debate`
- Green uses a deterministic gate instead of a debate by default
- Refactor hands off to `$review-with-multi-debate` with the cumulative production diff from pre-Green to post-Refactor
- Test Refactor follows the converged production Refactor audit, edits only test-like paths, and hands off to `$review-with-multi-debate`
- implementation ownership stays with one main agent rather than parallel workers

## Output Quality Dimensions

Each positive eval should also check:

- no parallel worker choreography is introduced
- green stays minimal and avoids speculative abstractions
- conflicting existing tests are handled explicitly
- refactor does not become a second implementation phase
- the cumulative Refactor audit checks final code smell, overreach, hidden fallbacks, and behavior drift
- the Test Refactor audit checks behavior-map coverage, independent oracles, boundary evidence, assertion strength, test selection, and regression preservation
- an empty Test Refactor diff records a no-op artifact and skips debate; any changed test diff requires the mandatory audit
- the response stays concrete and actionable rather than writing process theater

## Failure Patterns To Penalize

- code-first behavior before a failing test exists
- selecting TDD before defining the complete deliverable
- forcing Markdown, rubrics, data curation, research evaluation, or result recording through TDD
- treating an isolated helper or scoring engine as complete when the requested user-facing artifact is unusable
- discovering a phase-path classification collision only after Red has started
- parallel workers being introduced for implementation, exploration, or test drafting
- green or refactor mutating tests
- skipping the full-suite regression check
- vague Red or Refactor audit language with no explicit `$review-with-multi-debate` handoff
- running default Green debate instead of the cheaper Green gate
- proposing large infrastructure, fallback logic, or configuration knobs not demanded by the current failing test

## Grading Guidance

When grading `evals/evals.json` expectations:

- grade trigger expectations independently from workflow and quality expectations
- fail any expectation that is only implied weakly
- require explicit mention for requirement classification, monitor behavior, phase order, and regression checks
- require explicit absence of TDD orchestration in non-trigger evals
- prefer lean plans over comprehensive but bloated plans
- penalize plans that are technically correct but operationally wasteful
