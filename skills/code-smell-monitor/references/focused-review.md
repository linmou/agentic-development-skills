# Focused redundancy review

Intent: cover independent source flows and tool-supported candidates without letting the first interesting finding consume the review.

Use this route for direct advisory reviews of redundancy, unused implementations or repeated execution. General quality scans and versioned caller-contract requests keep the general monitor workflow.

## Prepare evidence once

Discover the requested production scope, package roots and instructions. Resolve relevant project intent from source and existing documents as needed to validate a finding. Keep caller searches rooted in actual source, tests, scripts and server entrypoints.

For JS/TS, write or reuse an exact file manifest relative to the package root and run:

```text
python3 <this-skill>/scripts/focused_redundancy.py --repo <package-root> --scope-file <manifest> --out <output>
```

This prepares normal/production Knip, scoped clone detection, behavioral candidates and syntax-only source navigation. The overview lists bounded page paths, counts and continuations; read pages separately. Inspect statuses and missing coverage first. A partial result can still supply usable evidence: preserve gaps and continue source review instead of repeatedly repairing or rerunning unchanged analyzers. Raw records remain linked for a concrete question. A source/navigation record is not a finding. For other stacks, use existing equivalent tools and the same review sequence; unavailable evidence stays explicit.

## Cover breadth before depth

First read all compact source-file summary pages; expand function/hook navigation only for the files being investigated, using the linked detail pages. Group files by responsibilities supported by their declarations and entrypoints. Track only compact IDs/spans with a status: inspect, supported, rejected or deferred. Keep remaining candidate page IDs and unread scope groups visible; stopping before completion is partial coverage.

Before detailed investigation, perform an independent source pass over the responsibility groups, including groups without detector candidates. Read complete relevant functions and hook calls using the supplied spans; a hook's callback, dependencies and cleanup belong to one unit. Trace values through transformations to their consumers, and triggers through callbacks, resource operations and state writes to downstream effects. Check branch-exclusive work, discarded or recomputed values, repeated policy/configuration construction and ownership across caller/callee boundaries. These are questions, not evidence of a smell.

Use a breadth-first first pass: inspect at least one relevant complete unit from each responsibility group before revisiting an already covered group for a deeper hypothesis. Choose the unit from actual entrypoints and code, not filenames alone. This is a coverage floor, not exhaustive review. Reuse captured spans; fetch missing boundaries instead of reloading whole files. Preserve the group/span inventory in a compact coverage table.

Then read every candidate page, triaging file-level unused implementations, export/type candidates, clones and execution signals across the scope before choosing deeper investigations. A large candidate family must not crowd out the others. In particular, retain the full-scope clone and unused-file inventories even when a selected source flow already yielded useful findings.

## Validate and reconcile

For each plausible finding, check its actual producer/consumer or execution path. For unused-code candidates inspect both Knip modes and production, test, dynamic, server and external consumers. For clones compare responsibilities and semantic differences. For repeated work inspect inputs, ordering, mutation, freshness, cancellation, retries and recovery. Rejection closes only that mechanism, not every other question in the enclosing function.

Retain source-supported in-scope findings even when impact is small. Low priority and insufficient evidence are different dispositions. Distinguish observed waste/duplication from uncertainty about a safe refactor. Do not infer safe deletion or behavior-preserving change from static evidence. A finding needs a concrete maintenance or execution consequence, not only an aesthetic preference or detector count.

Before finishing, revisit the compact coverage table and every candidate family. Resolve remaining high-value checks within the assigned budget; mark unresolved candidates and uninspected groups explicitly. There is no finding quota. Do not spend the remaining budget polishing already supported findings while entire groups are still untriaged.

## Report once

Write detailed findings once in `code_smell_report.md`, grouped by mechanism, with exact locations, concise evidence, consequence, confidence and caveat. Aim for about100words per finding; use more only for a necessary causal boundary. Include concise rejected/deferred candidates, coverage, command/status references and timing. Preserve raw outputs without copying whole source excerpts into multiple reports.

The runner's `summary.json` remains the tool evidence record. Add only finding IDs, locations and report links for agent interpretation; if `report.md` is requested, make it an index. Report visited/total pages and uninspected responsibility groups separately from validated findings. Categories outside the focused review are not assessed. This focused summary is not a replacement for the general monitor's versioned invocation result.
