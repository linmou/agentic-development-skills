---
name: review-with-multi-debate
description: Use when an artifact must be audited against a claim by multiple independent reviewers, each review must be saved to `audits/...json`, and disagreement should trigger targeted follow-up rounds until convergence or a hard stop.
---

# Review With Multi Debate

## Overview

Use this skill when a single review is too brittle and you need a structured multi-review audit instead. The job is not to create theatrical debate. The job is to decompose the claim into auditable criteria, collect independent evidence-bound reviews, and recurse only on disputed points.

## Trigger Conditions

Use this skill when the user asks for any of the following:

- multiple reviewers to assess whether an artifact meets a claim
- audit files written to `audits/<feature_name>_<phase>_auditN_iterationM.json`
- iterative debate, recursive review, or disagreement resolution
- convergence rules for claim checking, requirement audits, or evidence-based review

Do not use this skill for:

- simple summaries
- one-pass reviews where disagreement handling is unnecessary
- open-ended brainstorming without a concrete artifact and claim

## Core Rule

Do not ask reviewers to argue about one big fuzzy verdict. First convert the claim into a small set of checkable criteria. Convergence is measured per criterion, then rolled up into an overall status.

If the claim cannot be decomposed into clear criteria, stop and rewrite the claim before launching reviewers.

## Workflow

### 1. Normalize the input

Inputs (full field list in [references/call-contract.md](references/call-contract.md)):

- `artifact`
- `claim`
- optional `feature_name`, derived from the claim when absent
- optional `phase`, default `review`: an opaque label for file names; never branch on it
- optional `evidence`, `require_reviewer_provenance`, `audit_dir`, `caller_tag`

Write a short claim decomposition before running reviewers:

- 3 to 7 criteria
- each criterion must be checkable with a `pass`, `fail`, or `insufficient_evidence` verdict
- identify which criteria are blocking

If the user did not provide a `feature_name`, derive a short snake_case or kebab-case label from the claim.

Every reviewer receives the same criterion set and must return exactly its criterion IDs, text, and blocking flags. The aggregator and phase gate reject missing, extra, renamed, or redefined criteria.

### 2. Keep audit artifacts out of Git

Before writing audit files in a Git repository:

- resolve the repository-local exclude file with `git rev-parse --git-path info/exclude`
- if `git check-ignore` does not already ignore a planned audit path, add a rule for `audit_dir` (default `/audits/`, relative to the repository root) to that exclude file
- preserve all existing exclude rules
- verify a planned audit path is ignored with `git check-ignore`
- if any audit file is already tracked, stop and report it; do not alter the Git index without user approval

Skip this step when the artifact is outside a Git repository.

### 3. Run round 1 reviewers in parallel

Launch three independent reviewers in parallel. The important part is reviewer separation and structured output.

Reviewer roles:

- `audit1`: strict verifier, biased toward rejecting unsupported claims
- `audit2`: charitable verifier, biased toward accepting only explicit evidence
- `audit3`: contradiction hunter, focused on disconfirming evidence and scope mismatches

Each reviewer gets:

- the artifact
- the claim
- the claim decomposition
- the reviewer JSON contract below

When tests are relevant to the claim, include existing test output or its path for each relevant component in the reviewer handoff. Reviewers distinguish passes, expected failures, unrelated failures, and tests known not to have run. If a result is missing, mark execution unverified; do not infer from test source that a test ran or did not run.

Each reviewer writes exactly one file:

- `audits/<feature_name>_<phase>_audit1_iteration1.json`
- `audits/<feature_name>_<phase>_audit2_iteration1.json`
- `audits/<feature_name>_<phase>_audit3_iteration1.json`

Before advancing from reviewer execution, validate that all three expected
result files exist:

```bash
python <skill_dir>/scripts/validate_audit_transition.py record_round \
  --feature-name <feature_name> \
  --phase <phase> \
  --iteration <iteration> \
  --audit-dir <audit_dir>
```

The validator is a coarse artifact-presence gate. It does not judge evidence
quality, blocking status, counterevidence, or convergence.

Every criterion verdict must cite evidence or explicitly record missing evidence. No unsupported verdicts.

Reviewer JSON contract:

```json
{
  "feature_name": "replace-me",
  "phase": "review",
  "iteration": 1,
  "reviewer_id": "audit1",
  "claim": "Replace with the claim under review.",
  "overall_verdict": "insufficient_evidence",
  "overall_confidence": 0.0,
  "criteria": [
    {
      "id": "c1",
      "text": "Replace with a checkable criterion.",
      "blocking": true,
      "verdict": "insufficient_evidence",
      "confidence": 0.0,
      "evidence": [],
      "reasoning": "Short evidence-bound reasoning.",
      "counterevidence": []
    }
  ],
  "open_questions": [],
  "disputed_points_if_any": []
}
```

When the caller sets `require_reviewer_provenance`, each reviewer also writes `reviewer_agent_id` and `reviewer_source` (see [references/audit_schema.md](references/audit_schema.md)).

Rules:

- allowed verdicts are `pass`, `fail`, and `insufficient_evidence`
- `id` must stay stable across rounds
- `evidence` may be empty only when the verdict is `insufficient_evidence`
- `counterevidence` is required when the reviewer sees a real contradiction
- all reviewers in a round return the same criterion set; never invent reviewer-specific criteria

### 4. Aggregate deterministically

After each round, aggregate the reviewer JSON files with the skill's aggregator script. When working from another repository, resolve the script from the skill directory instead of assuming the repository has its own `scripts/` folder:

```bash
python <skill_dir>/scripts/aggregate_audits.py audits/<feature_name>_<phase>_audit1_iteration1.json audits/<feature_name>_<phase>_audit2_iteration1.json audits/<feature_name>_<phase>_audit3_iteration1.json --output audits/<feature_name>_<phase>_iteration1_summary.json
```

The command returns `invalid_contract` instead of measuring convergence when reviewers return different criterion sets or definitions.

The aggregator mechanically reports:

- which criteria converged
- which criteria are disputed
- whether the round status is `converged` or `not_converged`

Mechanical convergence rule:

- all reviewers give the same criterion verdict
- confidence spread for that criterion is at most `0.2`

Full convergence also requires that no new counterevidence remains unanswered. The aggregator does not judge evidence quality or blocking status; the main agent must check those from the reviewer JSON files before declaring the audit converged.

Before advancing to the next phase, run the strict phase gate after the
summary has been written:

```bash
python <skill_dir>/scripts/validate_audit_transition.py advance_phase \
  --feature-name <feature_name> \
  --from-phase <phase> \
  --to-phase <next_phase> \
  --iteration <iteration> \
  --audit-dir <audit_dir>
```

This gate fails closed unless all three reviewer files have valid metadata and
criterion contracts, the current iteration summary exists, and every blocking
criterion is converged with a final verdict of `pass`. For iteration M > 1 the
gate also loads rounds 1 to M−1 (all of which must exist) and judges each
blocking criterion by the latest round that reviewed it, so a blocking failure
settled in an earlier round is never forgotten by a targeted follow-up round.
A follow-up round must keep each criterion's round-1 text and blocking flag
and may not add criterion IDs; the gate rejects any change as
`criterion_definition_drift`. Each follow-up round may re-review only criteria
still unresolved (disputed in some earlier round and not yet settled;
`follow_up_scope_violation`), and
every earlier round is re-validated like the current one (reviewer fields,
shared criteria, and requested provenance) before it is
merged. A summary, earlier or current, is used only if it still matches its
validated reviewer files (`stale_summary`); the gate recomputes convergence
from verdicts and confidences, so pass it the same `--confidence-gap` given to
the aggregator (default 0.2). Re-aggregate after regenerating a reviewer file. A missing, malformed, or
`not_converged` blocking result must trigger a targeted follow-up round before
the next phase. Non-blocking disputes may remain only when the blocking gate
passes and must be reported explicitly.

If all blocking criteria fully converge, the final result may be treated as converged even if only non-blocking criteria still differ slightly. State that explicitly in the final answer.

### 5. Re-audit disputed criteria only

If any blocking criterion is not fully converged, do not re-run the full audit blindly.

Prepare a disagreement packet containing:

- the artifact
- the claim
- the original claim decomposition
- the disputed criteria only
- all previous audit JSON files
- the latest summary JSON

Then run a second round of reviewers. Each reviewer must:

- address only disputed criteria, keeping each one's original ID, text, and blocking flag
- say which earlier reviewer points they accept or reject
- keep unchanged criteria out of scope

Write:

- `audits/<feature_name>_<phase>_audit1_iteration2.json`
- `audits/<feature_name>_<phase>_audit2_iteration2.json`
- `audits/<feature_name>_<phase>_audit3_iteration2.json`

Aggregate again.

### 6. Stop conditions

Stop when any of the following is true:

- all blocking criteria converged
- all criteria converged
- iteration count reached 3

If iteration 3 still has unresolved blocking disagreement, do not force consensus. Mark the final status `unresolved` and report the exact disputed criteria and evidence conflict.

If the claim cannot be decomposed, a reviewer file stays malformed after regeneration by its owning reviewer, or the aggregator returns `invalid_contract`, mark the final status `error` and report the reason. Nothing is converged.

## Output Contract

For each iteration, produce:

- three reviewer JSON files
- one summary JSON file

Recommended summary names:

- `audits/<feature_name>_<phase>_iteration1_summary.json`
- `audits/<feature_name>_<phase>_iteration2_summary.json`
- `audits/<feature_name>_<phase>_iteration3_summary.json`

The final answer is the Response in [references/call-contract.md](references/call-contract.md). It should report:

- the final status: `converged`, `unresolved`, or `error`, and the overall verdict when converged
- the blocking criteria
- the disputed criteria, if any
- the main evidence that drove the result
- whether the audit converged or stopped unresolved

## Execution Guidance

Use parallel workers for reviewer generation, but keep the aggregation deterministic. Parallelism makes the first round faster. It does not replace a schema, a stopping rule, or an aggregator.

Avoid these failure modes:

- reviewers all receive the same vague prompt and produce correlated fluff
- later rounds re-audit everything instead of only disputed criteria
- convergence is defined as matching overall verdicts instead of criterion-level agreement
- disagreement is resolved by copying the dominant reviewer instead of addressing evidence

## Resources

- Load [references/audit_schema.md](references/audit_schema.md) when checking the reviewer schema, roles, convergence rules, or file naming.
- Copy [assets/audit_result_template.json](assets/audit_result_template.json) as the starting structure for each reviewer result, then replace its placeholders.
- Run [scripts/aggregate_audits.py](scripts/aggregate_audits.py) after each round to compute verdict and confidence alignment mechanically.
- Load [references/call-contract.md](references/call-contract.md) when another skill invokes this one: Request and Response fields, final statuses, the gate commands callers may run, and owned files.

## Invocation contract

This skill works directly from a user request. A host skill or third-party caller invokes it through the versioned Request/Response in [references/call-contract.md](references/call-contract.md) (checkable projection: `contract.json`). The contract is owned here: callers pass their own stage names only as the opaque `phase` label, and must not redefine reviewer fields or write reviewer files.
