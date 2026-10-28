# Architecture follow-up validation

Tracking: https://github.com/linmou/agentic-development-skills/issues/11

This change adds source-grounded requirement associations and a static Python
adapter. It retains PR 1's distinction between structural facts, review candidates,
and violations of explicitly configured rules. Requirements never alter enforcement.

## Reproduce the offline checks

From the repository root, with Python 3.10+ and pytest installed:

```sh
python3 -m unittest discover -s skills/code-smell-monitor/tests -v
python3 -m py_compile skills/code-smell-monitor/scripts/*.py
python3 -m pytest -q
```

The code-smell-monitor suite covers actual Python CLI graph/report production,
functional and quality source mappings, exact-quote and source-hash preservation,
stale/missing/escaping sources, missing uncertainty, mixed-adapter coverage,
missing TypeScript representation, ambiguous/dynamic/unresolved Python imports,
large cycles, and enforcement behavior. All 30 monitor unittest tests passed.

The broader repository suite completed with **635 passed, 2 failed**. It retains two previously observed failures in
`fast-multi-agent-tdd/tests/test_skill_configuration.py`:

- `test_post_review_test_correction_has_an_authenticated_pre_edit_order`
- `test_bounded_recovery_contract_is_consistent_and_does_not_weaken_red_debate`

They assert exact phrases absent from existing skill documents. This change does
not modify those documents or weaken the assertions.

## Real project graph and requirement pipeline

Target: `linmou/PhishingTrainingProgram`, commit
`359828f43a6fe9a5f97de298bea6c0730929e819`, package root `tutor-system`.
Tools: Node 24.19.0, dependency-cruiser 17.3.1, TypeScript 5.9.3, Python 3.12.14.

The isolated target checkout's frontend dependencies were installed with
`npm ci --ignore-scripts --no-audit --no-fund`. The nested `functions` package
has no lockfile, so it used
`npm install --package-lock=false --ignore-scripts --no-audit --no-fund`.
No tracked target files changed. No target application, database, or deployment
was started. The functions package declares Node 18 and emitted an engine warning;
this validation only parsed source and resolved imports, and does not establish
Node 24 runtime compatibility.

Install dependency-cruiser and TypeScript together in an isolated tools directory,
place its `node_modules/.bin` on PATH, then run (adjust absolute paths):

```sh
python3 /path/to/agentic-development-skills/skills/code-smell-monitor/scripts/code_smell_monitor.py \
  --repo /path/to/PhishingTrainingProgram/tutor-system \
  --architecture-only --install never \
  --requirements /path/to/agentic-development-skills/skills/code-smell-monitor/references/examples/ptp-requirements.json \
  --out /path/to/validation-report
```

The example mapping quotes the current result identity/persistence and privacy
contracts, not the target repository's historical spec sections. Its module
mapping is analyst-supplied and does not prove impact. The measured import cycle
between `supabase.ts` and `transferAssessmentService.ts` warrants investigation;
dynamic imports in that cycle do not establish a runtime initialization failure.

Observed result:

- JS/TS: 338 repository/linked modules, 791 internal edges, 18 findings.
- Every discovered JS/TS source file was represented in the graph.
- Six imports remained unresolved: two references to `@cucumber/cucumber`, three
  to `@jest/globals`, and one Deno `https://esm.sh/` import. Coverage is **partial**.
- Python: one file parsed, no internal edges or structural findings.
- Two sourced requirements produced six associations, all impact hypotheses
  retaining source quotation/hash, rationale, evidence and uncertainty.
- No configured error-rule violations; default command exited 0 with coverage
  warnings. `--fail-on-tool-error` is intended to reject this partial coverage.

Separate real dependency-cruiser fixtures verify that high-degree review metrics
remain advisory, a configured warning rule exits 0, and the same rule configured
as `error` exits 1. Offline regression tests also exercise strict coverage failure.

This validates the architecture/interpretation pipeline, not target application
behavior, security compliance, requirement satisfaction, or complete import coverage.
