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
- a compact filter or selector plan identifies existing compatible controls with material selection effects and requires combined, non-neutral interaction evidence without combining mutually exclusive strategies
- planned paths are preflighted against phase contracts before Red
- phase scope is published at each transition from a Git snapshot containing the scope artifact; the old caller-supplied `--changed` interface is not used
- phase order is explicit: request map, red, green, regression, production refactor, test refactor
- red starts with the next failing test
- green does not edit tests
- refactor starts only after green plus regression are clean
- the full available suite is required after code changes
- the monitor agent stays non-editing, has a stable identity from an authorized delegation mechanism, and performs phase-boundary checks
- delegation is backend-neutral: an absent candidate interface triggers discovery of another available mechanism before the run is declared blocked
- Red hands off to `$review-with-multi-debate`
- each Red reviewer writes its own correctly named JSON with stable identity and delegation-source fields; the controller binds all three files and their hashes to the role receipt before `record_round`, deterministic aggregation, blocking evidence/counterevidence inspection, and the strict phase gate before Green
- reviewer execution respects available capacity; serial execution still uses three distinct identities, roles, isolated prompts, and reviewer-owned files, and a capacity retry preserves already valid files while retrying only the missing reviewer
- a reviewer-required Red correction is monitor-approved from its precise plan, scope, retained provenance, and current pre-edit test hashes/status; the append-only numbered snapshot precedes the planned test-only edit, and genuine Red plus the next three-reviewer iteration verify the corrected content
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
- testing a new filter predicate in isolation while omitting a compatible existing quota, ordering, or output control that materially changes selection
- parallel workers being introduced for implementation, exploration, or test drafting
- green or refactor mutating tests
- skipping the full-suite regression check
- vague Red or Refactor audit language with no explicit `$review-with-multi-debate` handoff
- reviewer verdicts preserved only in chat or transcribed into JSON by the main agent/monitor instead of reviewer-owned files
- requiring one provider-specific delegation operation, identity prefix, source label, or Git-ref namespace
- stopping on one missing delegation interface without checking another available authorized mechanism
- treating independence as mandatory concurrency, discarding valid reviewer files after a capacity error, or replacing a missing reviewer by restarting, relabeling, reusing an identity, or transcription
- requiring reviewer-requested corrected test content before the numbered pre-Red snapshot that authorizes editing it
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
