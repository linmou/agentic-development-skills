# Call Contract: Review With Multi Debate

**Intent:** Let any caller request a multi-reviewer audit of an artifact against a claim, and read a final status, without importing the caller's workflow states or redefining the reviewer schema.

## Version

`1.0.0`. [`../contract.json`](../contract.json) is the checkable projection of this file; callers declare `review-with-multi-debate@^1.0.0`. Add optional fields for compatible changes. Removing a field, a status, or a gate check, or changing a meaning, is a new major version.

## Request

| Field | Class | Required / default | Meaning |
|---|---|---|---|
| `artifact` | content | required | The thing under review: a path, diff, document, or inline text. |
| `claim` | content | required | The statement the artifact must satisfy. Decomposed into 3–7 checkable criteria before review. |
| `feature_name` | output | optional; derived from the claim as a short snake_case or kebab-case label | First part of every audit file name. |
| `phase` | output | optional; `review` | Opaque label in audit file names and metadata. Callers may use their own stage names; this skill never branches on the value. |
| `evidence` | seed | optional; `[]` | Paths or excerpts reviewers need, including existing test output. Missing test output is reported as unverified execution, never inferred. |
| `frozen` | control | optional; absent | Frozen-round mode. An object with `criteria_manifest` (required: the persisted criterion set), optional `scope` (editable and protected paths), optional `include` (other input paths), and `bundle_path` (where to write the review bundle). When present, every reviewer receives the manifest, bundle and digest fields become required, and the gates verify the bundle. |
| `require_reviewer_provenance` | control | optional; `false` | When `true`, every reviewer file must carry `reviewer_agent_id` and `reviewer_source` (see `audit_schema.md`), with distinct identities. `advance_phase --require-reviewer-provenance` enforces it; without that gate the skill checks the fields before reporting `converged`. Fields still missing after regeneration by the owning reviewer make the final status `error`. |
| `audit_dir` | output | optional; `audits` | Directory for reviewer and summary files. |
| `caller_tag` | opaque | optional; absent | Caller correlation label. Echoed in the final answer; never control. |

Precedence: `frozen.criteria_manifest`, when present, fixes the criteria and replaces the skill's own decomposition. Otherwise the skill decomposes `claim`. `evidence` adds inputs; it never changes the claim. In frozen mode `artifact` must be a path, and the artifact and every `evidence` path are frozen with the bundle together with `frozen.include`, so reviewers never read an unfrozen input.

### Minimal third-party request

```json
{ "artifact": "docs/password-reset-prd.md", "claim": "The PRD specifies a complete password-reset flow." }
```

This writes `audits/<derived_feature>_review_audit{1,2,3}_iteration1.json` and a summary, and returns a final status.

## Response

The final answer of the skill carries the fields below. It is not a file: the per-round summary that `aggregate_audits.py` writes has its own schema (see [Round summary](#round-summary)), and gated callers read that summary and the `advance_phase` result instead.

| Field | Condition | Meaning |
|---|---|---|
| `status` | always | `converged`, `unresolved`, or `error`. |
| `overall_verdict` | when `converged` | `pass` only if every blocking criterion converged on `pass`; `fail` if any blocking criterion converged on `fail`; otherwise `insufficient_evidence`. |
| `blocking_criteria` | always unless `error` before decomposition | Criterion IDs marked blocking, with final verdicts. |
| `disputed_criteria` | always; `[]` when none | Criteria still disputed, with the evidence conflict. |
| `iterations` | always unless `error` before round 1 | Number of rounds run (1–3). |
| `summary_path` | always unless `error` before aggregation | Last `<feature_name>_<phase>_iterationM_summary.json`. |
| `audit_paths` | always unless `error` before round 1 | Reviewer files of the last round. |
| `review_bundle_id` | when `frozen` | Digest of the frozen inputs. |
| `errors` | always; `[]` when none | Contract or gate failures. |
| `caller_tag` | if supplied | Exact opaque label. |

Status rules:

- `converged`: every blocking criterion converged (same verdict, confidence spread ≤ 0.2, no unanswered counterevidence). Non-blocking disputes may remain and are listed.
- `unresolved`: blocking disagreement remains after iteration 3. The skill never forces consensus.
- `error`: the claim could not be decomposed into checkable criteria, a reviewer file stayed malformed after regeneration by its owning reviewer, a frozen bundle failed verification, or the aggregator returned `invalid_contract`. Nothing is converged.

`not_converged` is a per-round summary status, not a final status: it always triggers another round or ends as `unresolved`.

### Round summary

Each round's `<audit_dir>/<feature_name>_<phase>_iterationM_summary.json` (written by `aggregate_audits.py`) has:

| Field | Meaning |
|---|---|
| `feature_name`, `phase`, `iteration`, `reviewer_count` | Round identity. |
| `review_bundle_id`, `criteria_manifest_digest` | Frozen-round digests, or `null`. Absent when `invalid_contract`. |
| `status` | `converged` (no disputed criterion), `not_converged`, or `invalid_contract` (reviewer inputs mismatched the frozen handoff). |
| `disputed_criteria` | Criterion IDs that did not converge mechanically. |
| `criteria` | Per criterion: verdicts, confidences, `final_verdict`, `converged`. |
| `contract_errors` | Only when `invalid_contract`. |

The summary measures mechanical agreement only; it does not judge blocking status, evidence quality, or counterevidence. A gated caller advances only when `advance_phase` returns `accepted`, which corresponds to a final `converged` status with every blocking criterion on `pass`.

## Gate interface

A caller that advances its own stages on a debate result may run these commands from this skill's directory. They are part of this contract and change only with its version:

| Command | Checks |
|---|---|
| `scripts/validate_audit_transition.py record_round --feature-name F --phase P --iteration M --audit-dir D` | All three reviewer files exist. |
| `scripts/aggregate_audits.py <three reviewer files> --output <summary>` (plus `--criteria-manifest`, `--review-bundle-id`, `--criteria-manifest-digest` when frozen) | Mechanical convergence per criterion; `invalid_contract` on mismatched inputs. With a manifest, round 1 must return the whole manifest and follow-up rounds a subset with unchanged definitions. |
| `scripts/validate_audit_transition.py advance_phase --feature-name F --from-phase P --to-phase N --iteration M --audit-dir D` (plus `--review-bundle`, `--repo-root`, `--criteria-manifest` when frozen) | Fails closed unless every blocking criterion converged on `pass`. From iteration 2 it merges all earlier rounds (which must exist) and judges each blocking criterion by the latest round that reviewed it; it rejects any change to a criterion's round-1 text or blocking flag, and any criterion ID added after round 1. |
| `scripts/review_bundle.py freeze` / `verify` | Freezes and verifies the declared inputs of a frozen round. |

`--to-phase` is the caller's own next-stage label; it is recorded, never interpreted.

## Writes

This skill alone writes reviewer files `<audit_dir>/<feature_name>_<phase>_auditN_iterationM.json`, summaries `<audit_dir>/<feature_name>_<phase>_iterationM_summary.json`, and, in frozen mode, the bundle at `frozen.bundle_path`. Each reviewer writes only its own file. In a Git repository it also adds a repository-local exclude rule for `audit_dir` when the audit paths are not already ignored, and never changes the index.

## Caller obligations

Supply the artifact, claim and inputs; read the final status; never write or repair a reviewer file, never transcribe a reviewer's opinion, and never treat `unresolved` or `error` as a pass. A caller may add stricter requirements on optional fields (for example `require_reviewer_provenance`), but may not add new required reviewer fields; propose them here instead.
