# Coding Lens

**Intent:** Coverage prompts for software-change tasks, adapted from `diagnose-agentic-coding`. For deep coding diagnoses, that skill remains available with its own fixed L1 and artifact ontology; see the aliases in [../meta-ontology.md](../meta-ontology.md).

| Prompt | Coverage question |
| --- | --- |
| Repository state | Is environment state grounded by commits, hashes, snapshots, migrations, or deployment IDs, separate from the agent's belief state about the repo? |
| Trace vs environment state | Can observations and claimed edits in the trace be checked against the resulting repository state? |
| Solution specification | Is there a type for the intended change, distinct from the diff actually applied? |
| Test and verification evidence | Are test runs typed as evidence about environment state, with their coverage, rather than as the state itself? |
| Completion criterion | Does completion evidence compare the objective to resulting state, not to "tests pass" alone? |
| Scaffold configuration | Are AGENTS.md, skills, project rules, and tool policies typed as versioned inputs with in-context and use evidence? |
| Working directory and identity | Is repository or environment identity explicit, so wrong-target modifications can be expressed? |
| Development method | If the method (for example test-first) changes which artifacts verification consumes, is that expressible? |
