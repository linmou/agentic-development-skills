# Detailed Workflow

## Intent

Preserve the complete phase rules and evidence contracts behind the concise controller in `../SKILL.md`. Read the relevant section before entering each phase; the entrypoint controls phase order.

## Start Gate

The authoritative activation boundary and start gate are in the first sections of `../SKILL.md`. The monitor approves the proposed pre-Red state before the main agent publishes its immutable snapshot. The sections below define the artifacts checked by that gate and the phases it unlocks.

## Overview

Use this skill for executable implementation work when the user wants strict TDD and strong phase discipline. Re-check the user-visible outcome before selecting tests or code. Keep implementation ownership with one main agent and use the monitor only for phase enforcement and audit handoff. File scope is decided incrementally at phase boundaries from Git snapshots and a Git-backed scope artifact.

This skill is not a generic planning or documentation workflow. For mixed requests, split executable behavior from guidance, rubric, data, research, and result-production work; run TDD only on the executable slice.

## Trigger Conditions

Use this skill when the request includes some combination of:

- add or change executable behavior
- fix a reproducible software bug
- strict TDD, red-green-refactor, or regression checks
- explicit auditing of Red, production Refactor, or Test Refactor phases
- concern that green or refactor work might quietly mutate tests

Do not use this skill when:

- the user only wants a code review
- the user only wants diagnosis, requirements analysis, planning, or status
- the task edits only Markdown, SKILL.md, AGENTS.md, rubrics, prompts, documents, schemas, or research guidance
- the task curates data, performs a research/evaluation run, or computes a one-off scientific result without changing executable behavior

## Core Rules

- Requirements come before methodology. Select TDD scope, test level, TDD roles, and audit mode only after the requirement re-check passes.
- When a new user requirement changes the active slice's behavior or invalidates an existing test, stop the current phase, mark the old requirement as superseded, and tell the user about the conflict to confirm that the change reflects their intent.
- Treat the conflicting instruction as a proposed replacement, not as its own confirmation; resume only after a later user reply explicitly confirms the replacement.
- The definition of done must name the user-visible outcome, must-exist artifacts, acceptance evidence, exclusions, and resource constraints.
- TDD owns only executable behavior after activation. Run prerequisite workflows to their implementation handoff, then preserve their evidence while TDD owns permanent tests and production changes. Keep non-code workstreams outside TDD phases; do not postpone a required skill, rubric, dataset, or result merely because code is unfinished.
- The first slice must be the smallest end-to-end usable behavior, not an isolated lower-level engine that leaves the requested artifact unusable.
- Red owns test specification changes. Green and production Refactor do not edit tests. Test Refactor may reorganize tests only after the cumulative production Refactor audit; if behavior, an oracle, or a boundary must change, go back to Red.
- After activation, Red is locked by the pre-Red monitor gate defined below; its pass unlocks the permanent regression-test edit.
- Update docs relevant to the code change only after Red, Green, regression, production Refactor, and Test Refactor are complete. Do not mix docs into either refactor phase.
- The main agent owns the critical path and the implementation work.
- A dedicated monitor agent never edits files. It checks phase scope, records violations, and blocks phase completion if boundaries were crossed.
- Keep implementation and Red test drafting for the active TDD slice with the main agent. A prerequisite workflow retains its own exploration orchestration until the activation handoff.
- Red always ends with a mandatory `$review-with-multi-debate` audit. On the full route, cumulative production Refactor and Test Refactor do too.
- Each delegated reviewer owns its audit output: it writes exactly one correctly named reviewer JSON for the assigned phase and iteration. A parent or monitor must not transcribe reviewer messages into JSON; chat-only verdicts are not audit artifacts.
- Reviewer independence comes from distinct stable identities, assigned roles, isolated review prompts, and reviewer-owned output, not from simultaneous execution. Schedule reviewer work within the available concurrency or capacity limit and run reviewers serially when only one reviewer slot is available.
- Before aggregation, run the debate skill's `record_round` expected-file gate, validate each reviewer JSON against its contract and regenerate malformed output at the same iteration, aggregate deterministically, and inspect blocking status, evidence, and counterevidence. Run its `advance_phase` gate before leaving a mandatory debate phase.
- A monitor or reviewer exists only when an authorized delegation mechanism gives it an independent context and returns a stable identity. Native worker tools, task APIs, MCP servers, and installed agent CLIs or APIs are valid examples, not an exhaustive list. Record the returned identity and actual mechanism in the applicable artifact; main-agent or otherwise self-authored monitor/reviewer evidence never counts.
- If one candidate interface is unavailable, inspect the interfaces exposed in the current environment and try another authorized delegation mechanism before stopping. Stop when none can provide the required independent role, a role fails, or a mandatory debate does not converge. Matching verdict text, a phase guard, self-review, or a limitation note is not a substitute. The filesystem recovery below never repairs or bypasses a role, review, debate, dependency, or capacity failure.
- User-specified audit counts, resource limits, and concurrency constraints override workflow defaults.
- Green ends with a deterministic gate, not a debate by default: scope check, no test edits, targeted test pass, and saved production diff.
- Refactor audit must review the cumulative production diff from pre-Green to post-Refactor, not only the refactor-only diff.
- After any code change, run the full available test suite. This is the regression check.

## Roles

Keep the setup minimal.

- Main agent: owns the current phase outcome and all file edits for that phase.
- Monitor agent: no file edits, no implementation suggestions, only scope enforcement and audit orchestration.
- Debate reviewers: independently audit Red, cumulative production Refactor, and Test Refactor artifacts through `$review-with-multi-debate`.

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
7. Select the resource ceiling for the mandatory Red, cumulative production Refactor, and Test Refactor debates; preserve any tighter human limit.
8. Classify the slice as `compact` or `full` before any TDD snapshot or formal Red test edit. `compact` requires bounded, deterministic, local CLI, process, or filesystem behavior, including config-driven materialization, with no network, GPU, concurrency, nondeterminism, external service, unrelated persistent side effect, or other high-risk behavior. Any uncertainty selects `full`.
9. Preflight the planned changed paths against [phase_contracts.md](phase_contracts.md). Resolve path-classification collisions before Red. If a runtime file sits under a lexically test-like path, obtain and record a human semantic classification or relocate it before editing.

Ask at most one concise clarification only when different answers would materially change the deliverable. If no executable behavior remains after classification, stop using this skill and continue with the appropriate non-TDD workflow.

### 1. Request Map

Before writing permanent tests or production code:

- treat this saved request map as the compact Scope & Evidence Plan: accepted scope stays authoritative, while discovered evidence may strengthen proof without adding product behavior

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
- for a compact filter or selector change, inspect the existing parser, selector, configuration, and tests for controls that can operate in the same request and materially change selected membership, cardinality, ordering, or output; list each compatible control in the Scope & Evidence Plan and require an interaction test that exercises the new filter and a binding non-neutral value of that control together, unless existing evidence already crosses both behaviors and asserts their combined effect
- do not treat a mutually exclusive strategy as a compatible control; record the incompatibility and its code, configuration, or requirement source instead of inventing a combined behavior
- for the strict-MS selector case, `limit_per_benchmark` is compatible and material: use a limit small enough to bind and assert both strict-dominance membership and the per-benchmark cap; `all_data` is a separate strategy rather than a strict-filter interaction when the existing configuration makes the strategies mutually exclusive
- when the slice reuses an existing policy or mechanism, inventory the controls that change the selected path's observable sequence, timing, bounds, ordering, or side effects and are constrained by the active requirement; preserving the headline outcome does not make one of those controls irrelevant, but neighboring unconstrained branches do not enter the slice
- call a control non-neutral only when the test gives it a value that makes its required effect observable and asserts that effect; zero delay, an empty value, a false flag, a no-op callback, immediate success, or one attempt is neutral for a property whose effect is respectively waiting, content, enablement, invocation, transition, or repetition, unless that boundary value is itself the requirement
- reject an exclusion that merely says the control is pre-existing, not newly requested, internal, or not user-visible, or that contradicts the requirement table, definition of done, another mapped property, or the selected execution path; every exclusion must name its source and quote the exact user or repository requirement that affirmatively permits omitting or neutralizing that control
- decide the likely test level: feature, integration, or unit
- list predicted Red, Green, production Refactor, Test Refactor, and documentation paths with their semantic classifications; predictions are initial guidance, not a complete future production allowlist
- if you plan to rely on lower-level tests because no high-risk integration boundary is actually crossed, justify that with a `strace` or `dtruss` check on the minimal execution path rather than with narrative alone
- derive a short `feature_name` for audit files
- declare `route: compact|full` and list the concrete eligibility or exclusion reasons from Requirement Re-check

Before any formal Red edit, save the request-map artifact as `audits/<feature_name>_request_map.md` for the later Red and Refactor audits. A missing map blocks Red and must not be reconstructed after formal Red begins. Do not run `$review-with-multi-debate` for request-map by default.

After saving the map, resolve and invoke an available authorized delegation mechanism for the dedicated monitor. Give it the map path and [phase_contracts.md](phase_contracts.md), and retain the stable identity returned by the backend. Create the snapshot and begin the formal Red test only after the independent monitor is running. If one interface is unavailable, try another mechanism already exposed by the environment; stop only when none can satisfy the role contract.

Write `audits/<feature>_role_receipt.json` only from the actual delegation result. It records schema `2`, the exact feature, the request-map route, the returned opaque monitor identity, and a nonempty `monitor_source` naming the mechanism used. Do not infer identity format from a provider or filesystem layout.

If receipt validation fails because its schema or transcription is malformed, correct it only against the original delegation result and revalidate it while the gate remains locked. If snapshot creation publishes no ref, correct a non-destructive invocation or repository-state problem and retry. Missing or ambiguous provenance, an unexpected existing phase ref, partial publication, or an unresolved monitor rejection remains a stop condition; never synthesize role evidence or overwrite a ref.

Write the proposed Red scope with `baseline_ref: refs/tdd/<feature>/pre_red`. <!-- initial-pre-red-monitor-validation --> Before that ref exists, give the dedicated monitor the proposed request map, its digest, route, planned path classifications, Red scope, and planned test-file Git hashes/status. The monitor validates those inputs directly without running tests, `phase_guard.py`, or resolving the intended baseline ref. Correct and recheck any finding inside this initial gate; because no approved initial snapshot or Red review exists yet, this is not a numbered Red round.

<!-- initial-pre-red-snapshot-publication --> After the monitor-authored pass, create the first snapshot as `pre_red`, pass the receipt explicitly, and verify the returned ref and commit:

```bash
python scripts/tdd_snapshot.py create --feature <feature> --phase pre_red --roles audits/<feature>_role_receipt.json
```

Snapshots capture tracked changes and non-ignored untracked files using normal Git ignore rules. Before entering the phase, verify that the ref contains the required request map, scope, receipt, and audit evidence. Keep those files non-ignored. Ignored environments, caches, and results are excluded; a required ignored artifact needs an explicitly authorized ignore-rule exception for that file, never a global force-add. See the coverage boundary in [phase_contracts.md](phase_contracts.md).

The monitor pass and snapshot publication unlock the formal Red test edit.

At every later phase transition, write the next scope artifact first, then capture the current worktree with `scripts/tdd_snapshot.py` so the immutable baseline contains that exact artifact. Decide the next phase's protected paths and semantic overrides, write `audits/<feature>_<phase>_scope.json`, and record the baseline ref and commit in the phase artifact. Name the Red-exit/pre-Green snapshot `pre_green`; name later snapshots `pre_<next-phase>`. Every create passes `--roles`. From `pre_green` onward, first add the distinct stable Red reviewer identities and the actual nonempty `reviewer_source` delegation mechanism to the receipt, then pass the latest accepted Red provenance artifact and matching iteration through `--provenance ... --review-iteration <M>`. Snapshot creation rejects stale iterations and re-hashes the staged receipt, provenance, and every bound audit before publishing. A missing, stale, rejected, or failed receipt/provenance/snapshot keeps the next phase locked; only the bounded non-publishing corrections above may be retried. Production phases may leave `editable` out; Test Refactor and Documentation must provide an explicit `editable` list.

<!-- post-red-numbered-rounds-only --> A request-map or test correction required by a completed Red review starts a subsequent Red round. Before any corrected test edit, update the map and Red scope, obtain a fresh monitor gate, retain the actual prior Red reviewer IDs in the receipt, and create the next append-only baseline:

```bash
python scripts/tdd_snapshot.py create --feature <feature> --phase pre_red --round <N> --roles audits/<feature>_role_receipt.json
```

Round 1 remains `pre_red`; round `N > 1` publishes `pre_red_round_<N>` and requires the latest accepted delegated-reviewer provenance through `--provenance ... --review-iteration <N-1>`. Point the Red scope at that exact ref. Never delete or overwrite a prior round ref or audit, weaken protected/editable scope, or edit production while opening the new Red round.

<!-- post-review-correction-order --> Use this exact order for a correction required by a completed Red review:

1. Write a precise correction plan that cites the disputed reviewer criteria, names every test path allowed to change, states the intended scenario/assertion correction, and names the targeted command and expected missing-behavior failure. Update the request map and Red scope for the intended numbered ref; retain all prior reviewer provenance in the role receipt.
2. Have the dedicated monitor validate that plan, the updated map and scope, the retained provenance, and the current pre-edit Git hash/status of every planned test. The intended numbered ref does not exist yet, so the monitor checks its expected name rather than resolving it. It must not require the corrected test content to exist at this pre-edit boundary.
3. After the monitor pass, publish and verify the append-only numbered snapshot and returned commit. The snapshot authenticates the correction artifacts and unchanged current test baseline.
4. Only after verification, edit only the planned tests. Do not edit production or unplanned tests.
5. Run the targeted test through the cache-neutral runner to prove genuine Red, then pass the Red scope guard against the numbered snapshot.
6. Run the applicable official follow-up review. Normally this is the next three-reviewer iteration, with reviewer-owned JSON and the capacity-aware schedule, against only the disputed criteria before the normal `record_round`, aggregation, inspection, and `advance_phase` gates. Use the single focused-reviewer path only when the initial round and `red_review_gate.py initial` produced the exact compact-low eligibility artifact defined in Audit Integration.

A monitor that rejects step 2 only because the planned corrected content is absent has applied the post-edit reviewer check before its authorizing snapshot; re-run the pre-edit validation with this contract instead of editing around the gate.

Run every active-worktree targeted, collection, and full pytest command through the cache-neutral runner:

```bash
python scripts/tdd_snapshot.py run -- python -m pytest <pytest-args>
```

The runner disables pytest's cache provider and Python bytecode writes before the child starts, preserves the child exit status and output, and never deletes cache paths.

The guard authenticates the scope artifact against the same repository-relative path in `baseline_ref` before evaluating changes. It fails closed when the artifact is edited, deleted, malformed, outside the repository, reached through a symlink, missing from the baseline, or paired with conflicting semantic overrides. Change discovery includes tracked, renamed, deleted, and non-ignored untracked paths using NUL-safe Git records. Ignored untracked files are outside the guard's coverage; required phase files must be tracked in the baseline or non-ignored. Protected paths always take precedence over editable paths, and matching patterns are exact paths or terminal `/**` only.

The `pre_green` Red-exit snapshot is the pre-Green production baseline. `tdd_snapshot.py replay`
runs the original Red command in a detached worktree at that ref and
records its stable test identifier and failure classification alongside the
captured output. Use `--preserve-worktree` for a blocked run; `cleanup` removes
phase refs and preserved replay worktrees only after successful terminal
closeout.

### 2. Red

Main goal: produce the next failing test and nothing else.

The Start Gate has already required the monitor to check the proposed map and scope against the Red criteria, including clause/control coverage and exact evidence for every control exclusion, and to return a pass containing its stable delegated identity, delegation mechanism, the map digest, and test baselines before snapshot publication. Preserve that exact monitor-authored response in the Red artifact; the main agent must not author or repair it. If the map changes before the first test edit, return to the initial monitor gate and publish `pre_red` only after the corrected proposal passes. After a Red review has occurred, follow the authenticated numbered-round contract instead.

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

- run `python scripts/phase_guard.py --phase red --scope audits/<feature>_red_scope.json`; the guard derives tracked, untracked, rename, and deletion paths from the baseline ref
- confirm every mapped property control has a non-neutral asserted effect that would reject its named shortcut
- run `$review-with-multi-debate` with the Red claim from [phase_audits.md](phase_audits.md), following the reviewer-owned artifact and transition sequence in Audit Integration; the artifact must record every independently delegated reviewer's stable identity and mechanism, and self-authored reviewer files are invalid

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

- run `python scripts/phase_guard.py --phase green --scope audits/<feature>_green_scope.json`
- confirm no test files changed
- confirm the targeted red test now passes
- save the Green production diff for the later cumulative Refactor audit
- do not run `$review-with-multi-debate` at Green by default

### 4. Regression Check

Run the full available test suite after the green change. This is not optional.

If the suite is large, you may first run the closest package or component suite, but phase completion still requires the full available suite unless the environment makes that impossible.

Record the targeted and full-suite results for the later cumulative Refactor audit. Do not run `$review-with-multi-debate` for regression by default.

Compact transition: when the request map says `route: compact`, the deterministic Green gate and targeted test pass, one full regression, all repository-required type/static checks, and direct inspection of the production and test diffs must show no behavior, safety, type, or meaningful maintainability issue requiring a delta. Then record `audits/<feature>_refactor_noop.md` and `audits/<feature>_test_refactor_noop.md` and proceed to Documentation Follow-Up, skipping smell cycles, replay, Refactor/Test Refactor debates, and repeated full suites. Cosmetic or pre-existing findings do not force refactor. Any real production or test delta, uncertainty, failed gate, or high-risk behavior changes the route to `full` and continues through Sections 5-6 unchanged.

### Bounded Phase-State Recovery

<!-- bounded-phase-state-recovery -->
Use recovery only for a local owning-phase command whose accidental write can be proven by observing it inside one invocation. Do not apply it after an arbitrary failed guard: without a clean pre-command observation, provenance is ambiguous.

Invoke the deterministic wrapper from the repository root:

```bash
python <skill-dir>/scripts/phase_recovery.py \
  --phase <phase> \
  --scope audits/<feature>_<phase>_scope.json \
  --receipt <fresh-path-outside-repository>.jsonl \
  --cause accidental_phase_write \
  -- <owning-phase-command>
```

The runner authenticates the scope against its immutable `baseline_ref`, requires the initial guard to pass, records the real index tree and a Git worktree tree, runs the command without a shell, and evaluates the same scope again. Recovery is all-or-none and limited to disallowed paths which:

- existed as regular tracked files in the authenticated baseline;
- exactly matched that baseline immediately before the command;
- became modified or deleted during the wrapped command;
- are unambiguous under the scope classification; and
- are not under `audits/**`.

Before restoration, the runner writes an exclusive append-only JSONL receipt outside the repository. Its `recovery_planned` event records the authenticated baseline ref and commit, scope digest, pre/post worktree tree objects, unchanged index tree, child result digests, and exact baseline/violating objects for every path. Present violating bytes are also embedded as base64 so evidence does not depend on unreachable Git objects surviving garbage collection. It then rechecks the worktree and index for drift, restores the complete path set from the authenticated commit in one bounded Git operation, reruns the guard, and appends `recovery_completed`. The JSON stdout status is `recovered` only when the command and final guard pass; the owning phase may then continue. A failed child may still be cleaned up, but its original nonzero status is returned as `recovered_command_failed`.

Never pass `--cause accidental_phase_write` for a semantic requirement conflict or a planned cross-phase edit. Missing or mutated scope evidence, pre-existing violations, untracked or renamed paths, symlinks or other non-regular entries, Git-index changes, concurrent drift, ambiguous classification/provenance, existing receipt paths, reviewer-owned or other `audits/**` artifacts, and role, dependency, capacity, reviewer, or debate failures return `non_recoverable` without restoration. Move intentional work to its owning phase; keep every official Red, Refactor, and Test Refactor debate unchanged.

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
- run `python scripts/phase_guard.py --phase refactor --scope audits/<feature>_refactor_scope.json`
- audit with `$review-with-multi-debate` using the cumulative Refactor claim from [phase_audits.md](phase_audits.md)
- include the cumulative production diff from pre-Green to post-Refactor, the refactor-only diff, the request map, the Red audit result, the Green gate result, and regression results

### 6. Test Refactor

Start only after the cumulative production Refactor audit converges. Read
[test_refactor.md](test_refactor.md), inspect the Red tests
and directly shared test support, and record a no-op artifact when no
demonstrated test smell exists and the test diff is empty.

Test Refactor may edit only test-like paths. It must preserve the behavior map,
independent oracles, assertion strength, test selection, and required execution
boundaries. A missing case, wrong expectation, or changed boundary returns the
workflow to Red.

Before closing, run the `test_refactor` scope guard, targeted and full suites,
replay the original Red behavior against pre-Green production, and run the
mandatory Test Refactor debate using the claim in
[phase_audits.md](phase_audits.md).

If the test diff is empty and no demonstrated test smell exists, create a
no-op artifact, run the scope, collection, targeted, and full-suite checks, and
skip the multi-review debate. Any Test Refactor test change requires the
mandatory debate. Replay metadata must retain the stable test ID and failure
classification; use `--preserve-worktree` for blocked runs and remove preserved
worktrees and all feature phase refs during terminal `cleanup`.

### 7. Documentation Follow-Up

Only start this step after Red, Green, and regression, plus either the compact
no-op transition or production Refactor and Test Refactor, are done.

Allowed actions:

- update docs relevant to the completed code change
- keep doc edits narrow and implementation-aligned

Forbidden actions:

- editing tests
- editing production code
- using docs as a place to sneak in design changes that the code does not implement

Before closing documentation:

- run `python scripts/phase_guard.py --phase docs --scope audits/<feature>_docs_scope.json`
- record the docs artifact for final closeout
- do not run `$review-with-multi-debate` for docs by default

### 8. Final Closeout

Before finishing:

- confirm each mapped requirement has a passing test
- confirm every non-TDD requirement row has its must-exist artifact and acceptance evidence
- confirm the user-visible definition of done is satisfied end to end
- summarize any unresolved risks
- keep the final explanation short and oversight-friendly

Do not run a final `$review-with-multi-debate` by default. The final closeout should point to the Red audit, Green gate, regression result, and either the two compact no-op artifacts or the cumulative production Refactor and Test Refactor audits.

## Monitor Protocol

The monitor agent is separate on purpose. Its job is to stop phase bleed.

At each phase boundary:

The initial pre-Red boundary is the sole pre-publication check before the first Red. A numbered post-review correction uses the same pre-edit evidence rule defined in `post-review-correction-order`: inspect the correction plan, proposed map/scope, retained provenance, and current Git hash/status directly, without tests, `phase_guard.py`, corrected-content inspection, or baseline-ref resolution. Run the commands below only after the applicable snapshot exists.

1. Collect the changed file list for the phase.
2. Run:

```bash
python scripts/phase_guard.py --phase red --scope audits/<feature>_red_scope.json
python scripts/phase_guard.py --phase green --scope audits/<feature>_green_scope.json
python scripts/phase_guard.py --phase refactor --scope audits/<feature>_refactor_scope.json
python scripts/phase_guard.py --phase test_refactor --scope audits/<feature>_test_refactor_scope.json
python scripts/phase_guard.py --phase docs --scope audits/<feature>_docs_scope.json
```

3. If the guard fails, stop. Do not rationalize the violation. A command already wrapped under Bounded Phase-State Recovery may proceed only when that runner returns `recovered` after its final guard pass. Otherwise move the work into the correct phase. Lexical classification is only a default; a path with a semantic conflict must have an explicit override in the artifact, and the guard fails closed when it is absent.
4. Hand the phase artifact plus the claim to `$review-with-multi-debate` only for Red, production Refactor, and Test Refactor. Other phases record artifacts for those audits and final closeout.

Use [phase_contracts.md](phase_contracts.md) for the exact phase ownership rules and [phase_audits.md](phase_audits.md) for audit claims.

## Audit Integration

Each `$review-with-multi-debate` audit should hand off:

- the artifact for the phase
- the exact claim text from [phase_audits.md](phase_audits.md)
- the `feature_name`
- the phase label

Each debate artifact must record every actual independent reviewer identity and delegation mechanism returned by the backend used. Missing provenance or any self-authored reviewer file invalidates the debate and stops the phase.

The local gates verify consistency and unchanged bytes; they cannot authenticate every possible backend. Preserve the actual delegation return as run evidence. A matching self-authored identity/source string is not proof that delegation occurred.

<!-- reviewer-owned-debate-artifacts --> For the initial iteration, and for every normal follow-up iteration `M`, assign the three independently delegated reviewers `audit1`, `audit2`, and `audit3`. Each reviewer must itself write exactly one file and no other reviewer file:

- `audits/<feature>_<phase>_audit1_iterationM.json`
- `audits/<feature>_<phase>_audit2_iterationM.json`
- `audits/<feature>_<phase>_audit3_iterationM.json`

For Red, extend the loaded debate skill's top-level audit schema with these required ownership fields:

```json
{
  "reviewer_agent_id": "<stable-reviewer-identity>",
  "reviewer_source": "<delegation-mechanism>"
}
```

Use the stable identity returned by the actual delegation backend and the same nonempty mechanism name recorded in the role receipt. These fields are additions to, not replacements for, the debate skill's fields.

<!-- capacity-aware-reviewer-scheduling --> Give each reviewer its distinct debate-skill role, the common artifact and claim decomposition, an isolated prompt, the schema, and only its own exact current-iteration destination. For an initial iteration, do not include or ask a later reviewer to read a completed sibling's current-iteration output. Independence does not require simultaneous execution. Use no more simultaneous reviewers than the available concurrency or capacity limit permits; with one free reviewer slot, delegate and await `audit1`, then `audit2`, then `audit3`.

If delegation hits a capacity error, retain every valid reviewer-owned file already completed and allow any active reviewer to finish. Once that reviewer has terminated and capacity is available, retry only the missing assigned reviewer with a new distinct identity in the same iteration. Do not restart completed reviewers, overwrite their files, reuse or relabel another identity, or transcribe an opinion. If the bounded retry fails and no available authorized mechanism can provide the reviewer cohort, stop the phase and report the capacity blocker.

The main agent and monitor may supply the artifact, claim decomposition, exact destination, reviewer role, and schema, but must not transcribe a reviewer response, author its JSON, or accept a chat-only verdict. After all three Red reviewers finish, bind the receipt to each reviewer-owned file before running any debate transition:

```bash
python scripts/red_review_gate.py provenance \
  --role-receipt audits/<feature>_role_receipt.json \
  --iteration <M> \
  --output audits/<feature>_red_iteration<M>_provenance.json \
  audits/<feature>_red_audit1_iteration<M>.json \
  audits/<feature>_red_audit2_iteration<M>.json \
  audits/<feature>_red_audit3_iteration<M>.json
```

The gate requires schema `2`, three distinct reviewer identities separate from the monitor, matching identity/source fields and filenames, and strict audit content. Its output binds the receipt and every audit by SHA-256. A rejected gate keeps Red locked; regenerate an invalid audit only through its owning reviewer.

Then use the scripts from the loaded `review-with-multi-debate` skill directory to verify all expected files exist:

```bash
python <review-skill-dir>/scripts/validate_audit_transition.py record_round \
  --feature-name <feature> --phase <phase> --iteration <M> --audit-dir audits
```

Read and validate each reviewer JSON against the debate skill's contract, including metadata, criterion fields, allowed verdicts, evidence requirements, and counterevidence. Regenerate a malformed file through its owning reviewer at the same iteration; the main agent or monitor must not repair it. Then aggregate deterministically:

```bash
python <review-skill-dir>/scripts/aggregate_audits.py \
  audits/<feature>_<phase>_audit1_iterationM.json \
  audits/<feature>_<phase>_audit2_iterationM.json \
  audits/<feature>_<phase>_audit3_iterationM.json \
  --output audits/<feature>_<phase>_iterationM_summary.json
```

Then read the three reviewer JSON files and deterministic summary. The main agent must explicitly check every blocking criterion's verdict and evidence, all counterevidence, disputed criteria, and convergence; the aggregator does not make those judgments. Only after those checks pass, run:

```bash
python <review-skill-dir>/scripts/validate_audit_transition.py advance_phase \
  --feature-name <feature> --from-phase <phase> --to-phase <next-phase> \
  --iteration <M> --audit-dir audits
```

Do not create the next-phase scope or snapshot before `advance_phase` passes. If a blocking criterion does not converge, iteration `M + 1` keeps all three reviewer identities and writes three new correctly named files that address only the disputed criteria; repeat `record_round`, aggregation, inspection, and `advance_phase`. Never overwrite or reuse a prior iteration file. Stop at the debate skill's hard limit rather than forcing consensus.

After `advance_phase` passes, provide the unchanged provenance output to the next `tdd_snapshot.py create` with `--provenance ... --review-iteration <M>`; snapshot publication verifies that this is the latest recorded iteration, re-hashes the staged receipt/provenance/audits, and rejects any intervening mutation.

<!-- risk-scaled-focused-red-review -->
### Compact Low-Risk Focused Red Review

The initial Red iteration always uses the three-reviewer workflow above. After `record_round`, aggregation, and explicit evidence inspection, do not weaken or bypass a passing gate. When the initial round instead has one unanimous blocking failure, test the narrow exception with:

```bash
python scripts/red_review_gate.py initial \
  --route compact --risk-tier low \
  --role-receipt audits/<feature>_role_receipt.json \
  --output audits/<feature>_red_focused_eligibility.json \
  audits/<feature>_red_audit1_iteration1.json \
  audits/<feature>_red_audit2_iteration1.json \
  audits/<feature>_red_audit3_iteration1.json
```

Eligibility requires three strictly valid reviewer-owned audits whose receipt-bound owners unanimously fail the same single blocking criterion and pass the complete unchanged remainder. Insufficient evidence, counterevidence, open questions, disputes, criterion drift, any other failure, or any route/risk other than compact-low returns `normal_three_reviewer_follow_up` and writes no eligibility output.

An eligible correction still follows the numbered-round monitor, append-only snapshot, test-only edit, genuine Red, and Red scope-guard sequence. Then delegate one new independent reviewer, distinct from the monitor and all three initial reviewers, to write only `audits/<feature>_red_focused_iteration2.json` and review only the frozen repaired criterion. Gate it with:

```bash
python scripts/red_review_gate.py focused \
  --eligibility audits/<feature>_red_focused_eligibility.json \
  --role-receipt audits/<feature>_role_receipt.json \
  --focused-audit audits/<feature>_red_focused_iteration2.json \
  --focused-reviewer-agent-id <stable-focused-reviewer-identity> \
  --reviewer-source <delegation-mechanism> \
  --output audits/<feature>_red_focused_gate.json
```

Only a receipt-hash-bound, strictly valid, evidence-backed pass on that exact criterion returns `advance_green`. Every malformed, unresolved, mismatched, reused-identity, or non-passing result writes no focused output and returns to the normal three-reviewer follow-up. This exception changes review multiplicity only; all phase, Green, regression, static, materialization, control-interaction, Refactor, Test Refactor, and high-risk rules remain unchanged.

The focused output is also its iteration-2 provenance artifact: it binds the role receipt, eligibility artifact, focused reviewer identity/source, and focused audit by path and SHA-256. Publish `pre_green` only with both branches of evidence:

```bash
python scripts/tdd_snapshot.py create \
  --feature <feature> --phase pre_green \
  --roles audits/<feature>_role_receipt.json \
  --provenance audits/<feature>_red_iteration1_provenance.json \
  --focused-provenance audits/<feature>_red_focused_gate.json \
  --review-iteration 2
```

Snapshot publication re-hashes the staged initial receipt/audits/provenance and the focused eligibility/audit/gate artifacts. Without `--focused-provenance`, iteration 2 must use the normal three-reviewer provenance shape.

Mandatory debate phases:

- `red`
- `refactor` on the full route
- `test_refactor` on the full route when its rules require debate

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
- Test Refactor behavior map, test diff, replay evidence, and full suite results

For Red and cumulative production Refactor audits, also include:

- the chosen execution path and the observable evidence that proves the path crosses the claimed boundary
- if lower-level tests are claimed to be sufficient, the `strace` or `dtruss` output that shows no high-risk boundary was crossed on the minimal execution path
- if the path does not prove traversal of the risky boundary, red is incomplete even if the test fails as expected

## Resources

- Use [../scripts/trace_boundary_check.py](../scripts/trace_boundary_check.py) to run `strace` or `dtruss` on a minimal execution path and emit JSON evidence about process, network, and filesystem boundary crossings.
- Open [phase_contracts.md](phase_contracts.md) when you need exact edit-boundary rules.
- Open [phase_audits.md](phase_audits.md) when preparing a mandatory Red, cumulative production Refactor, or Test Refactor audit with `$review-with-multi-debate`.
- Read [test_refactor.md](test_refactor.md) before changing tests after production Refactor.
- Use [../scripts/phase_guard.py](../scripts/phase_guard.py) for the monitor agent's scope check.
- Use [../scripts/phase_recovery.py](../scripts/phase_recovery.py) only for the bounded, command-proven accidental-write contract above.
- Use [../evals/evals.json](../evals/evals.json) to benchmark whether the skill triggers on the right work and stays lean.
