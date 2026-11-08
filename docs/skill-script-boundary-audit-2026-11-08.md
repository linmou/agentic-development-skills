# Skill authoring boundary audit — 2026-11-08

Tracking: [#20](https://github.com/linmou/agentic-development-skills/issues/20).

## Rule used

Follow Skill Creator's degrees-of-freedom principle: an agent chooses context-sensitive inputs, trade-offs, source authority, and interpretations; scripts own repeatable deterministic calculations, validation, exact-source checks, and verifiable transformations. A large script is **not** a problem by itself. Flag scripts only if they claim an adaptive judgment they do not actually perform or impose an unnecessary author-machine/repository assumption.

## Findings and dispositions

| Skill | Current script responsibility | Judgment/script conflation? | Disposition |
| --- | --- | --- | --- |
| `code-smell-monitor` | Generic scan orchestration, architecture graph, optional v1 mapping and quote validation | **Confirmed:** `requirement_interpretation.py` was named/described as interpretation but only validated preauthored module mappings; CLI made the JSON format appear necessary for requirement-aware work. | **Fixed here:** agent-first SKILL instructions, source-agnostic interpretation guidance, explicit legacy adapter scope; support parent-workspace citations in optional mapping without changing analyzer root. Graph and deterministic validation remain. |
| `handoff-context` | Template generator, agent fills/selects context and validates with fresh readers | **No judgment conflation**; confirmed environment coupling: helper invocation hardcoded `/Users/admin/.codex/...`. | **Fixed here:** skill-root-relative invocation. |
| `formalize-workflow-state-machine` | Agent extracts, adjudicates and obtains approval; generator builds bounded approved state machine | No: clear approval boundary and the generator is for a source-verified spec. | Keep. Observe drift if generator starts inferring semantics. |
| `skill-contract` | Script checks mechanical caller/callee contract shapes; agent scores semantic V1–V7 separately | No: explicit semantic review is outside the script. | Keep. |
| `review-with-multi-debate` | Scripts validate transition metadata and aggregate recorded reviewer votes; reviewers assess actual evidence | No: explicit instruction not to let aggregator judge evidence quality. | Keep. |
| `fast-multi-agent-tdd` | Scripts enforce snapshot/provenance/phase boundaries; agents implement and independently review | No demonstrated conflation; high procedural strictness is intentional for phase integrity. | Keep; evaluate overhead separately if requested. |
| `speckit-orchestrate` | Script validates declared transition metadata, explicitly does not independently authenticate actors/history | No: explicit validator limits, integration/reconciliation remains agent-led. | Keep. |
| `auto-exp` | Uses deterministic log writing/iteration records, agent formulates experiment hypotheses and conclusions | No confirmed conflation from skill definition. | Keep. |
| `parallelize-workflow` | Agent models workflow and bottlenecks; scripts enforce resulting state machine when runnable version is requested | No observed conflation in skill design. | Keep. |

## Portability rule

The skill must not rely on any named repository, authoring framework, document filename, status token, language stack, or directory layout to discover architectural intent. The agent learns the repository's actual conventions at runtime. Existing historical fixtures and examples are not prerequisites and must not be used as default sources.

## Verification and limitations

- Evidence: current `SKILL.md` contents and script boundaries for every row; detailed inspection of `code-smell-monitor/scripts/requirement_interpretation.py`, its CLI integration, existing Python tests, and `handoff-context` invocation.
- Tests added to `code-smell-monitor/tests/test_requirement_architecture.py`: optional manifest compatibility, nested package with parent workspace source document, explicit path containment checks, and no implied source authority.
- Agent-behavior scenarios in `skills/code-smell-monitor/references/agent-interpretation.md` are a **test plan**, not evidence of a completed agent-level benchmark. A full new-vs-old multi-repository eval requires actual agent executions and should be assessed before merge.
- The concurrently open [PR #15](https://github.com/linmou/agentic-development-skills/pull/15) addresses Python Import Linter enforcement and JS/TS coverage. It is not merged or superseded. Reconcile any conflicts rather than silently overwriting it.
- Do not claim the portable invocation is directly shell-executable without resolving `<skill-root>`: the agent must substitute its installed skill directory.
