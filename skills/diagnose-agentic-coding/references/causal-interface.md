# Causal Research Interface

**Intent:** Define the boundary between this host skill's artifact reconstruction and the causal-research dependency.

The host reconstructs the six L1 functions, artifact instances, SYS versions and transitions, method-dependent edges, and evidence gaps. It presents the returned attribution in the case graph. It does not rank rival explanations or issue a causal ruling independently.

The `competing-explanations-causal-research` skill owns evidence assessment, rival-model construction, symmetric testing, ranking, execution and evidence statuses, stopping, and the versioned Request/Response contract. Load that skill and use its current call contract when invoking it.

## Request

Submit a Request under call contract version 2 (`competing-explanations-causal-research@^2.0.0`) with:

- `outcome`: the frozen observed outcome.
- `scope`: analysis unit, attempt/time boundary, environment, intended outcome, and decision.
- `evidence_seeds`: source locations or excerpts, graph records, development-method evidence, gaps, candidate deviations, and supplied theories as unranked leads.
- `constraints`: evidence cutoff, permitted sources/tests, access limits, and the requirement to mark unknown links.
- `detail`: `full` for an auditable ledger.
- `output_language`: the requester's language.
- `contract_version`: `2`.

Include `caller_tag` only when correlation is useful. Provide accessible sources or excerpts. Local-only access is a source constraint, not a reason to bypass the dependency.

## Response handling

Act on `execution_status`:

- `completed`: map the returned models and `evidence_status` (`supported`, `provisional`, or `insufficient`) to concrete L1 actions, artifact paths, and SYS transitions. Present `provisional` and `insufficient` rulings as such; never upgrade them.
- `needs_clarification`: obtain the missing boundary from the user or the evidence, then submit a new Request. Do not issue a causal ruling meanwhile.
- `blocked`: report `errors` and the descriptive graph with its unknowns; no causal ruling.

A malformed response or unsupported version does not support a causal ruling.

If the comparison lacks a material artifact link, proposes a new mechanism, or new evidence changes the case, submit an updated Request. The host adds graph references and presentation; causal revisions return to the dependency.
