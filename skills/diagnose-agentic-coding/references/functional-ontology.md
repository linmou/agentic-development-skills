# Agentic Coding Functional Ontology v0.2

Use this ontology to generate and organize causal hypotheses about success and failure. It describes functions that the agentic coding system must realize; it does not assign functions exclusively to the model, harness, human, or tool.

## L1 functional system

| ID | Function | Diagnostic question |
| --- | --- | --- |
| 1 | Objective Alignment & Governance | Was the intended target made operational, preserved, bounded, and evaluated without distortion? |
| 2 | Problem & State Understanding | Did the system acquire and maintain an adequate model of the relevant code, environment, and causal problem? |
| 3 | Solution Formation | Did it generate, compare, select, and plan a suitable change? |
| 4 | Action Execution & Coordination | Did it realize the intended change correctly through available capabilities and coordinate dependent work? |
| 5 | Monitoring, Adaptation & Recovery | Did it detect trajectory deviations, interpret feedback, and adapt or escalate effectively? |
| 6 | Verification & Completion | Did it obtain sufficient evidence, assess all material conditions, and make a justified completion claim? |

## L2 functions

| ID | Function | Functional criterion | Common non-equivalent symptom |
| --- | --- | --- | --- |
| 1.1 | Task & Success Definition | Convert the request into a sufficiently explicit task, success claims, and relevant constraints. | Later goal drift; that belongs to 1.2 unless the initial definition caused it. |
| 1.2 | Objective Representation & Preservation | Maintain the intended objective and priorities across reasoning, tool calls, revisions, and long traces. | An unauthorized action; that is primarily 1.3. |
| 1.3 | Action Boundary & Autonomy Governance | Determine and respect permitted actions, escalation points, risk limits, and user authority. | A technically incorrect edit within scope; that is not a boundary failure by itself. |
| 1.4 | Evaluation Alignment & Integrity | Keep evaluators, proxies, rewards, and optimization behavior aligned with the real success conditions. | Incomplete testing caused only by poor coverage; that may be 6.1 or 6.3. |
| 2.1 | Information Acquisition & Observation | Acquire relevant, timely, and sufficiently reliable observations from files, tools, state, and feedback. | Misinterpreting correctly observed facts; that is 2.2 or 2.3. |
| 2.2 | System & State Representation | Maintain a coherent representation of architecture, dependencies, current state, and uncertainty. | Choosing a weak solution despite an adequate state model; that is in 3. |
| 2.3 | Problem & Causal Understanding | Explain the failure mechanism and which controllable change should affect it. | Merely failing to read a necessary file; that is 2.1. |
| 3.1 | Candidate Solution Generation | Produce a sufficiently diverse and relevant set of plausible solution strategies. | Selecting the wrong candidate from a good set; that is 3.2. |
| 3.2 | Solution Evaluation & Selection | Compare candidates against goals, constraints, risks, evidence, and likely effects. | A sound selection implemented badly; that is in 4. |
| 3.3 | Solution Design & Planning | Translate the selected strategy into coherent, dependency-aware, testable actions. | Tool invocation failure despite a sound plan; that is 4.1. |
| 4.1 | Capability & Interface Use | Select and invoke models, tools, APIs, commands, and interfaces correctly. | Incorrect code semantics after successful invocation; that is often 4.2. |
| 4.2 | Action & Change Realization | Make the intended changes accurately in the target system. | Merge or cross-component mismatch; that may be 4.3. |
| 4.3 | Coordination & Integration | Sequence, combine, and reconcile interdependent agents, components, changes, and outputs. | A locally wrong edit with no integration issue; that is 4.2. |
| 5.1 | Trajectory Monitoring & Feedback Assessment | Observe progress and interpret test, tool, verifier, and environmental feedback against the intended trajectory. | Knowing the deviation but failing to respond; that is 5.2. |
| 5.2 | Adaptation, Recovery & Escalation | Revise understanding, strategy, plan, tool use, or escalation when deviation is detected. | Initial bad planning before feedback exists; that is 3.3. |
| 6.1 | Verification Planning & Evidence Acquisition | Design and execute checks capable of producing relevant evidence for the success claims. | Correct evidence interpreted against a wrong criterion; that may be 1.4 or 6.2. |
| 6.2 | Outcome & Constraint Assessment | Judge whether the artifact and process satisfy intended outcomes and constraints. | Insufficient test breadth not recognized; that is 6.3. |
| 6.3 | Evidence Sufficiency & Coverage Assessment | Judge whether evidence covers material claims, risks, regressions, and uncertainty. | Communicating success despite knowing evidence is insufficient; that is 6.4 and possibly 1.4. |
| 6.4 | Completion Decision & Status Communication | Stop, continue, or escalate appropriately and communicate verified status, caveats, and residual work. | A hidden defect despite reasonable evidence; do not infer 6.4 without evidence available at decision time. |

## Core causal handoffs

Use handoffs as candidate edge deviations. Ask what information or constraint should have crossed the edge, whether it did, and whether the receiver used it.

| From | Relation | To |
| --- | --- | --- |
| 1.1 | grounds | 1.2 |
| 1.1 | defines evaluation target | 1.4 and 6.1 |
| 1.2 | supplies objective and selection criteria | 3.1 and 3.2 |
| 1.3 | constrains | 3.2 and 4.1 |
| 2.1 | supplies observations | 2.2 |
| 2.2 | supports explanation and design context | 2.3 and 3.3 |
| 2.3 | informs | 3.1 |
| 3.1 | supplies alternatives | 3.2 |
| 3.2 | selects strategy for | 3.3 |
| 3.3 | specifies intended actions | 4.1 |
| 4.1 | enables | 4.2 |
| 4.3 | coordinates and integrates | 4.2 |
| 4.2 | produces execution outcome | 5.1 and 6.1 |
| 5.1 | updates observations and signals deviation | 2.1 and 5.2 |
| 5.2 | requests new understanding, reconsideration, or rerouting | 2.1, 3.1, and 4.1 |
| 1.4 | aligns evaluation | 6.1 |
| 6.1 | supplies evidence | 6.2 |
| 1.2 and 1.3 | supply intended outcome and constraints | 6.2 |
| 6.2 | supplies assessment results | 6.3 |
| 6.3 | authorizes justified completion or demands more evidence | 6.4 or 6.1 |
| 6.2 or 6.3 | triggers recovery when failure or insufficiency is detected | 5.2 |

## Configuration hypotheses

A configuration deviation is a conditional interaction, not a vague claim that “many things contributed.” Express it as:

`factor A × factor B [× context C] -> altered mechanism -> outcome`

Examples include:

- compact context window × long trajectory -> loss of objective/state representation -> inconsistent edits;
- tool latency × weak monitoring -> premature retry -> duplicated or conflicting actions;
- incomplete task specification × evaluator proxy -> locally optimized artifact -> real requirement failure;
- parallel agents × ambiguous ownership -> overlapping edits -> integration conflict;
- high action autonomy × weak verification -> large unvalidated change -> unsafe completion.

Treat these only as examples. Generate case-specific configurations from evidence.

## System-level success relation

Objective Alignment & Governance and Problem & State Understanding jointly constrain Solution Formation. Solution Formation specifies Action Execution & Coordination. Execution changes the system state. The resulting state produces observations for Monitoring, Adaptation & Recovery, which can update understanding, revise the solution, or reroute execution. Objective Alignment defines the claims that Verification & Completion must assess. Successful agentic coding requires both a satisfactory resulting state and sufficient evidence for a legitimate completion decision.
