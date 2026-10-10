# Multi-Agent Lens

**Intent:** Coverage prompts for systems with delegation, subagents, or peer agents.

| Prompt | Coverage question |
| --- | --- |
| Role contract | Is each agent's assigned role, scope, and authority typed as an artifact with delivery evidence? |
| Delegation brief | Is the brief a subagent received distinct from what the delegator intended? |
| Context transfer | Can loss, truncation, or staleness of context between agents be expressed as an Edge? |
| Return report | Is a subagent's report typed as Record, checkable against World? |
| Shared state | Is shared state (files, boards, memory) versioned, with concurrent writes expressible? |
| Coordination | Can duplicated, conflicting, or orphaned work be expressed? |
| Aggregation | Is the step that merges results typed, so errors introduced there are distinguishable from upstream errors? |
| Escalation | Can the option to ask a human or another agent, and the choice not to, be expressed? |
| Per-agent task models | If agents may hold different views of the task, can each be recorded as a Belief-layer artifact? |
