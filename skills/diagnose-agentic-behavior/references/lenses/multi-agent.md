# Multi-Agent Lens (MAST)

**Intent:** Coverage prompts for systems with delegation, subagents, or peer agents, using the 14 failure modes of the MAST taxonomy (source in [README.md](README.md)). For each mode, ask whether the task ontology has the types needed to express it if it happened.

| MAST category | Failure mode | Coverage question |
| --- | --- | --- |
| FC1 System design issues | FM-1.1 Disobey task specification | Is the task specification each agent received typed, with in-context evidence? |
| | FM-1.2 Disobey role specification | Is each agent's role, scope, and authority typed as an artifact? |
| | FM-1.3 Step repetition | Can repeated actions be distinguished from intended retries? |
| | FM-1.4 Loss of conversation history | Can context lost between turns or agents be expressed as an Edge? |
| | FM-1.5 Unaware of termination conditions | Are termination conditions typed and delivered to the agents that need them? |
| FC2 Inter-agent misalignment | FM-2.1 Conversation reset | Can a restart that drops accumulated context be expressed? |
| | FM-2.2 Fail to ask for clarification | Is the option to ask a human or another agent typed as a decision point? |
| | FM-2.3 Task derailment | Can work that drifts from the assigned task be compared with the specification? |
| | FM-2.4 Information withholding | Can a message that omits information the sender had in context be expressed? |
| | FM-2.5 Ignored other agent's input | Can an input that was in context but not used be recorded? |
| | FM-2.6 Reasoning-action mismatch | Can an agent's stated reasoning be compared with the action it took? |
| FC3 Task verification | FM-3.1 Premature termination | Is completion evidence typed separately from the completion claim? |
| | FM-3.2 No or incomplete verification | Is a verification action expected, so its absence is an error of omission? |
| | FM-3.3 Incorrect verification | Can a verification result be checked against environment state? |

Also check that shared state (files, boards, memory) is versioned and that the action merging agents' results is typed, so errors introduced during aggregation are distinguishable from upstream errors.
