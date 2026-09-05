---
name: fast-multi-agent-tdd
description: Use when the user explicitly wants executable feature or bug-fix behavior delivered under strict Red-Green-Refactor with requirement re-checking, a dedicated monitor, mandatory Red, cumulative production Refactor, and Test Refactor debates, deterministic Green gates, and regression checks. Apply TDD only to executable behavior; do not use it for Markdown, SKILL.md, AGENTS.md, rubrics, documents, data curation, research evaluation, or review/diagnosis-only work.
---

# Fast Multi Agent TDD

## Stop: Mandatory Start Gate

Before any test or production edit, test run, `apply_patch`, or exploration command that can generate files, enter this gate and complete its steps in order. While the gate is open, the only permitted writes are the request map, role receipt, required scope artifact, and `pre_red` snapshot:

1. Save `audits/<feature>_request_map.md` with `route: compact|full` after the requirement re-check and path preflight.
2. **Delegate the dedicated monitor through any available, authorized mechanism that gives it an independent context and returns a stable identity. Native worker tools, task APIs, MCP servers, and installed agent CLIs or APIs are all valid; no operation name is privileged. If a candidate is unavailable, inspect the interfaces exposed in the current environment and try another authorized delegation mechanism. The handoff must include the absolute request-map path, the absolute `references/phase_contracts.md` path, and the active project cwd.**
3. Write `audits/<feature>_role_receipt.json` only from the delegation result. Record the returned identity verbatim and a compact name for the mechanism used. For `pre_red`, use exactly this contract; replace the four angle-bracket values, keep the field name `monitor_agent_id` (not `monitor`), and do not add reviewer fields yet:

   <!-- pre-red-role-receipt-contract -->
   ```json
   {
     "schema": 2,
     "feature": "<feature>",
     "route": "<compact|full>",
     "monitor_agent_id": "<stable-monitor-identity>",
     "monitor_source": "<delegation-mechanism>"
   }
   ```
   <!-- /pre-red-role-receipt-contract -->

4. Write the proposed Red scope artifact. Its `baseline_ref` must be `refs/tdd/<feature>/pre_red`, never `HEAD`, even though that intended ref does not exist yet.
5. <!-- initial-pre-red-monitor-validation --> Ask the dedicated monitor to validate the proposed request map, map digest, route, planned path classifications, Red scope, and planned test-file Git hashes/status. This initial check must not run tests, `phase_guard.py`, or require the intended `baseline_ref` to resolve. If the monitor finds a defect, correct the proposed map or scope and have the same dedicated monitor recheck it inside this initial gate; do not open or number a Red round. Receive the monitor-authored pre-Red gate pass before continuing.
6. <!-- initial-pre-red-snapshot-publication --> Only after that pass, run `python scripts/tdd_snapshot.py create --feature <feature> --phase pre_red --roles audits/<feature>_role_receipt.json` and verify its returned ref and commit. Red unlocks only when both the monitor pass and snapshot publication succeed.

Test execution begins only after step 6 through the cache-neutral snapshot runner.

Until step 6 succeeds: do not edit tests or production, run tests, or perform another write-capable action. Self-authored monitor, role, reviewer, or snapshot evidence is invalid. Do not stop merely because one delegation interface is absent. A receipt formatting error may be corrected only from the original delegation result and revalidated. A snapshot invocation may be retried only when it published no ref; never overwrite an existing phase ref. Stop when no available authorized mechanism can provide an independent role with a stable identity, provenance is missing or ambiguous, a phase ref already exists unexpectedly, or the monitor gate cannot pass.

Local validators prove internal consistency and immutability of recorded provenance, not the authenticity of every possible backend. Preserve the actual delegation return in the run evidence and never infer a successful handoff from self-authored receipt fields alone.

## Sequential Phase Controller

Follow the phases in order. Before acting in a phase, read its section in [references/workflow.md](references/workflow.md) and the linked specialized reference. Do not enter the next phase until the current gate passes.

### 0. Requirement Re-check and Request Map

Read `Overview`, `Trigger Conditions`, `Core Rules`, and Workflow sections 0-1 in [references/workflow.md](references/workflow.md), plus [references/phase_contracts.md](references/phase_contracts.md). Keep only executable behavior inside TDD, define the smallest end-to-end slice and done conditions, classify `compact|full`, preflight path semantics, and save the request map. Then immediately execute the mandatory start gate above.

### 1. Start Gate

Execute the six gate steps above without interleaving edits, test runs, or other write-capable actions beyond the named gate artifacts and their monitor-required corrections. The main agent implements; the delegated monitor never edits files. Do not delegate parallel implementers.

### 2. Red

Read Workflow section 2 and [references/phase_audits.md](references/phase_audits.md). Edit tests only, prove the mapped risky boundary with a genuine failing test, pass the Red scope guard, and complete the mandatory Red debate. Record the stable identities and delegation mechanism returned for the reviewers, run the provenance gate, and pass its output through `--provenance` with the matching `--review-iteration` when creating the append-only `pre_green` Git-ref snapshot. <!-- post-red-numbered-rounds-only --> A correction required by a completed Red review opens a new authenticated `pre_red_round_<N>` and retains the prior reviewer provenance; an initial monitor correction does not. Never overwrite an earlier ref.

<!-- post-review-correction-order --> At that numbered round's pre-edit boundary, the monitor validates the precise correction plan, updated map and scope, retained prior reviewer provenance, and current pre-edit Git hashes/status of every planned test. It must not require the corrected test content to exist before the snapshot that authorizes the edit. After the monitor pass, publish and verify the append-only numbered snapshot `pre_red_round_<N>` with the latest accepted provenance artifact and `--review-iteration <N-1>`; only then edit only the planned tests. Run the targeted test to prove genuine Red and pass the Red scope guard before the applicable follow-up verifies the correction. Normally that follow-up is the next three-reviewer iteration; only the exact compact-low eligibility below permits one focused reviewer instead.

<!-- reviewer-owned-debate-artifacts --> The initial Red debate follows the loaded review skill's three-reviewer contract, extended here with `reviewer_agent_id` and `reviewer_source` in every audit. Each independently delegated reviewer writes exactly one `audits/<feature>_red_auditN_iteration1.json` with its assigned `auditN`; parent/monitor transcription and chat-only verdicts are invalid. Normal follow-up iterations retain that contract.

<!-- risk-scaled-focused-red-review --> One exception applies after the initial round: for `route=compact`, `risk_tier=low`, `scripts/red_review_gate.py initial` may freeze exactly one repaired blocking criterion only when all three valid reviewer-owned audits fail that same criterion, pass every other criterion, and contain no insufficient evidence, counterevidence, open question, dispute, changed criterion, or other failure. The normal correction monitor, numbered snapshot, test-only edit, genuine Red run, and Red scope guard remain mandatory. After them, exactly one newly delegated reviewer, distinct from the monitor and all initial reviewers, writes `audits/<feature>_red_focused_iteration2.json` and reviews only the frozen criterion. `red_review_gate.py focused` must validate the unchanged receipt and eligibility hash, reviewer provenance, strict audit schema, structured evidence, and a clean pass before returning an `advance_green` artifact. Create `pre_green` with the initial-round `--provenance`, this artifact as `--focused-provenance`, and `--review-iteration 2`. Any invalid or ineligible state, including `full`, medium risk, or high risk, uses the normal three-reviewer follow-up.

<!-- capacity-aware-reviewer-scheduling --> Reviewer independence requires three distinct identities with their assigned roles, isolated prompts, and reviewer-owned files; it does not require simultaneous execution. Keep reviewer execution within the available concurrency or capacity limit. When only one reviewer slot is free, delegate and await `audit1`, then `audit2`, then `audit3`. A capacity error does not invalidate a completed reviewer-owned file or justify interrupting an active reviewer: wait for the active reviewer to finish, then retry only the missing distinct reviewer in the same iteration. If no available authorized mechanism can run the reviewer cohort after the bounded retry, stop. Never replace the missing reviewer by reusing an identity, relabeling a file, or parent/monitor transcription.

Before leaving Red, run `red_review_gate.py provenance` to bind the receipt to the three reviewer-owned audit files and their hashes. Then run the review skill's `record_round`, deterministic aggregator, and inspect every initial reviewer file for blocking verdicts, evidence, and counterevidence. Run `advance_phase` when the blocking criteria pass. Pass the unchanged provenance artifact and its iteration to the next snapshot; `tdd_snapshot.py` requires the latest review iteration and re-hashes the staged receipt, provenance, and audits before publishing the ref. A normal later iteration repeats the three-reviewer sequence and provenance gate for only the disputed criteria; the exact compact-low exception instead requires the focused gate above. Missing, stale, malformed, non-converged, or unowned evidence stops Red or routes to normal three-reviewer follow-up.

### 3. Green

Read Workflow section 3. Edit production only and make the smallest change that passes the Red test. Close with the deterministic Green gate: authenticated scope, no test edits, targeted pass through the cache-neutral snapshot runner, and saved production diff. Green has no debate by default.

### 4. Regression Check

Read Workflow section 4. Run the full available suite after every code change, plus repository-required type/static checks, without editing files during the check. A failure returns to the owning phase.

<!-- bounded-phase-state-recovery -->
When an owning-phase command may accidentally touch a disallowed path, run it through `scripts/phase_recovery.py` with the authenticated phase scope, the explicit cause `accidental_phase_write`, and a new receipt path outside the repository. The helper may continue the phase only when the pre-command guard passed, every violating path was a baseline-clean tracked regular file, the command alone produced the violation, the Git index did not change, evidence was durably recorded before one exact restore, and the same guard passes afterward. Untracked or renamed paths, `audits/**`, ambiguous classifications or provenance, semantic requirement conflicts, reviewer-owned artifacts, and role, dependency, capacity, review, or debate failures stop unchanged. Read the bounded recovery contract in [references/workflow.md](references/workflow.md) before invoking it.

### 5. Production Refactor

Read Workflow section 5. On the `compact` route, use the documented no-op transition only when all eligibility and no-delta checks pass. On the `full` route, edit production only, preserve behavior, guard the cumulative production diff from pre-Green, rerun regression, and complete the mandatory cumulative Refactor debate.

### 6. Test Refactor

Read Workflow section 6 and [references/test_refactor.md](references/test_refactor.md). Start only after the production Refactor gate. Test Refactor may edit only test-like paths and must preserve behavior, independent oracles, assertion strength, selection, and required boundaries. Run the scope guard plus targeted and full suites; any test change requires the mandatory Test Refactor debate. A changed oracle, boundary, or behavior returns to Red.

### 7. Documentation Follow-Up

Read Workflow section 7. Update only relevant docs after all code and test phases close, use the explicit docs scope, and do not alter behavior.

### 8. Final Closeout

Read Workflow section 8. Confirm every mapped requirement and non-TDD artifact, cite the Red audit, Green gate, regression evidence, route-specific Refactor evidence, and docs artifact, then run terminal snapshot cleanup. Do not make edits during closeout.

## Invariants

- New or conflicting behavior returns to Red; a conflicting user instruction requires later explicit confirmation before resuming.
- Tests change only in Red or Test Refactor. Production changes only in Green or production Refactor. Docs change only after both refactor stages close.
- Mandatory monitors, reviewers, and debates cannot be replaced by self-review or matching prose. Exhaust available authorized delegation mechanisms before treating a role as unavailable; unavailable or non-converged roles then stop the phase.
- Phase scope comes from authenticated, append-only Git refs plus scope artifacts. Keep both the ref and commit metadata; SHA-only evidence does not replace the ref.
- User resource limits override defaults. The main agent owns implementation; the monitor owns enforcement and audit handoff only.

## Resources

- [references/workflow.md](references/workflow.md): complete rules, artifacts, monitor protocol, and audit handoff; read the relevant section before each phase.
- [references/phase_contracts.md](references/phase_contracts.md): exact edit ownership, role provenance, dynamic scope, and compact/full transition rules.
- [references/phase_audits.md](references/phase_audits.md): exact mandatory audit claims.
- [references/test_refactor.md](references/test_refactor.md): Test Refactor decision and evidence contract.
- [scripts/tdd_snapshot.py](scripts/tdd_snapshot.py): authenticated Git-ref snapshots, replay, cache-neutral test runner, and cleanup.
- [scripts/phase_guard.py](scripts/phase_guard.py): phase-scope enforcement.
- [scripts/phase_recovery.py](scripts/phase_recovery.py): bounded command wrapper for authenticated accidental phase-state recovery.
- [scripts/trace_boundary_check.py](scripts/trace_boundary_check.py): process, network, and filesystem boundary evidence.
