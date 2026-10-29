# Optional trace check (high-stakes callees)

Intent: static checks show a caller *could* supply a valid Request; local agent sessions show whether, at the moment of each real call, the context *did* contain the facts it sent. This tier is optional and suggested only for high-stakes callees.

## When to suggest it

Set `high_stakes: true` in the callee's `contract.json`, and suggest this tier in the report, when any holds:

- the callee writes durable or shared state (logs, datasets, ledgers, records others build on);
- its output feeds a decision or evaluation (results, judgments, release gates);
- it takes actions that are hard to reverse;
- it has many callers, or callers that decide at runtime whether to call it.

Run it only when the user agrees. Otherwise write `suggested, not run` in the report.

## Prerequisites

- Callers emit the explicit Request block (`contract-format.md` §5). Without it, the sent Request must be reconstructed from prose and file edits; mark such calls `reconstructed` and never fail a caller on a reconstructed call alone.
- The user names the session folders to read. Session formats differ by agent and change between versions; write a small, local adapter per format rather than assuming one. Do not commit adapters that embed private paths.

## Procedure

1. **Select** — Find sessions that loaded the callee (a skill invocation, or a read of its `SKILL.md`). Keep a window from session start to the callee's response for each call.
2. **Match version** — Hash the callee `SKILL.md` text the session read, when present, and compare it with the current file. Judge only matching calls; list the rest as `stale`.
3. **Extract calls** — For each call record: caller skill, Request, Response status, and what the caller did next.
4. **Trace provenance** — For every field the Request sets, find the earliest source in the window: user message, tool output, file content, or a value fixed by the caller's procedure. A value with no source is `unsourced`. Exact or near-exact matches can be found mechanically; judge the rest by reading.
5. **Check status handling** — For each non-success status, confirm the next actions follow the caller's documented handling and do not claim the write happened.
6. **Record** — Fill the trace section of the report: calls examined, stale, reconstructed, unsourced fields, mishandled statuses.
7. **Harden** — Turn every confirmed failure into a call example or fixture, so the static tier catches it next time.

## Verdict effect

- An `unsourced` required field or a mishandled status in a matched, non-reconstructed call fails V3 or V4 for that caller.
- Clean traces never upgrade a static `fail` or `insufficient_evidence`: traces only cover situations that happened.

## Privacy

Sessions contain credentials, personal data and unrelated work. Read them locally, quote only the fields under review, redact secrets in the report, keep outputs in `out_dir`, and never commit trace excerpts.
