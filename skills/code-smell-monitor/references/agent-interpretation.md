# Agent-led interpretation of code-quality evidence

This is an **agent reasoning workflow**, not a prescribed document format or a new script. Apply after collecting raw deterministic observations.

## 1. Discover what is authoritative

Look at repository instructions and navigation first: `AGENTS.md`, project README, package roots, docs index, ADR/decision records, BMAD Architecture Spine, PRD/NFR, design specifications, security policy, and current code. Do not assume any path or naming scheme.

- Select **relevant** decisions only after checking what behavior a module owns. Resolve conflicting documents by explicit supersession, status, project policy and owner approval; if no reliable ordering exists, report it as ambiguous.
- `ADOPTED` / accepted: current approved rule; evaluate whether the observed code or proposed change may conflict.
- `TARGET` / proposed: future direction; mark existing noncompliance as possible known migration debt, not automatically a regression or a policy violation.
- Superseded / historical / draft / `ASSUMPTION`: contextual evidence only until authority is established.
- No docs: continue structural analysis; report missing authority rather than inventing requirements.
- For nested packages, keep tool execution rooted at the package, but search the **workspace root** for applicable design records; never let a source document above the workspace escape its trust boundary.

## 2. Reason from the finding, not a fixed module mapping

For each relevant tool finding:

1. Reproduce its concrete location and graph/tool evidence. A cycle or high fan-out is an **observable graph fact**; the design risk is only a **review candidate**.
2. Examine actual code responsibilities and call paths. Avoid guessing from filenames, directory names, or a graph alone.
3. Ask which, if any, current ADR, PRD/NFR, or local rule applies. Quote or cite the *exact current section/line range*, include decision status and provenance. Treat this as an agent-reasoned connection, not a validated policy violation.
4. Explain the possible failure mechanism and serious alternatives (e.g., a legitimate facade or test-only dependency). Name the discriminating evidence or behavioral verification that remains.
5. Distinguish **finding** (observed), **design hypothesis** (inferred), **approved-policy conflict** (requires cited rule plus validated code behavior), **tool-reported configured-rule violation** (explicit analyzer rule), and **behavioral failure** (requires separate behavioral evidence).
6. Prioritize by demonstrated or plausible project-specific consequence, not fan-out threshold alone. Emit an issue only when requested.

Keep report text concise: finding ID, observed evidence and effective scope, relevant code, authoritative source+status if available, risk mechanism, competing explanations, what is unverified, suggested follow-up.

## 3. Optional legacy JSON evidence adapter

`--requirements path/to/requirements.json` remains for existing automation requiring machine-readable associations. It must be **preauthored**, with exact requirement quotations, source paths, explicit module paths, rationale and uncertainty. The script validates literal text/path consistency and performs a module-path join. **It does not** select documents, interpret semantics, determine source authority, enforce requirements, or prove impact.

Do **not** require this manifest for ordinary agent-led interpretation. A report can cite an ADR directly. If a legacy manifest cites a document in the parent workspace while tools analyze a nested package, set `--workspace-root` to the containing workspace; mapping `modules` still uses paths relative to `--repo`, and source `path` uses paths relative to the workspace root.

Do not equate `requirement_interpretation.status = not_provided` with a failure of the **agent's** interpretation. It indicates only that the optional JSON path was not invoked.

## 4. Cross-repository behavioral evaluation scenarios

Evaluate the **agent skill**, not just unit-test the scripts. For each scenario inspect the transcript, reports and cited evidence.

| Case | Expected agent behavior | Failure condition |
| --- | --- | --- |
| No requirements/docs | Produce useful structural findings, explicitly note missing authority | Invent a PRD, ADR, impact or policy violation |
| BMAD/ADR in workspace root; TS app nested | Discover applicable parent decision, preserve analyzer package root, cite correct paths/status | Demand a hand-written JSON manifest or silently skip parent docs |
| Conflicting adopted/target/historical records | Distinguish approved current rule from target and stale text; flag unresolved conflict | Treat any matching quote as a current hard rule |
| Misleading filenames | Inspect actual code before claiming component ownership | Invent responsibilities from path names |
| Graph cycle/high fan-out | Report concrete observation and potential mechanism with alternatives | Claim SRP/DIP/behavioral failure from metric alone |
| Existing configured rule violation | Preserve exact analyzer rule and severity; separate from semantic inference | Downgrade confirmed analyzer violation to a guess or enforce a guessed contract |
| Malformed evidence mapping | Validator fails and keeps evidence; no fabricated association | Ignore stale quote or path traversal |
| Unsupported language/tool | Adapt to existing repo tools or report unavailable coverage | Present an unsupported scan as clean |

Compare current script-driven baseline to this hybrid workflow on representative unfamiliar repositories; measure supported coverage, false positives, groundedness, execution cost and analyst work. Do not claim an empirical improvement without running that comparison.
