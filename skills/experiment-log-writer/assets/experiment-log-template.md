# Intent

Record the question, execution, evidence, and follow-up needed to interpret and reproduce one experiment.

# Experiment: <short descriptive title>

## Metadata

- Log status: <planned | running | completed | failed | partial>
- Created: <ISO-8601 timestamp and timezone>
- Updated: <ISO-8601 timestamp and timezone>
- Author or agent: <name>
- Repository: <repository identifier>
- Initial source commit: <full commit ID at log creation, or Unknown with reason>
- Working directory: <path>
- Results address: <Not produced | repository-relative path | URL | object-store URI | experiment-tracker run URL | Unknown with reason and recovery action>

## Research Questions

### RQ1: <question>

- Origin: <New question | Derived from [previous experiment log](relative/path.md)>
- Prior result motivating this question: <result summary, or Not applicable>
- Answer criterion: <evidence needed to answer the question>

## Hypotheses

### H1 (addresses RQ1): <falsifiable prediction>

- Expected observation: <prediction>
- Rejection observation: <outcome that rejects H1>
- Status: <preregistered | post-hoc>

## Experiment Design

- Independent factor changed: <factor and levels>
- Factors held constant: <controls>
- Data or inputs: <dataset, split, version, checksum, or artifact path>
- Evaluation method: <metric definition and procedure>
- Stopping rule: <rule>
- Known confounders: <items or None known>

## Execution Commands

### Command 1: <purpose>

- Status: <Planned | Executed | Modified during execution>
- Timestamp: <ISO-8601 timestamp and timezone, or Not executed>
- Working directory: <path>
- Environment: <runtime, dependencies, hardware, and environment-file reference>
- Exit status: <integer, signal, or Not executed>
- Output or log: <path, or Not executed>

```bash
<exact command>
```

## Results

### Result 1: <short label>

- Informs: <RQ1 and/or H1>
- Run status: <completed | failed | partial>
- Input: <exact input, dataset slice, or artifact reference>
- Configuration: <config path and relevant overrides>
- Output: <exact output, representative output, or artifact reference>
- Metric and value: <definition and observed value>
- Observation: <what the evidence directly shows>
- Interpretation: <what it may mean>
- Evidence path: <log, table, checkpoint, plot, or result file beneath or associated with the Results address>

## Iterations

### Iteration 1: <ISO-8601 timestamp and timezone>

- Hypothesis: <H ID, or Unknown with reason>
- Source commit: <full commit ID of the revision used for this run, or Unknown with reason>
- Files or configs changed: <paths and changed factors, or Unknown with reason>
- Commands: <Command IDs above, including any deviations>
- Results: <Result IDs above, including failures or partial runs>
- Decision: <support | reject | inconclusive | revise, with evidence>
- Revision note: <change to hypothesis or plan, or None>

## Corrections And Deviations

- <dated correction, command deviation, or None>

## Analysis Notes

- <dated observation, interpretation, and any later iteration commit reference, or None>

## Next Research Directions

### Direction 1: <next question>

- Motivating evidence: <result or unresolved issue>
- Factor to change: <factor>
- Factors to hold constant: <controls>
- Evaluation: <test or measurement>
- Priority: <high | medium | low, with reason>
