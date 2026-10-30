---
name: experiment-log-writer
description: Create or update Markdown experiment logs that preserve scientific provenance and reproducibility. Use when recording experiment plans, commands, configurations, inputs, outputs, results, follow-up research questions, or when extending an existing experiment log after a run or analysis.
---

# Experiment Log Writer

Produce a durable research record, not a narrative summary. Start from
`assets/experiment-log-template.md` and retain every required section.

When another skill calls this writer, use the versioned Request/Response in
`references/call-contract.md`. The same procedure also works when invoked alone.
This skill owns log creation and edits. The caller supplies facts and decides
when to invoke it; this skill does not run experiments or commit changes.

## Workflow

1. Locate the target log and nearby experiment logs. Read any previous experiment log that the new research question cites or clearly derives from.
2. Separate supplied facts from missing information. Do not invent commands, results, timestamps, commit IDs, configurations, or causal explanations. Mark an unavailable required value as `Unknown` and state what would resolve it.
3. Create a new log from the template, or update the existing log in place according to the update rules below.
4. Cross-check identifiers: each research question has an `RQ` ID, each hypothesis names its `RQ`, and each result names the hypothesis or question it informs.
5. Record the canonical experiment-results address. Use `Not produced` only before execution; otherwise record the stable path, URL, object-store URI, or experiment-tracker run URL where the results can be retrieved.
6. Verify that commands are exact, multiline shell blocks include their working directory and environment, and executed commands include status and outcome evidence.
7. End with evidence-grounded Next Research Directions. Separate direct follow-ups from speculative ideas.
8. Return the contract response after writing, including the hypothesis IDs assigned by a `plan` entry. If required execution facts are missing, return `needs_input` without adding a misleading execution or result entry.

## Required Sections

Keep these sections in every experiment log:

- `Research Questions`
- `Hypotheses`
- `Execution Commands`
- `Results`
- `Iterations` when an experiment has iteration records
- `Next Research Directions`

Also retain the experiment-results address, metadata, changed factors, environment, inputs, outputs, and artifacts when they affect interpretation or reproduction.

## Research Questions And Provenance

Label each question `RQ1`, `RQ2`, and so on. Record its origin immediately below it:

- For a new question, write `Origin: New question`.
- For a question derived from prior results, write `Origin: Derived from [previous experiment log](relative/path.md)` and summarize the specific result that motivated it.

Use a relative Markdown link to the previous experiment log whenever repository layout permits. Never use a vague phrase such as “previous run” when a document path is known. A derived question without a previous-log reference is incomplete.

## Hypotheses

Write a falsifiable prediction for each hypothesis and link it to one or more research-question IDs. Include the expected observation and the observation that would reject it. Do not rewrite a post-hoc explanation as though it were a preregistered hypothesis; label it as post-hoc.

## Execution Commands

Distinguish commands by status:

- `Planned`: specified but not run.
- `Executed`: run as written; include timestamp, working directory, relevant environment or environment-file reference, exit status, and output or log path.
- `Modified during execution`: retain the planned command and add the exact executed command plus the reason for the change.

Preserve command ordering. Include setup, data preparation, experiment, evaluation, and analysis commands needed to reproduce the stated results. Redact secrets by naming the environment variable, never by recording its value.

## Results

Record one canonical `Results address` in the log metadata. Prefer a repository-relative path for repository artifacts; otherwise use a resolvable URL, object-store URI, experiment-tracker run URL, or an absolute path with enough storage or host context to locate it. If results span multiple locations, point the canonical address to an index or manifest and list the individual evidence paths under each result. Never record credentials or signed secret URLs.

Use `Results address: Not produced` for a planned experiment. Replace it with the actual address after any completed, failed, or partial execution that produced results or diagnostic evidence. If an address is unavailable, write `Unknown` with the reason and the recovery action instead of omitting the field.

Record failures and partial runs as results. For each result, identify the input or dataset version, configuration, output or artifact path, metric definition, observed value, and the RQ or hypothesis informed. Preserve representative input-output pairs when outputs are qualitative or model-generated.

Do not claim that a hypothesis is supported without tying the claim to recorded evidence. Distinguish observation from interpretation.

## Updating Existing Logs

Preserve prior commands, results, provenance, results addresses, and metadata. Append a dated execution or analysis entry instead of replacing historical evidence. If an existing statement is wrong, keep it readable and add a dated correction explaining what changed and why. When results move, record the new canonical address and retain the old address in the dated correction or migration note.

Update status fields as work progresses, but do not relabel a planned command as executed unless it ran exactly as recorded. When a command changes, preserve both versions. Add newly discovered research questions with their own origin; if they arise from this log, link to this log as their previous experiment log when moving them into a later document.

## Next Research Directions

For each direction, state:

- the evidence or unresolved result motivating it;
- the proposed next research question;
- the factor to change and factors to hold constant;
- the evaluation needed to answer it.

Prioritize directions that discriminate between competing explanations. Do not present routine engineering work as a research direction unless it resolves a stated uncertainty.
