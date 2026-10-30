# Causal Research Interface

**Intent:** Define the boundary between this host skill's ontology and case-graph work and the causal-research dependency.

The host frames the failure target, induces and versions the task ontology, builds the case graph and residual log, runs the expressibility check, and presents the returned attribution. It does not rank rival explanations or issue a causal ruling on its own.

The `competing-explanations-causal-research` skill owns evidence assessment, rival-model construction, symmetric testing, ranking, execution and evidence statuses, stopping, and the versioned Request/Response contract. Load that skill and use its current call contract. Use only the contract's documented fields; the host keeps its own workflow state out of the Request.

## Request

Submit a Request under call contract version 2 (`competing-explanations-causal-research@^2.0.0`) with:

- `outcome`: the frozen observed deviation from the intended outcome.
- `scope`: analysis unit, attempt/time boundary, environment, success conditions, and intended decision.
- `evidence_seeds`: source locations or excerpts; the current task ontology version and its revision log; case-graph records; expected-type coverage including absences; the residual log; the agent task model if built; candidate deviations and supplied theories as unranked leads.
- `constraints`: evidence cutoff, permitted sources and tests, access limits, and the requirement to mark unknown links.
- `detail`: `full` for an auditable ledger.
- `output_language`: the requester's language.
- `contract_version`: `2`.

Include `caller_tag` only when correlation is useful. Local-only access is a source constraint, not a reason to bypass the dependency.

## Response handling

Act on `execution_status`:

- **`completed`:** run the expressibility check in [ontology-induction.md](ontology-induction.md) on every returned model. A gap leads to an ontology extension, a remap, and a new Request, as the contract requires for further research. Then map the returned models and `evidence_status` (`supported`, `provisional`, or `insufficient`) to concrete actions, artifact paths, world-state transitions, and absences in the case graph; never upgrade a `provisional` or `insufficient` ruling.
- **`needs_clarification`:** obtain the missing boundary, then submit a new Request; no causal ruling meanwhile.
- **`blocked`:** report `errors` and the descriptive findings; no causal ruling.
- **Malformed response or unsupported version:** no causal ruling.
- **Missing material link or new evidence:** submit an updated Request. The host adds graph references and presentation; causal revisions return to the dependency.
