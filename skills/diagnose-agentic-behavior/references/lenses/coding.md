# Coding Lens

**Intent:** Coverage prompts for software-change tasks, adapted from `diagnose-agentic-coding`. For deep coding diagnoses, that skill remains available and uses this vocabulary as its fixed ontology.

| Prompt | Coverage question |
| --- | --- |
| Repository state | Is World grounded by commits, hashes, snapshots, migrations, or deployment IDs, separate from the agent's belief about the repo? |
| Execution record vs state | Can tool returns and claimed edits be checked against the resulting repository state? |
| Solution specification | Is there a type for the intended change, distinct from the diff actually applied? |
| Test and verification evidence | Are test runs typed as evidence about World, with their coverage, rather than as World itself? |
| Completion criterion | Does completion evidence compare the objective to resulting state, not to "tests pass" alone? |
| Configuration | Are AGENTS.md, skills, project rules, and tool policies typed as versioned inputs with delivery and use evidence? |
| Working directory and identity | Is repository or environment identity explicit, so wrong-target modifications can be expressed? |
| Development method | If the method (for example test-first) changes which artifacts verification consumes, is that expressible? |
