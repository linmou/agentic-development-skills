# Causal Research Interface

**Intent:** Define the boundary between this host skill's ontology and case-graph work and the causal-research dependency.

The host frames the contrastive target, induces and versions the task ontology, builds the case graph and residual log, and presents the returned attribution. It does not rank rival explanations or issue a causal ruling on its own.

The `competing-explanations-causal-research` skill owns evidence assessment, rival-model construction, symmetric testing, ranking, execution and evidence statuses, stopping, and the versioned Request/Response contract. Load that skill and use its current call contract.

## Request

Submit the Request version supported by the dependency's current call contract with:

- `outcome`: the frozen behavior X and foil Y.
- `scope`: analysis unit, attempt/time boundary, environment, success conditions (if any), and intended decision.
- `evidence_seeds`: source locations or excerpts; the current task ontology version and its revision log; case-graph records; expected-type coverage including absences; the residual log; the agent task model if built; candidate deviations and supplied theories as unranked leads.
- `constraints`: evidence cutoff, permitted sources and tests, access limits, the requirement to mark unknown links, and the **expressibility request**: report any rival that cannot be stated in the current ontology, with the concept it needs.
- `detail`: `full` for an auditable ledger.
- `output_language`: the requester's language.
- `contract_version`: the version declared by the current call contract.

Include `caller_tag` only when correlation is useful. Local-only access is a source constraint, not a reason to bypass the dependency.

## Response handling

Map the response's statuses to concrete actions, artifact paths, world-state transitions, and absences in the case graph.

- **Expressibility gap reported:** extend the ontology under the admission rules, remap, and resubmit before accepting the ranking.
- **Clarification or blocking:** obtain the missing boundary, or report errors and descriptive findings.
- **Malformed response or unsupported version:** no causal ruling.
- **Missing material link, new mechanism, or new evidence:** submit an updated Request. The host adds graph references and presentation; causal revisions return to the dependency.
