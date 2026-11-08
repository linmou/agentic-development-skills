# Agent-led interpretation of code-quality evidence

This is an **agent reasoning workflow**, not a prescribed document format or a new script. Apply after collecting raw deterministic observations.

## 1. Discover what is authoritative

Inspect the target repository's available instructions, source, tests, configuration, design decisions, and navigational references. Discover the local conventions rather than assuming any particular documentation format, framework, filename, directory, or status vocabulary. A repository may express intent only in code or tests; it may also contain conflicting or no explicit design decisions.

- Select **relevant** sources only after checking what behavior a module actually owns. Determine authority and precedence through evidence supplied by the repository, not a globally assumed hierarchy. If no reliable ordering exists, report ambiguity.
- When a source clearly represents **current approved intent**, assess potential conflicts with the observed code or proposed change.
- When a source is **proposed, aspirational, or future-facing**, treat mismatch as possible planned migration work, not automatically a regression or policy violation.
- When a source is **outdated, withdrawn, disputed, or unverified**, treat it as context rather than automatically enforceable policy; apply any repository-specific lifecycle labels by their documented meaning.
- No authoritative documentation: continue structural analysis; report unavailable design authority rather than inventing requirements.
- For nested packages, keep tool execution rooted at the package, but search the **workspace root** for applicable design records; never let a source document above the workspace escape its trust boundary.

## 2. Reason from the finding, not a fixed module mapping

For each relevant tool finding:

1. Reproduce its concrete location and graph/tool evidence. A cycle or high fan-out is an **observable graph fact**; the design risk is only a **review candidate**.
2. Examine actual code responsibilities and call paths. Avoid guessing from filenames, directory names, or a graph alone.
3. Determine whether any existing source of project intent actually applies (documentation, explicit policy, tests, or code-level contract). Cite its precise location and explain the local evidence for its authority and currency. Do not assume that a document is a governing rule merely because its filename or wording resembles a specification. Treat this as an agent-reasoned connection, not automatically a verified violation.
4. Explain the possible failure mechanism and serious alternatives (e.g., a legitimate facade or test-only dependency). Name the discriminating evidence or behavioral verification that remains.
5. Distinguish **finding** (observed), **design hypothesis** (inferred), **approved-policy conflict** (requires cited rule plus validated code behavior), **tool-reported configured-rule violation** (explicit analyzer rule), and **behavioral failure** (requires separate behavioral evidence).
6. Prioritize by demonstrated or plausible project-specific consequence, not fan-out threshold alone. Emit an issue only when requested.

Keep report text concise: finding ID, observed evidence and effective scope, relevant code, authoritative source+status if available, risk mechanism, competing explanations, what is unverified, suggested follow-up.

## Redundancy interpretation boundary

Production-only Knip candidates are unused-code signals, not proof that test references alone keep an export reachable or that deletion is safe. For code that is reachable by multiple production paths, use a call-path or event-trigger analysis rather than dead-code analysis. Before labeling a repeated resource access as redundant, inspect arguments, triggers, ordering, cancellation, recovery requirements and side effects; express unresolved alternatives in the existing report. Requirements refine the risk interpretation but are neither mandatory nor sufficient to certify redundancy. The monitor never deletes tests or code and does not verify a proposed removal.

## 3. Optional legacy JSON evidence adapter

`--requirements path/to/requirements.json` remains for existing automation requiring machine-readable associations. It must be **preauthored**, with exact requirement quotations, source paths, explicit module paths, rationale and uncertainty. The script validates literal text/path consistency and performs a module-path join. **It does not** select documents, interpret semantics, determine source authority, enforce requirements, or prove impact.

Do **not** require this manifest for ordinary agent-led interpretation. A report can directly cite whatever authoritative source the target repository provides, where available. When legacy manifest documents live in a parent workspace while tools analyze a nested package, set `--workspace-root` to the containing workspace; mapping `modules` still uses paths relative to `--repo`, and source `path` uses paths relative to the workspace root.

Do not equate `requirement_interpretation.status = not_provided` with a failure of the **agent's** interpretation. It indicates only that the optional JSON path was not invoked.

## 4. Cross-repository behavioral evaluation scenarios

Evaluate the **agent skill**, not just unit-test the scripts. For each scenario inspect the transcript, reports and cited evidence.

| Case | Expected agent behavior | Failure condition |
| --- | --- | --- |
| No documented design intent | Produce useful structural findings, explicitly note unavailable authority | Invent project requirements, impact, or policy violations |
| Unconventional, unindexed design document at workspace root; application nested in a package | Discover source based on repository evidence, preserve analyzer package root, cite correct source locations and authority | Demand a hand-written JSON manifest, assume a named framework, or silently skip parent sources |
| Conflicting current, proposed, and historical records with arbitrary project-specific labels | Determine meaning from local evidence; distinguish current enforceable intent from proposals and stale text; flag unresolved conflict | Treat any label or matching quote as a universally recognized hard rule |
| Misleading filenames | Inspect actual code before claiming component ownership | Invent responsibilities from path names |
| Graph cycle/high fan-out | Report concrete observation and potential mechanism with alternatives | Claim SRP/DIP/behavioral failure from metric alone |
| Existing configured rule violation | Preserve exact analyzer rule and severity; separate from semantic inference | Downgrade confirmed analyzer violation to a guess or enforce a guessed contract |
| Malformed evidence mapping | Validator fails and keeps evidence; no fabricated association | Ignore stale quote or path traversal |
| Unsupported language/tool | Adapt to existing repo tools or report unavailable coverage | Present an unsupported scan as clean |

Compare current script-driven baseline to this hybrid workflow on representative unfamiliar repositories with differing document conventions and no framework dependencies; measure supported coverage, false positives, groundedness, execution cost and analyst work. Do not claim an empirical improvement without running that comparison.
