# Contract format (`skill-contract/1`)

Intent: give a callee skill one machine-readable, versioned contract that callers declare against, so dependencies can be checked mechanically instead of read from prose.

A contract has three parts, owned by different skills:

| Part | Owner | File |
|------|-------|------|
| Contract | callee | `<callee>/contract.json` |
| Dependency declaration | caller | `metadata.requires` in the caller's `SKILL.md` frontmatter |
| Call examples | caller | `<caller>/references/calls/<callee>/*.json` |

The callee's prose contract (for example `references/call-contract.md`) stays the authority for meaning. `contract.json` is its checkable projection; the two must agree.

---

## 1. Callee: `contract.json`

```json
{
  "contract_format": "skill-contract/1",
  "skill": "note-store",
  "version": "1.0.0",
  "capability": "Store a plain-text note and return its id.",
  "prose_contract": "SKILL.md#call-contract-v1",
  "request": { "type": "object", "required": ["text"], "properties": { "text": { "type": "string", "minLength": 1 } } },
  "response": { "type": "object", "required": ["status"], "properties": { "status": { "enum": ["ok", "error"] } } },
  "status_field": "status",
  "statuses": ["ok", "error"],
  "writes": [{ "store": "notes", "location": "notes/<note_id>.json" }],
  "high_stakes": false,
  "changes": [{ "version": "1.0.0", "note": "Initial contract." }]
}
```

| Key | Required | Meaning |
|-----|----------|---------|
| `contract_format` | yes | Always `skill-contract/1` for this format. |
| `skill` | yes | Callee skill name; must equal the folder and `SKILL.md` `name`. |
| `version` | yes | Semantic version `MAJOR.MINOR.PATCH`. Bump MAJOR when a valid old Request may now fail, a status disappears, or a field changes meaning. |
| `capability` | yes | One line: the reusable job, never a host state. |
| `prose_contract` | yes | Path (optionally `#anchor`) of the human contract, relative to the callee folder. |
| `request` | yes | Request schema (JSON Schema subset, §4). |
| `response` | yes | Response schema (JSON Schema subset, §4). |
| `status_field` | yes | Response key carrying the status. |
| `statuses` | yes | Every status the callee can return. Callers must handle each one. |
| `writes` | yes | Stores the callee owns and writes. `[]` for a read-only skill. Each item: `store` (stable id, unique across all contracts), `location` (path pattern or `request.<field>` when the caller chooses the path). |
| `high_stakes` | no | `true` when the trace tier is recommended (see `trace-check.md`). Default `false`. |
| `changes` | yes | Changelog, newest last; the last entry's `version` equals `version`. |

Rules:
- The callee alone writes its `writes` stores. A second contract claiming the same `store` id is an error.
- Opaque fields such as `caller_tag` may appear in `request`; the prose contract must say they are log-only.
- Conditional rules the subset cannot express (for example "if `prior_log` then `prior_result`") stay in the prose contract and are checked by the semantic pass, not the script. Do not invent schema keywords to encode them.

## 2. Caller: dependency declaration

Declare in `SKILL.md` frontmatter under the spec's `metadata` map (string values only), so the skill stays valid for any Agent Skills client:

```yaml
---
name: meeting-notes
description: ...
metadata:
  requires: note-store@^1.0.0, other-skill@~2.1.0
---
```

- One entry per callee: `<skill>@<range>`, comma-separated.
- Ranges: `^1.2.0`, `~1.2.0`, `>=1.2.0 <2.0.0`, `=1.2.0`, `1.2.0`, `*`. Space-separated comparators are ANDed.
- A caller that invokes a callee without declaring it is reported as an undeclared caller.

## 3. Caller: call examples (consumer-driven tests)

Each declared caller ships at least one example per distinct way it calls the callee, at `references/calls/<callee>/<case>.json`:

```json
{
  "case": "save meeting summary",
  "request": { "version": 1, "text": "Ship the beta on Friday." },
  "provenance": {
    "version": "constant in Procedure step 2",
    "text": "meeting summary collected from the user in Procedure step 1"
  }
}
```

- `request` must validate against the callee's current `request` schema.
- `provenance` maps each field path the example sets to where the caller gets that value in its own workflow. Paths are dotted; array items use `[]` (`entry.commands[].command`). A prefix covers its subtree (`entry.design` covers `entry.design.controls`).
- Provenance text is free-form; the script checks coverage, the semantic pass checks that the source really exists in the caller's procedure.
- When the callee changes, these examples are the impact test: an example that fails the proposed schema names a caller that breaks.

## 4. Schema subset

Both `request` and `response` use this JSON Schema subset. Unsupported keywords are an error, so a contract never silently claims more checking than it gets.

`type` (`object`, `array`, `string`, `integer`, `number`, `boolean`, `null`, or a list), `properties`, `required`, `additionalProperties` (boolean), `items`, `enum`, `const`, `minLength`, `minItems`, `oneOf`, `anyOf`, `allOf`, `description`, `title`, `default`, `examples`.

## 5. Explicit Request block (recommended; required for the trace tier)

Before invoking a callee, the caller writes the Request as a fenced block:

````markdown
```skill-request note-store@1.0.0
{ "version": 1, "text": "Ship the beta on Friday." }
```
````

It costs one block per call, makes the call reviewable in the transcript, and is what the optional trace tier parses. Callers of a `high_stakes` callee should state this rule in their own procedure.
