# Intent

Define the smallest enforceable phase boundaries for `fast-multi-agent-tdd`.

## Before TDD

Requirement re-check, mixed-work classification, and path preflight happen before phase ownership begins.

- Classify each requirement as executable, guidance, rubric, data, research, or result work.
- Put only executable behavior under Red-Green-Refactor.
- Keep required non-code artifacts outside TDD phases; do not use TDD ordering to delay them.
- Record planned paths and semantic roles before Red.
- Record `route: compact|full` and concrete reasons before any snapshot or Red edit. Compact eligibility is limited to bounded, deterministic, local CLI, process, or filesystem behavior, including config-driven materialization, with no network, GPU, concurrency, nondeterminism, external service, unrelated persistent side effect, or other high-risk behavior; uncertainty means `full`.
- Resolve lexical collisions before edits. A human-approved semantic classification recorded in the requirement map overrides the default path heuristic for that exact path or bounded subtree.

## Role Provenance

- Before any snapshot or Red edit, an available authorized delegation mechanism must start the dedicated monitor in an independent context and return a stable identity. Native worker tools, task APIs, MCP servers, and installed agent CLIs or APIs are valid examples, not a closed list. If one interface is unavailable, inspect the current environment and try another mechanism before declaring the role unavailable. <!-- initial-pre-red-monitor-validation --> Before the intended `pre_red` ref exists, the monitor validates the proposed request map, route, path classifications, Red scope, map digest, and planned test-file Git hashes/status directly. It does not run tests, `phase_guard.py`, or require the intended baseline ref to resolve. A finding is corrected and rechecked inside this initial gate.
- Each mandatory debate artifact records every independently delegated reviewer's stable identity and the actual delegation mechanism.
- <!-- reviewer-owned-debate-artifacts --> Each delegated reviewer writes exactly one correctly named audit for its assigned identity and iteration. Red audits extend the loaded review schema with the stable `reviewer_agent_id` and actual `reviewer_source`. Parent/monitor transcription, self-authored reviewer JSON, chat-only verdicts, missing expected files, and overwritten earlier iterations are invalid. The initial iteration and normal follow-ups run `red_review_gate.py provenance` before the loaded review skill's three-file `record_round`, deterministic aggregation plus explicit blocking/evidence/counterevidence inspection, and `advance_phase`; normal later iterations write three new files targeted only to disputed criteria.
- <!-- capacity-aware-reviewer-scheduling --> Reviewer independence requires distinct stable identities, assigned roles, isolated prompts, and reviewer-owned files; it does not require simultaneous execution. Keep concurrent reviewer count within the available capacity limit; with one free reviewer slot, delegate and await `audit1`, then `audit2`, then `audit3`. On a capacity error, preserve completed valid files, await any active reviewer, and retry only the missing distinct reviewer once in the same iteration when capacity is free. Never restart a valid reviewer, reuse or relabel an identity, or transcribe its output; stop if the bounded retry still fails without an occupied debate reviewer slot.
- <!-- risk-scaled-focused-red-review --> Only after a valid three-reviewer initial Red round may `red_review_gate.py` admit one focused follow-up. Admission requires `route=compact`, `risk_tier=low`, receipt-bound reviewer ownership, one identical unanimous blocking failure, all other criteria passing unchanged, and no insufficient evidence, counterevidence, question, dispute, or other failure. The correction still requires the normal monitor, numbered snapshot, test-only edit, genuine Red, and scope guard. One newly delegated identity then owns `audits/<feature>_red_focused_iteration2.json`, reviews only the frozen criterion, and must provide a strict evidence-backed pass through the focused gate. That gate output binds the receipt, eligibility, reviewer identity/source, and audit. The `pre_green` snapshot requires the initial `--provenance`, focused output as `--focused-provenance`, and `--review-iteration 2`. Any invalid state, or any medium/high/full case, retains the normal three-reviewer follow-up.
- Main-agent or otherwise self-authored monitor/reviewer evidence is invalid. Exhaust the available authorized delegation mechanisms before stopping for an unavailable role.
- The main agent writes `audits/<feature>_role_receipt.json` only from actual delegation results. Every snapshot create requires `--roles` and validates schema `2`, the exact feature, `route: compact|full`, a nonempty opaque monitor identity, and a nonempty mechanism source before publishing a ref. Receipt shape alone does not prove independence; the recorded values must come from the real handoff.
- <!-- initial-pre-red-snapshot-publication --> Only after the initial monitor pass does the main agent create and verify the first snapshot, `pre_red`; Red stays locked until both operations succeed. The Red-exit snapshot is `pre_green`; it and every later `pre_<next-phase>` snapshot also require nonempty distinct Red reviewer identities, separation from the monitor, a nonempty reviewer delegation source, and `--provenance <accepted-provenance> --review-iteration <M>`. Snapshot creation requires the latest recorded iteration and re-hashes the staged role receipt, provenance artifact, and every bound audit before publishing.
- <!-- post-red-numbered-rounds-only --> A map or test correction required by a completed Red review opens a numbered Red round before any corrected test edit. After revising the map and scope and receiving a fresh monitor gate, create `--phase pre_red --round N --provenance <accepted-provenance> --review-iteration <N-1>`; round `N > 1` publishes append-only `pre_red_round_<N>` and retains the prior delegated Red reviewer identities. An initial monitor finding is not a numbered round. The new Red scope points to that ref and may retain or strengthen prior protections, never weaken them.
- <!-- post-review-correction-order --> The numbered-round monitor validates the precise correction plan, updated map and scope, retained prior reviewer provenance, and current pre-edit Git hashes/status for every planned test. Because the intended numbered ref is not published yet, it checks the expected ref name without resolving it and must not require the corrected test content to exist. After its pass, publish and verify the append-only numbered snapshot; only then edit only the planned tests. The targeted test must prove genuine Red and the Red scope guard must pass before the applicable official follow-up verifies the corrected content and evidence against only its authorized criteria. Normally that follow-up is the next three-reviewer iteration; only the exact compact-low eligibility permits one focused reviewer instead.
- Invalid, missing, feature-mismatched, or self-authored-source receipts fail closed. Keep the next phase locked after receipt validation or snapshot creation fails. A formatting error may be corrected only from the original delegation result and revalidated; a snapshot may be retried only when no ref was published. Missing or ambiguous provenance, partial publication, and an unexpected existing phase ref remain terminal for that transition.

## Dynamic Scope Artifact

Each phase publishes the scope for the next phase under `audits/`:

```json
{
  "schema": 1,
  "feature": "stripe_webhook",
  "phase": "green",
  "baseline_ref": "refs/tdd/stripe_webhook/red",
  "protected": ["tests/**", "features/**", "docs/**", "audits/**"],
  "editable": [],
  "semantic_overrides": {"src/tests/runtime.py": "prod"}
}
```

At the initial pre-Red transition, write the proposed artifact, obtain the
monitor pass without resolving its future ref, then capture the tracked and
untracked worktree into a Git snapshot so the immutable baseline contains the
approved artifact. At later transitions, write the next-phase artifact first,
then capture it. Record the baseline ref and commit in the phase output.
The guard treats the baseline ref as authoritative, verifies the current scope
bytes at the same repository-relative path before parsing, and fails closed on
mutation, deletion, malformed content, missing baseline copy, symlink aliases,
or out-of-repository paths. It includes both sides of renames and deleted paths,
normal untracked files, and ignored untracked files using NUL-safe Git status.
Ignored files are enforceable changes, not a hiding place. Overlapping semantic
override patterns with different classifications are conflicts; exact paths and
terminal `/**` are the only supported pattern forms. Production phases can omit
`editable`; Test Refactor and Documentation must include it. Protected paths
always win over editable paths.

Phase refs are append-only: creating an existing `refs/tdd/<feature>/<phase>`
is an error and never overwrites the prior snapshot. Replay worktrees and refs
are retained for explicitly preserved blocked runs and removed by feature
cleanup after terminal closeout.

Active-worktree targeted, collection, and full pytest commands run through
`python scripts/tdd_snapshot.py run -- python -m pytest ...`. The runner sets
`PYTHONDONTWRITEBYTECODE=1` and disables pytest's cache provider before the
child starts, returns the child output/status, and does not delete caches.

The guard accepts exact paths and bounded terminal `/**` patterns only. It
rejects malformed paths, missing or mismatched baseline refs, invalid artifacts,
and unresolved semantic conflicts. Lexical classification is a default safety
check, not permission to guess when a path's location and filename imply
different roles.

## Recoverable State Violation Contract

<!-- bounded-phase-state-recovery -->
An accidental filesystem violation is recoverable only through the owning-command wrapper documented in [workflow.md](workflow.md). A successful pre-command guard and matching baseline/pre-command Git tree entries establish the starting state; the wrapper's post-command tree establishes the bounded mutation window. The recovery set must contain every disallowed path and every member must be a tracked regular baseline file with unambiguous classification. Recovery is invalid when any member is untracked, renamed, non-regular, baseline-dirty, under `audits/**`, or paired with real-index or later worktree drift.

The helper writes a fresh external JSONL receipt before mutation, restores the all-or-none set from the scope's resolved authenticated baseline commit, and reruns the same guard. Only `status: recovered` with `guard_status: pass` reopens the owning phase. `recovered_command_failed` preserves the cleanup but retains the child's failure, and `non_recoverable` never authorizes continuation. This contract cannot classify intent: known semantic requirement conflicts and planned cross-phase work must not be labelled `accidental_phase_write`. Reviewer artifacts, role provenance, dependencies, capacity, reviews, and debates remain outside filesystem recovery and retain their existing stop rules.

## Phase Ownership

### Request Map

- Main output: unified Scope & Evidence Plan in the request-map artifact, test seam choice, feature label
- Compact filter/selector plans must distinguish compatible controls from mutually exclusive strategies. Every compatible control that materially changes selection needs combined evidence with the new behavior at a binding non-neutral value; existing evidence counts only when it crosses and asserts both effects.
- Allowed edits: docs, notes, planning artifacts
- Forbidden edits: tests, production code

### Red

- Main output: the next failing test
- Scope policy: phase-kind checks plus the protected paths in the Red artifact
- Allowed edits:
  - files under `tests/`
  - files under `__tests__/`
  - files matching `*.test.*`
  - files matching `*.spec.*`
  - files matching `*.feature`
  - short docs or notes explaining the test seam
- Forbidden edits:
  - production code
  - config churn unrelated to making the test runnable

### Green

- Main output: the smallest production change that makes red pass
- Scope policy: phase-kind checks plus protected paths; production files remain flexible for newly discovered modules
- Allowed edits:
  - production code
  - minimal runtime wiring required by the failing test
- Forbidden edits:
  - any test file
  - any feature file
  - broad refactors

### Regression

- Main output: targeted plus full-suite test evidence
- Allowed edits: none, unless the run exposes a real issue that forces a return to red or green
- Forbidden edits:
  - silent fixes during the check itself

### Compact Transition

- After the Green gate, targeted pass, one full regression, repository-required type/static checks, and direct inspection show no required production or test delta, write the production and test no-op artifacts and continue to Documentation.
- Skip smell cycles, replay, Refactor/Test Refactor debates, and repeated full suites. Cosmetic or pre-existing findings do not force refactor.
- Any real delta, uncertainty, failed gate, or high-risk behavior selects the unchanged full Refactor and Test Refactor phases.

### Refactor

- Main output: cleaner production code with behavior held constant
- Scope policy: phase-kind checks plus protected paths; production files remain flexible for cumulative cleanup
- No-op rule: if no cleanup is needed, record that inspection in the Refactor artifact and do not invent code churn
- Allowed edits:
  - production code
- Forbidden edits:
  - any test file
  - any feature file
  - doc-like files such as `README.md`, `.md`, `.rst`, or `.txt`
  - new behavior disguised as cleanup

### Test Refactor

- Main output: clearer tests with the Red specification and execution boundaries preserved
- Scope policy: phase-kind checks, protected paths, and the explicit `editable` list of Red tests and directly shared test support
- No-op rule: record inspection and do not invent test churn when no demonstrated smell warrants change
- Allowed edits:
  - test-like paths selected in the request map
  - directly shared test support under a test-like path
- Forbidden edits:
  - production, documentation, runtime configuration, or test-selection files
  - new behavior, changed expectations, weakened assertions, silent deselection, skips, or `xfail`
  - replacing a required high-risk boundary with a lower-level mock
- Return-to-Red rule: stop when the work reveals a missing case, wrong oracle, changed boundary, or requirement conflict

### Documentation

- Main output: documentation that matches the already-completed code change
- Scope policy: documentation kind, protected paths, and the explicit `editable` documentation list
- Allowed edits:
  - doc-like files such as `.md`, `.rst`, `.txt`, or files under `/docs/`
- Forbidden edits:
  - production code
  - any test file
  - design churn unrelated to the completed implementation

### Final

- Main output: closeout that cites the Red audit, Green gate, regression check, either both compact no-op artifacts or the full-route Refactor audits, and the docs artifact when docs were updated
- Allowed edits: none
- Forbidden edits: any test, production, or documentation changes during closeout

## File Classification Heuristics

Use these as the default monitor rules:

- test-like:
  - path contains `/tests/`
  - path contains `/__tests__/`
  - basename contains `.test.`
  - basename contains `.spec.`
  - suffix is `.feature`
- doc-like:
  - suffix is `.md`, `.rst`, or `.txt`
  - path contains `/docs/`
- everything else is treated as production-like unless a human explicitly overrides it

If a path cannot be classified confidently, the monitor should mark it ambiguous and ask for a human decision instead of guessing.

Do this preflight before Red, not after a passing Green implementation exposes the collision.
