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

Inputs:

- `artifact`
- `claim`
- `feature_name`
- optional `phase`, default `green`

Write a short claim decomposition before running reviewers:

- 3 to 7 criteria
- each criterion must be checkable with a `pass`, `fail`, or `insufficient_evidence` verdict
- identify which criteria are blocking

If the user did not provide a `feature_name`, derive a short snake_case or kebab-case label from the claim.

### 2. Keep audit artifacts out of Git

Before writing audit files in a Git repository:

- resolve the repository-local exclude file with `git rev-parse --git-path info/exclude`
- add `/audits/` to that exclude file if the exact rule is absent
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

Each reviewer writes exactly one file:

- `audits/<feature_name>_<phase>_audit1_iteration1.json`
- `audits/<feature_name>_<phase>_audit2_iteration1.json`
- `audits/<feature_name>_<phase>_audit3_iteration1.json`

Every criterion verdict must cite evidence or explicitly record missing evidence. No unsupported verdicts.

Reviewer JSON contract:

```json
{
  "feature_name": "replace-me",
  "phase": "green",
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

Rules:

- allowed verdicts are `pass`, `fail`, and `insufficient_evidence`
- `id` must stay stable across rounds
- `evidence` may be empty only when the verdict is `insufficient_evidence`
- `counterevidence` is required when the reviewer sees a real contradiction

### 4. Aggregate deterministically

After each round, aggregate the reviewer JSON files with the skill's aggregator script. When working from another repository, resolve the script from the skill directory instead of assuming the repository has its own `scripts/` folder:

```bash
python <skill_dir>/scripts/aggregate_audits.py audits/<feature_name>_<phase>_audit1_iteration1.json audits/<feature_name>_<phase>_audit2_iteration1.json audits/<feature_name>_<phase>_audit3_iteration1.json --output audits/<feature_name>_<phase>_iteration1_summary.json
```

The aggregator mechanically reports:

- which criteria converged
- which criteria are disputed
- whether the round status is `converged` or `not_converged`

Mechanical convergence rule:

- all reviewers give the same criterion verdict
- confidence spread for that criterion is at most `0.2`

Full convergence also requires that no new counterevidence remains unanswered. The aggregator does not judge evidence quality or blocking status; the main agent must check those from the reviewer JSON files before declaring the audit converged.

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

- address only disputed criteria
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

## Output Contract

For each iteration, produce:

- three reviewer JSON files
- one summary JSON file

Recommended summary names:

- `audits/<feature_name>_<phase>_iteration1_summary.json`
- `audits/<feature_name>_<phase>_iteration2_summary.json`
- `audits/<feature_name>_<phase>_iteration3_summary.json`

The final user-facing answer should report:

- the final status
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
