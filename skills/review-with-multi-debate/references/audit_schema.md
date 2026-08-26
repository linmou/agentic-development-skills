# Intent

Define the audit JSON shape and the minimum reviewer obligations for `review-with-multi-debate`.

## Reviewer Output Schema

Each reviewer must write one JSON object with these top-level fields:

```json
{
  "feature_name": "login-flow",
  "phase": "green",
  "iteration": 1,
  "reviewer_id": "audit1",
  "claim": "The artifact satisfies the login-flow claim.",
  "overall_verdict": "pass",
  "overall_confidence": 0.82,
  "criteria": [],
  "open_questions": [],
  "disputed_points_if_any": []
}
```

Allowed verdicts:

- `pass`
- `fail`
- `insufficient_evidence`

## Criterion Schema

Each item in `criteria` must contain:

```json
{
  "id": "c1",
  "text": "Artifact includes explicit login validation.",
  "blocking": true,
  "verdict": "pass",
  "confidence": 0.91,
  "evidence": [
    {
      "kind": "quote",
      "location": "artifact:12",
      "text": "..."
    }
  ],
  "reasoning": "Short explanation tied to the evidence.",
  "counterevidence": []
}
```

Rules:

- `id` must stay stable across rounds
- `reasoning` must be short and evidence-bound
- `evidence` may be empty only when the verdict is `insufficient_evidence`
- `counterevidence` is required when the reviewer sees a real contradiction

## Reviewer Roles

Use these reviewer identities in round 1:

- `audit1`: strict verifier
- `audit2`: charitable verifier
- `audit3`: contradiction hunter

Later rounds keep the same reviewer ids so iteration history stays comparable.

## Round 2 and Later

When reviewers receive prior audit files, they must:

- focus only on disputed criteria
- explicitly reference which earlier reviewer claims they accept or reject
- avoid rewriting already converged criteria

`disputed_points_if_any` should contain short references such as:

- `c2: audit1 says fail from artifact:54, audit2 says pass from artifact:61`

## Convergence Rules

A criterion converges when all of these hold:

- all reviewer verdicts match
- the confidence spread is `<= 0.2`
- no unaddressed counterevidence remains

Overall status options:

- `converged`
- `not_converged`
- `unresolved`

Use `unresolved` only after the hard stop iteration if blocking criteria still disagree.

## File Naming

Reviewer files:

- `audits/<feature_name>_<phase>_audit1_iteration1.json`
- `audits/<feature_name>_<phase>_audit2_iteration1.json`
- `audits/<feature_name>_<phase>_audit3_iteration1.json`

Summary files:

- `audits/<feature_name>_<phase>_iteration1_summary.json`
- `audits/<feature_name>_<phase>_iteration2_summary.json`
- `audits/<feature_name>_<phase>_iteration3_summary.json`

## Aggregator Responsibility

The aggregator must stay dumb and deterministic. It should:

- load reviewer JSON files
- compare verdicts per criterion id
- compare confidence spread
- report disputed criteria
- avoid generating new substantive judgments

That separation matters. Reviewers interpret evidence. The aggregator measures alignment.
