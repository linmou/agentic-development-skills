# Claim decomposition

**Artifact:** `/Users/admin/.codex/skills/ecological-forward-test/`  
(SKILL.md + references/ecological-cases.md, failure-labels.md, root-reason.md, agents/openai.yaml)

**Claim:** The ecological-forward-test skill is complete enough to run ecological case generation, forward testing, failure summarizing, root-reason analysis, and continued improvement (surgical patch loop) across agent harnesses, without critical missing procedure.

**feature_name:** ecological_forward_test  
**phase:** green

## Criteria

| id | text | blocking |
|----|------|----------|
| c1 | Ecological case generation is defined and required as the primary suite (not lab-only explicit $skill prompts). | true |
| c2 | Forward-test integrity is specified (fresh threads, no gold leakage, runner not told it is testing). | true |
| c3 | Failure labeling rules are complete, checkable, and ban invented jargon / overloaded bare nouns. | true |
| c4 | Root-reason analysis covers layered causes and maps to caller vs callee vs harness. | true |
| c5 | Continued improvement includes surgical edition scope limits that prevent brutal full-skill rewrites. | true |
| c6 | Guidance is harness-agnostic enough to apply beyond a single CLI (Codex/Grok/others). | true |
| c7 | No critical operational gap remains for a competent agent to finish a full loop (cases → score → label → root → patch → re-run → handoff). | true |
