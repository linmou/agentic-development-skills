# Caller verify rubric (V1–V7)

Intent: decide, per caller, whether it can call the callee correctly using only the contract. The script answers the mechanical half; this rubric covers what only reading the caller can show.

Score each caller on its own. Verdicts: `pass` | `fail` | `insufficient_evidence`; V7 is `pass` | `warn`. Every verdict cites a file path and line or quote, and for `pass` names one counterexample you looked for and did not find.

Read for each caller: its `SKILL.md`, its `references/`, its call examples, and the callee's prose contract. Do not read callee internals to excuse a caller; if the caller only works because of undocumented callee behaviour, that is a V6 fail.

---

## V1 — Declared and compatible (blocking)

- `metadata.requires` names the callee with a range that includes the contract version (script: `version-mismatch`, `requires-unresolved`).
- For a script `undeclared-caller` warning, decide whether the text is a real call. Prose that only names the callee ("do not use X", history, comparison) is not a call: note it and pass. A real call without a declaration fails.

## V2 — Request fit (blocking)

- There is a call example for each distinct way the caller invokes the callee (each `kind`, mode or profile it uses).
- Examples validate against the schema (script: `example-invalid`).
- Examples also satisfy the prose contract's conditional rules the schema subset cannot express (paired fields, required-if rules, value meanings).
- Examples match the caller's procedure: the procedure would actually produce this shape. An example that is cleaner than what the procedure sends fails.

## V3 — Field provenance (blocking)

- Each provenance entry names a source that exists in the caller's procedure or inputs: a step that collects it, a tool output, a file, or a user answer.
- No required field depends on the agent guessing. Phrases such as "infer", "fill in", "use a reasonable value" for a fact the caller never observes fail V3.
- When a source can be missing, the caller says what happens (ask the user, send without the optional field, or expect `needs_input`), not "make one up".

## V4 — Status handling (blocking)

- Every status in the contract has an action in the caller's text (script: `status-unmentioned` is a lead).
- The caller never continues as if a non-success status succeeded: no commit, report or next step claims a write that did not happen.
- Retries are bounded and change the Request (supply the missing facts); blind retries of the same Request fail.

## V5 — Single writer (blocking)

- The caller never edits a store listed in the callee's `writes`, including "fallback", "quick fix" or audit paths.
- The caller does not redefine Request or Response field meanings or add its own required fields to the callee's Response.

## V6 — Contract-only coupling (blocking)

- The caller relies only on the contract: no reading callee templates, scripts or internal files to construct a Request or interpret a Response.
- Opaque fields (`caller_tag`, correlation ids) carry no control meaning in either direction.
- The caller does not require callee behaviour the contract does not promise (ordering, side files, timing).

## V7 — Call hygiene (non-blocking)

- The caller points to the callee's prose contract and names the version it was written against.
- For a `high_stakes` callee, the caller emits the explicit Request block before each call (`contract-format.md` §5).
- List misses as fixes; V7 never changes the verdict.

---

## Caller verdict

`fail` if any of V1–V6 fails; `insufficient_evidence` if any of V1–V6 lacks evidence (for example, no call example exists); otherwise `pass`.

## Common failure patterns

1. Example written to pass the schema, not taken from the procedure (V2).
2. "Fill the metadata" instructions that turn missing facts into invented ones (V3).
3. Success path only: `needs_input` is never mentioned, so the caller commits anyway (V4).
4. Audit or recovery step that edits the callee's file "just this once" (V5).
5. Caller opens the callee's template to build the Request (V6).
