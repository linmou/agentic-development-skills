# Auto-exp call contract v1

Intent: expose the existing experiment workflow to calling skills through a versioned interface. The execution procedure remains in [SKILL.md](../SKILL.md).

Updated: 2026-10-30. Source baseline: `6dd1da1`.

## Request

Version: `1.0.0`. Required fields:

- `repository`: absolute path to the existing repository where the experiment is requested. Inspect it before selecting the execution worktree.
- `task`: the experiment request, including known research question, evaluation signal, constraints, and references to applicable plans or domain procedures. Missing facts must be identified rather than invented; resolve them through the existing Start Gate. Caller-supplied domain procedures govern scientific interpretation, while this skill owns experiment execution.

This is an agent skill call, not an executable API. It requires filesystem and Git tools plus whatever execution capabilities the experiment needs. Inspect referenced artifacts; unreadable references or unavailable capabilities prevent dependent execution. Supplied facts remain subject to the Start Gate and repository guidance. Requests confer no authorization beyond the user's scope.

Minimal example:

```json
{"repository":"/work/research","task":"Measure whether the candidate reduces classifier false negatives against the baseline. Use evaluation-plan.md for fixed cases and metrics. Runtime and model budget are not yet supplied."}
```

## Response

Return an object with `status`, `summary`, `artifacts`, `branch`, and `commits`:

- `completed`: the declared experiment scope ran and its records and iteration commits are complete, including experiments whose hypothesis was rejected. Domain acceptance belongs to the caller.
- `needs_input`: named facts or decisions required by the Start Gate or repository guidance are missing; `summary` names them.
- `incomplete`: execution stopped with unfinished scope, such as exhausted authorized budget or interrupted runs; `summary` names the remaining work.
- `error`: a tool, configuration, validation, or commit failure prevents completion; `summary` states the failure and affected state.

`summary` is a non-empty explanation. `artifacts` lists paths or durable artifact locations actually produced, including the experiment log when created. `branch` is the actual experiment branch, or null before one exists. `commits` contains only verified iteration commit hashes. Empty arrays are valid when no corresponding artifacts or commits exist. Preserve available evidence on every status; never fabricate success artifacts for a failure response.

Produce these fields from observed tool results, the experiment log and verified Git state. Validate the response against `contract.json` and check listed artifacts exist. If a storage failure prevents writing a log, return `error` in conversation with the available evidence locations and empty collections where necessary. The ordinary success path is the existing setup, experiment loop, validation and commit procedure.

## Ownership and versioning

Auto-exp coordinates execution and delegates every ledger write to its declared experiment-log-writer dependency. Callers provide findings through auto-exp rather than writing that ledger. Domain specifications, evaluation decisions and reports remain caller-owned. Other experiment artifacts follow the existing project-placement policy in SKILL.md, with observed paths returned in `artifacts`. A missing or incompatible logging dependency blocks execution; the writer's `needs_input` and `error` results propagate to the corresponding status here.

Breaking changes to fields or status meanings require a major version. Initial version `1.0.0` formalizes the existing workflow's inputs, evidence and completion states.
