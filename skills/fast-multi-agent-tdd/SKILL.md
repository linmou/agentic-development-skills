---
name: fast-multi-agent-tdd
description: Use when the user explicitly wants executable feature or bug-fix behavior delivered under strict Red-Green-Refactor with requirement re-checking, a dedicated monitor, mandatory Red and cumulative Refactor debates, deterministic Green gates, and regression checks. Apply TDD only to executable behavior; do not use it for Markdown, SKILL.md, AGENTS.md, rubrics, documents, data curation, research evaluation, or review/diagnosis-only work.
---

# Fast Multi Agent TDD

## Overview

Use this skill for executable implementation work when the user wants strict TDD and strong phase discipline. Re-check the user-visible outcome before selecting tests or code. Keep implementation ownership with one main agent and use the monitor only for phase enforcement and audit handoff.

This skill is not a generic planning or documentation workflow. For mixed requests, split executable behavior from guidance, rubric, data, research, and result-production work; run TDD only on the executable slice.

## Trigger Conditions

Use this skill when the request includes some combination of:

- add or change executable behavior
- fix a reproducible software bug
- strict TDD, red-green-refactor, or regression checks
- explicit auditing of Red and Refactor phases
- concern that green or refactor work might quietly mutate tests

Do not use this skill when:

- the user only wants a code review
- the user only wants diagnosis, requirements analysis, planning, or status
- the task edits only Markdown, SKILL.md, AGENTS.md, rubrics, prompts, documents, schemas, or research guidance
- the task curates data, performs a research/evaluation run, or computes a one-off scientific result without changing executable behavior

## Core Rules

- Requirements come before methodology. Do not select TDD scope, test level, agents, or audit mode until the requirement re-check passes.
- When a new user requirement changes the active slice's behavior or invalidates an existing test, stop the current phase, mark the old requirement as superseded, and tell the user about the conflict to confirm that the change reflects their intent.
- Treat the conflicting instruction as a proposed replacement, not as its own confirmation; resume only after a later user reply explicitly confirms the replacement.
- The definition of done must name the user-visible outcome, must-exist artifacts, acceptance evidence, exclusions, and resource constraints.
- TDD owns only executable behavior. Keep non-code workstreams outside TDD phases; do not postpone a required skill, rubric, dataset, or result merely because code is unfinished.
- The first slice must be the smallest end-to-end usable behavior, not an isolated lower-level engine that leaves the requested artifact unusable.
- Red owns test changes. Green and refactor do not edit tests. If a new test is needed later, go back to red.
- Red is locked by the pre-Red monitor gate defined below; without its pass, stop before editing tests.
- Update docs relevant to the code change only after red, green, regression, and refactor are complete. Do not mix README or other doc edits into refactor.
- The main agent owns the critical path and the implementation work.
- A dedicated monitor agent never edits files. It checks phase scope, records violations, and blocks phase completion if boundaries were crossed.
- Do not spawn parallel workers for implementation, exploration, or test drafting. Extra workers here create chaos rather than speed.
- Red and cumulative Refactor end with mandatory `$review-with-multi-debate` audits.
- Before aggregation, validate every reviewer file against the debate skill's JSON contract and regenerate malformed output at the same iteration.
- If the monitor or a mandatory debate is unavailable, fails, or its aggregate status is not `converged`, stop at that phase and tell the user; matching verdict text, a phase guard, self-review, or a limitation note is not a substitute.
- User-specified audit counts, resource limits, and concurrency constraints override workflow defaults.
- Green ends with a deterministic gate, not a debate by default: scope check, no test edits, targeted test pass, and saved production diff.
- Refactor audit must review the cumulative production diff from pre-Green to post-Refactor, not only the refactor-only diff.
- After any code change, run the full available test suite. This is the regression check.

## Roles

Keep the setup minimal.

- Main agent: owns the current phase outcome and all file edits for that phase.
- Monitor agent: no file edits, no implementation suggestions, only scope enforcement and audit orchestration.
- Debate reviewers: independently audit Red and cumulative Refactor artifacts through `$review-with-multi-debate`.

## Workflow

### 0. Requirement Re-check and Applicability Gate

Before starting a monitor, writing a request map, or selecting TDD:

1. Restate the requested outcome in one sentence from the user's perspective.
2. Carry forward relevant constraints already present in the conversation and repository guidance; do not ask the user to repeat them.
3. Record a compact requirement-to-feature table:

| Requirement | User-visible feature | Must-exist artifact | Acceptance evidence | Work type | TDD? |
|---|---|---|---|---|---|

Use work types such as `executable`, `guidance`, `rubric`, `data`, `research`, and `result`.

4. Define done as the complete set of required artifacts and operational results, not merely a passing component test.
5. Mark executable rows for TDD. Keep all other rows outside this skill's phases.
6. Choose the smallest vertical executable slice that advances the user-visible outcome. Reject a lower-level slice that cannot be used without several still-missing primary artifacts.
7. Select the resource ceiling for the mandatory Red and cumulative Refactor debates; preserve any tighter human limit.
8. Preflight the planned changed paths against [references/phase_contracts.md](references/phase_contracts.md). Resolve path-classification collisions before Red. If a runtime file sits under a lexically test-like path, obtain and record a human semantic classification or relocate it before editing.

Ask at most one concise clarification only when different answers would materially change the deliverable. If no executable behavior remains after classification, stop using this skill and continue with the appropriate non-TDD workflow.

### 1. Request Map

Before writing tests or code:

- read the nearest guidance files such as `AGENTS.md`, `CLAUDE.md`, `README.md`, and nearby docs
- import the requirement re-check rather than reinterpreting the request
- identify the next executable behavior inside the selected vertical slice
- identify the highest-risk execution boundary
- identify the concrete minimal execution path that actually traverses the highest-risk execution boundary
- identify the observable evidence that will prove the boundary was crossed during the test
- list every behavior-controlling property of the next executable behavior and, for each property, the test observation and one plausible shortcut implementation that must fail
- treat bounds, ordering, timing, and forbidden side effects as separate properties when the requirement makes them behaviorally significant; omit dimensions the requirement does not constrain
- trace every constraining clause in the imported active requirement and definition of done to one listed property or an explicit exclusion; naming the outcome without its required bound, order, timing, or side-effect constraint is incomplete
- for each property, inventory every independent existing or planned control that governs it, such as an option, argument, state transition, timer/wait seam, or external call; each control needs its own non-neutral asserted effect, or an exclusion backed by quoted user or repository requirement evidence
- when the slice reuses an existing policy or mechanism, inventory the controls that change the selected path's observable sequence, timing, bounds, ordering, or side effects and are constrained by the active requirement; preserving the headline outcome does not make one of those controls irrelevant, but neighboring unconstrained branches do not enter the slice
- call a control non-neutral only when the test gives it a value that makes its required effect observable and asserts that effect; zero delay, an empty value, a false flag, a no-op callback, immediate success, or one attempt is neutral for a property whose effect is respectively waiting, content, enablement, invocation, transition, or repetition, unless that boundary value is itself the requirement
- reject an exclusion that merely says the control is pre-existing, not newly requested, internal, or not user-visible, or that contradicts the requirement table, definition of done, another mapped property, or the selected execution path; every exclusion must name its source and quote the exact user or repository requirement that affirmatively permits omitting or neutralizing that control
- decide the likely test level: feature, integration, or unit
- list predicted Red, Green, Refactor, and documentation paths with their semantic classifications
- if you plan to rely on lower-level tests because no high-risk integration boundary is actually crossed, justify that with a `strace` or `dtruss` check on the minimal execution path rather than with narrative alone
- derive a short `feature_name` for audit files

Start the monitor agent here. It should open [references/phase_contracts.md](references/phase_contracts.md) and enforce it for the rest of the run.

Before any Red edit, save the request-map artifact as `audits/<feature_name>_request_map.md` for the later Red and Refactor audits. A missing map blocks Red and must not be reconstructed after tests exist. Do not run `$review-with-multi-debate` for request-map by default.

### 2. Red

Main goal: produce the next failing test and nothing else.

Before the first Red edit, give the monitor the saved request-map path and digest plus the planned test paths and their current Git hashes/status. The monitor must check the map against the Red criteria, including clause/control coverage and exact evidence for every control exclusion, then return a pre-Red gate pass containing the map digest and test baselines; preserve that exact response in the Red artifact, and if the map changes, return to this gate before editing tests.

Allowed actions:

- create or edit tests
- add a brief Gherkin feature file when the behavior is broad enough to need one
- adjust test fixtures only if required by the new test
- write the first failing test at the highest-risk execution boundary identified in Request Map
- use the highest-risk boundary to choose the test entry point, not to narrow the behavior asserted; identify each behavior-controlling property of the active requirement, make it observable, and do not neutralize it with a fixture value
- for every property and independent control recorded in the request map, use a non-neutral fixture and assert the control's effect through a deterministic fake or spy seam instead of real sleeping; add another test only when it distinguishes a separate behavior decision constrained by the active requirement
- specify only the next behavior; do not bundle later validation, sensitivity, reporting, or error-path requirements into the first Red merely because they share one CLI
- if the boundary involves multiple components, process execution, shell, filesystem, network, concurrency, or external tool invocation, an integration test is mandatory
- when an integration test is mandatory, the failing test must assert at least one observable outcome that proves the risky boundary was actually traversed
- command construction or mocked boundary tests do not satisfy this requirement unless the boundary itself is purely local logic
- run the targeted test to confirm the failure reason is missing behavior rather than syntax or setup

Before closing red:

- run the monitor scope check for `red`
- confirm every mapped property control has a non-neutral asserted effect that would reject its named shortcut
- run `$review-with-multi-debate` with the Red claim from [references/phase_audits.md](references/phase_audits.md)

### 3. Green

Main goal: make the red test pass with the smallest production change.

Allowed actions:

- edit production code
- add the smallest missing wiring required for the failing test
- run the targeted test until it passes

Forbidden actions:

- editing tests
- broad cleanup
- hidden fallback logic

Before closing green:

- run the monitor scope check for `green`
- confirm no test files changed
- confirm the targeted red test now passes
- save the Green production diff for the later cumulative Refactor audit
- do not run `$review-with-multi-debate` at Green by default

### 4. Regression Check

Run the full available test suite after the green change. This is not optional.

If the suite is large, you may first run the closest package or component suite, but phase completion still requires the full available suite unless the environment makes that impossible.

Record the targeted and full-suite results for the later cumulative Refactor audit. Do not run `$review-with-multi-debate` for regression by default.

### 5. Refactor

Only start refactor after green plus regression are both clean.

Run `$code-smell-monitor` on the changed production scope before editing to have an understanding of code quality.

Allowed actions:

- simplify production code
- remove duplication
- improve naming or structure
- tighten obvious implementation seams

Forbidden actions:

- editing tests
- editing docs such as `README.md`
- sneaking in new behavior
- using refactor as a second green phase

Before closing refactor:

- run the full available test suite again
- rerun `$code-smell-monitor` on the same scope and record both report paths
- run the monitor scope check for `refactor`
- audit with `$review-with-multi-debate` using the cumulative Refactor claim from [references/phase_audits.md](references/phase_audits.md)
- include the cumulative production diff from pre-Green to post-Refactor, the refactor-only diff, the request map, the Red audit result, the Green gate result, and regression results

### 6. Documentation Follow-Up

Only start this step after red, green, regression, and refactor are done.

Allowed actions:

- update docs relevant to the completed code change
- keep doc edits narrow and implementation-aligned

Forbidden actions:

- editing tests
- editing production code
- using docs as a place to sneak in design changes that the code does not implement

Before closing documentation:

- run the monitor scope check for `docs`
- record the docs artifact for final closeout
- do not run `$review-with-multi-debate` for docs by default

### 7. Final Closeout

Before finishing:

- confirm each mapped requirement has a passing test
- confirm every non-TDD requirement row has its must-exist artifact and acceptance evidence
- confirm the user-visible definition of done is satisfied end to end
- summarize any unresolved risks
- keep the final explanation short and oversight-friendly

Do not run a final `$review-with-multi-debate` by default. The final closeout should point to the Red audit, Green gate, regression result, and cumulative Refactor audit.

## Monitor Protocol

The monitor agent is separate on purpose. Its job is to stop phase bleed.

At each phase boundary:

1. Collect the changed file list for the phase.
2. Run:

```bash
python scripts/phase_guard.py --phase red --changed tests/test_login.py docs/login.md
python scripts/phase_guard.py --phase green --changed src/login.py
python scripts/phase_guard.py --phase refactor --changed src/login.py
python scripts/phase_guard.py --phase docs --changed README.md docs/login.md
```

3. If the guard fails, stop. Do not rationalize the violation. Move the work into the correct phase. For a pre-recorded human semantic path override, record the override and have the monitor apply it explicitly instead of pretending the lexical classifier passed.
4. Hand the phase artifact plus the claim to `$review-with-multi-debate` only for Red and Refactor. Other phases record artifacts for those audits and final closeout.

Use [references/phase_contracts.md](references/phase_contracts.md) for the exact phase ownership rules and [references/phase_audits.md](references/phase_audits.md) for audit claims.

## Audit Integration

Each `$review-with-multi-debate` audit should hand off:

- the artifact for the phase
- the exact claim text from [references/phase_audits.md](references/phase_audits.md)
- the `feature_name`
- the phase label

Mandatory debate phases:

- `red`
- `refactor`

Default gate/artifact phases:

- `request_map`
- `green`
- `regression`
- `docs`
- `final`

Keep the phase artifact compact. Good artifacts are:

- requirement map plus chosen test seam
- failing test output
- Green gate output plus saved production diff
- targeted and full suite results
- cumulative production diff plus refactor diff plus full suite results

For Red and cumulative Refactor audits, also include:

- the chosen execution path and the observable evidence that proves the path crosses the claimed boundary
- if lower-level tests are claimed to be sufficient, the `strace` or `dtruss` output that shows no high-risk boundary was crossed on the minimal execution path
- if the path does not prove traversal of the risky boundary, red is incomplete even if the test fails as expected

## Resources

- Use [scripts/trace_boundary_check.py](scripts/trace_boundary_check.py) to run `strace` or `dtruss` on a minimal execution path and emit JSON evidence about process, network, and filesystem boundary crossings.
- Open [references/phase_contracts.md](references/phase_contracts.md) when you need exact edit-boundary rules.
- Open [references/phase_audits.md](references/phase_audits.md) when preparing the mandatory Red or cumulative Refactor audit with `$review-with-multi-debate`.
- Use [scripts/phase_guard.py](scripts/phase_guard.py) for the monitor agent's scope check.
- Use [evals/evals.json](evals/evals.json) to benchmark whether the skill triggers on the right work and stays lean.
