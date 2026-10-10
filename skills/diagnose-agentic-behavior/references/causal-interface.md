# Causal Research Interface

**Intent:** Define the boundary between this host skill's ontology and annotation work and the causal-research dependency.

The host frames the failure target, induces and freezes the task ontology, builds the annotated trace and residual log, runs the expressibility check, and presents the returned attribution. It does not rank rival explanations or issue a causal ruling on its own.

The `competing-explanations-causal-research` skill owns evidence assessment, rival-model construction, symmetric testing, ranking, execution and evidence statuses, stopping, and the versioned Request/Response contract. Load that skill and use its current call contract. Use only the contract's documented fields; the host keeps its own workflow state out of the Request.

## Request

Submit the Request version supported by the dependency's current call contract with:

- `outcome`: the frozen observed deviation from the intended outcome.
- `scope`: analysis unit, attempt/time boundary, environment, success conditions, and intended decision.
- `evidence_seeds`: source locations or excerpts; the frozen task ontology `O_v0`; annotated-trace records; expected-type coverage including errors of omission; the residual log with carried residuals as raw spans; candidate deviations and supplied theories as unranked leads.
- `constraints`: evidence cutoff, permitted sources and tests, access limits, and the requirement to mark unknown links.
- `detail`: `full` for an auditable ledger.
- `output_language`: the requester's language.
- `contract_version`: the version declared by the current call contract.

Include `caller_tag` only when correlation is useful. Local-only access is a source constraint, not a reason to bypass the dependency.

## Response handling

- **Completed:** run the expressibility check in [ontology-induction.md](ontology-induction.md) on every returned model, then map the statuses to concrete actions, artifact paths, environment-state transitions, and errors of omission in the annotated trace. Representation gaps are rendered with raw spans and leave the returned ranking unchanged.
- **Clarification or blocking:** obtain the missing boundary, or report errors and descriptive findings.
- **Malformed response or unsupported version:** no causal ruling.
- **Missing material link or new evidence:** submit an updated Request. The host adds trace references and presentation; causal revisions return to the dependency.
