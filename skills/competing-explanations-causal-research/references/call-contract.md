# Call Contract: Competing-Explanations Causal Research

**Intent:** Let any caller request causal-comparison research without importing caller lifecycle states or file schemas.

## Version

`1`. Add optional fields for compatible changes. Do not silently repurpose a field; make a breaking change a new major version and document any temporary alias with a clear winner and retirement date.

## Request

| Field | Class | Required / default | Meaning |
|---|---|---|---|
| `contract_version` | control | optional; `1` | Version to apply. Fail closed for an unsupported major version. |
| `outcome` | content | required | The event, state, change, difference, or decision to explain. |
| `scope` | content | optional; infer from the outcome and supplied context | Boundaries such as analysis unit, period, geography, population, and intended decision. |
| `evidence_seeds` | seed | optional; `[]` | Files, links, records, or claims that are leads to assess, not accepted proof. |
| `constraints` | control | optional; no extra constraint | Research cutoff, permitted sources, access limits, or required comparisons. Cannot change `outcome`. |
| `detail` | control | optional; `standard` | `brief`, `standard`, or `full`. `full` includes the evidence-ledger view. |
| `output_language` | control | optional; requester language | Language of the response. |
| `caller_tag` | opaque | optional; absent | Caller correlation label. Echo it if supplied; never branch research control on it. |

Precedence is: the required `outcome` fixes the target; explicit `scope` narrows inferred context; `constraints` govern method and access without changing the target; `evidence_seeds` provide leads only. If a material boundary is still unknown, ask one minimal question or return `needs_clarification`; never invent it.

### Minimal third-party request

```json
{
  "outcome": "Why did adoption of the service rise between 2024 and 2025?"
}
```

This request completes the capability at the level permitted by available evidence. If the outcome is not identifiable enough to research, return `needs_clarification` with the missing item rather than silently choosing a different outcome.

## Standard Response

| Field | Default / condition | Meaning |
|---|---|---|
| `status` | always | `completed`, `evidence_limited`, `needs_clarification`, or `blocked`. These are callee statuses, never caller states. |
| `report` | always unless blocked before analysis | The causal comparison with citations and bounded conclusion. |
| `limitations` | always; `[]` if none identified | Scope, timing, source, or inference limits. |
| `errors` | always; `[]` on success | Fail-closed errors, including an unsupported contract version. |
| `artifacts` | always; `[]` | Persistent output paths. This skill creates no persistent artifacts unless the direct user separately requests one. |
| `evidence_ledger` | only for `detail: full` | The compact ledger view defined by `evidence-ledger.md`. |
| `caller_tag` | only if supplied | Exact opaque label from the Request. |

The skill has no validator, persistence template, or mandatory stored attribute. `artifacts` is therefore empty by default and no Request field fills storage.

### Report-format requirement

For every response with `status: completed` or `status: evidence_limited`, `report` must be rendered using [the report template](report-template.md), with these six headings in this order:

1. `Scope and outcome`
2. `Evidence roles and quality`
3. `Competing models`
4. `Process and counterfactual assessment`
5. `Relative ruling`
6. `Limitations, residuals, and next evidence`

The `brief` detail level may shorten entries but may not remove a heading or field label. `standard` and `full` responses must complete all applicable template fields and explicitly mark unavailable or unrun work. A response with `detail: full` must also include the evidence-ledger view from [evidence-ledger.md](evidence-ledger.md) in `evidence_ledger`. The response is invalid if it returns a free-form narrative without these sections, even when `report` is otherwise populated.

## Caller obligations

Callers may pack available context into the documented fields and render the returned report. Do not require or supply caller phase names, workflow tokens, or a caller-specific response schema. A caller that needs more research must make a new Request; it must not independently rewrite the causal comparison as a fallback.
