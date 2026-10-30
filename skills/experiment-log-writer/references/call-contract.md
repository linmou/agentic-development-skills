# Experiment Log Writer Call Contract

Version: 1.1

## Intent

Let any caller supply experiment facts while the writer alone maintains the log. This contract describes calls to `$experiment-log-writer`; it does not require a particular experiment orchestrator.

The checkable projection of this contract is `../contract.json` (`skill-contract/1`). This file stays the authority for meaning; conditional rules the schema cannot express live only here.

## Request

Required fields:

| Field | Meaning |
|-------|---------|
| `log_path` | Path of the log to create or update. An absent file is created from the template. |
| `entry` | One event object with `kind` and the facts for that event. |

`entry.kind` is `plan`, `iteration`, `analysis`, or `correction`. The writer infers create versus update from `log_path`; there is no separate write mode. Optional fields omitted by the caller remain unknown unless the fill paths below say otherwise. An optional `caller_tag` is an opaque correlation label; never branch on its value or write it as a research fact.

| Kind | Required event facts | Optional event facts |
|------|----------------------|----------------------|
| `plan` | `question` | `title`, `prior_log`, `prior_result`, `answer_criterion`, `hypotheses`, `design`, `commands`, `directions`, `author`, `repository`, `source_commit`, `working_directory` |
| `iteration` | `number`, `timestamp`, `hypothesis_id`, `changed_files`, `decision`, `decision_reason`, and at least one `commands` record or `no_command_reason`; at least one `results` record or `no_result_reason` | `revision_note`, `artifacts`, `source_commit`, `working_directory` |
| `analysis` | `timestamp`, `observation` | `interpretation`, `directions`, `results`, `artifacts`, `iteration_commit` |
| `correction` | `timestamp`, `target`, `correction`, `reason` | `replacement_results_address`, `source_commit`, `iteration_commit` |

If `plan.prior_log` is supplied, `plan.prior_result` is required, and vice versa. A supplied hypothesis addresses the new RQ unless it explicitly names another existing RQ. Reject a reference to an RQ or hypothesis ID absent from the target log. A non-plan entry against a nonexistent log returns `needs_input` and requests a plan entry.

Nested records use these keys; supplied records missing a required key return `needs_input`:

| Record | Required keys | Optional keys |
|--------|---------------|---------------|
| `plan.hypotheses[]` | `prediction`, `expected_observation`, `rejection_observation`, `status` (`preregistered` or `post-hoc`) | `rq_id` for an existing question |
| `plan.design` | `independent_factor`, `controls`, `inputs`, `evaluation_method`, `stopping_rule`, `known_confounders` | None |
| `commands[]` | `purpose`, `status`, `command`; for `Executed` or `Modified during execution`, also `timestamp`, `working_directory`, `environment`, `exit_status`, `output_path`; for `Modified during execution`, also `planned_command` and `reason` | None |
| `results[]` | `informs`, `run_status`, `input`, `configuration`, `output`, `metric_definition`, `metric_value`, `observation`, `interpretation`, `evidence_path`; for qualitative output, also `representative_pair` or a durable pair path | None |
| `directions[]` | `question`, `motivating_evidence`, `factor_to_change`, `factors_to_hold_constant`, `evaluation`, `priority` | None |
| `artifacts` | `results_address` when known; for external raw evidence, also `location`, `content_hash` (with algorithm), `generation_command`, `run_id`, `file_count`, `size_bytes` | None |

`iteration.changed_files` contains paths with their changed factors. `iteration.decision` is `support`, `reject`, `inconclusive`, or `revise`; `decision_reason` cites recorded evidence or explains why none was produced. A planned command has status `Planned` and execution fields `Not executed`. An executed command has status `Executed`. A changed command has status `Modified during execution`, with both the planned and executed command preserved.

An executed command record requires its exact shell command, purpose, execution timestamp, working directory, environment or environment-file reference, exit status, and output/log path. A planned command requires its exact command and purpose; its execution fields are `Not executed`. If the executed command differs from the planned command, provide both and the reason. A result record requires the informed RQ or hypothesis, run status, input identifier, configuration, output or evidence path, metric definition and value (or `Not measured` with reason), observation, and interpretation. Preserve a representative input-output pair for qualitative or model-generated output, or give its durable evidence path. The writer rejects an `iteration` entry missing these facts with `needs_input`; it must not infer an unobserved execution outcome. `no_result_reason` is valid only when execution produced neither a result nor diagnostic evidence; a failed or partial run with evidence needs a result record.

`artifacts` may provide a canonical `results_address`. If raw evidence lives outside Git, also provide its durable location, content hash, generation command, run/config identifier, file count, and size. The writer records these in the log or a linked manifest and never copies bulk output into Git. After a run with diagnostic evidence, an omitted results address is written as `Unknown` with its reason and recovery action; it is never silently treated as `Not produced`. Preserve the prior canonical address in a dated note when a new unknown or replacement address becomes canonical.

The `source_commit` means the revision used to run the experiment, not the commit that will contain the log. If code had uncommitted changes during execution, record the base commit and changed files. `iteration_commit` is the later known commit containing an iteration; record it only in a subsequent dated entry. It is never required in the commit that creates it.

Minimal independent call:

```yaml
log_path: auto_experiments/2026-09-25-example/experiment_log.md
entry:
  kind: plan
  question: Does the revised prompt improve accuracy on the fixed evaluation set?
```

This creates a planned log. The writer marks unavailable required metadata and design facts `Unknown` with a reason and recovery action; it does not invent hypotheses, commands, or results.

## Response

| Field | Meaning |
|-------|---------|
| `status` | `written`, `needs_input`, or `error`. |
| `log_path` | The target path, including when no write occurred. |
| `entry_id` | New RQ ID for `plan`, new Iteration ID for `iteration`, or `null` for `analysis` and `correction`. |
| `hypothesis_ids` | For `plan`, the IDs assigned to `plan.hypotheses`, in request order (for example `["H1", "H2"]`); `[]` when none were supplied, for other kinds, and when nothing was written. Callers pass these as `iteration.hypothesis_id`. |
| `missing` | List of required facts needed for a faithful entry; empty on `written`. |
| `errors` | File or contract errors; empty unless `error`. |

On `needs_input` or `error`, do not claim that the requested entry was written. The caller may correct the request and retry. The writer does not decide whether the experiment should continue or commit.

## Template Fill Paths

Each field required by `assets/experiment-log-template.md` has a named source. `Unknown` always includes the missing fact and how to obtain it. A section with no records says `Not supplied` or `Not produced` as appropriate; it does not contain an invented example record.

| Stored attribute | Source or fail rule |
|------------------|---------------------|
| Log status | Infer from entry kind and recorded run statuses; planned before execution. |
| Created and updated timestamps | Infer from the writer's current clock when writing; preserve Created on updates. |
| Author or agent | `entry.author`, otherwise `Unknown` with recovery action. |
| Repository and working directory | `entry.repository` and `entry.working_directory`, otherwise infer from accessible repository context or write `Unknown`. |
| Experiment title | `plan.title`, otherwise use `plan.question` verbatim. |
| Initial source commit | `plan.source_commit`, otherwise infer current HEAD only when creating a planned log; else `Unknown`. |
| Results address | `entry.artifacts.results_address`; `Not produced` before execution; after new execution with evidence, `Unknown` with reason and recovery action if absent. Preserve any prior address in a dated note. |
| RQ ID and question | Assign next RQ ID; `plan.question` is required. |
| RQ origin and prior result | `plan.prior_log` and `plan.prior_result` for derived questions; otherwise `New question` and `Not applicable`. A missing half of the pair causes `needs_input`. |
| RQ answer criterion | `plan.answer_criterion`, otherwise `Unknown`. |
| Hypothesis ID, prediction, expected/rejection observations, status | Assign IDs from `plan.hypotheses`; absent hypotheses remain `Not supplied`. A supplied hypothesis missing these facts is `needs_input`; `post-hoc` must be explicit when applicable. |
| Design factor, controls, inputs, evaluation, stopping rule, confounders | Corresponding `plan.design` facts; otherwise `Unknown` with recovery action. |
| Command ID, purpose, status, exact command, timestamp, directory, environment, exit, output | Assign ID from `plan.commands` or `iteration.commands`; use the command record. Missing executed-command facts cause `needs_input`. Planned execution fields are `Not executed`. |
| Result ID, informed question/hypothesis, status, input, config, output, metric, observation, interpretation, evidence | Assign ID from `iteration.results` or `analysis.results`; use the result record. Missing result facts cause `needs_input`. |
| Iteration number, timestamp, hypothesis, source commit, changed files, commands, results, decision, revision note | `iteration` facts and IDs assigned to its command/result records; `iteration.source_commit` for the run revision, otherwise `Unknown`; optional revision note defaults to `None`. |
| Corrections and deviations | `correction` facts and command deviations; otherwise `None`. A later `iteration_commit` is a dated provenance note, never a self-reference. |
| Analysis notes | `analysis.timestamp`, `analysis.observation`, and optional interpretation or later `iteration_commit`; otherwise `None`. |
| Direction, evidence, next question, changed/constant factors, evaluation, priority | `plan.directions` or `analysis.directions`; absent directions remain `Not supplied`. A supplied direction missing these facts is `needs_input`. |

When multiple sources can supply the same attribute, a new explicit `entry` fact wins over inference. Existing historical records are preserved; a correction appends a dated note rather than replacing them. An explicit replacement results address becomes canonical while the old address remains in the correction history.

## Changes

- 1.1: Add `hypothesis_ids` to the Response so callers need not read the log to learn assigned hypothesis IDs. Additive.
- 1.0: Initial independent Request/Response contract. Additive optional facts are allowed; changing required fields or their meaning requires a new version.
