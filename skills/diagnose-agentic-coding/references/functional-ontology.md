# L1 Functional Ontology

**Intent:** Define the functional view whose actions are decomposed into artifact production and consumption.

| ID | Function | Diagnostic question |
| --- | --- | --- |
| 1 | Objective Alignment & Governance | Was the intended outcome and its constraints made operational and preserved? |
| 2 | Problem & State Understanding | Was the relevant problem and system state adequately represented? |
| 3 | Solution Formation | Was a suitable intended change formed from the objective and current state? |
| 4 | Action Execution & Coordination | Were intended actions realized and dependent work coordinated? |
| 5 | Monitoring, Adaptation & Recovery | Did feedback lead to appropriate reconsideration, revision, or recovery? |
| 6 | Verification & Completion | Was success assessed with sufficient evidence and a justified completion status? |

## Functional graph

Objective alignment constrains understanding, solution formation, execution, monitoring, and verification. Understanding informs solution formation, execution, and verification. Solution formation specifies execution. Execution feeds understanding, monitoring, and verification. Monitoring routes adaptation to understanding, solution formation, and execution, with consumption by verification dependent on the development method. Verification feeds monitoring and completion, with consumption by solution formation and execution dependent on the development method.

These are functional dependencies. [artifact-flow.md](artifact-flow.md) supplies their artifact-mediated decomposition and case reconstruction rules. Each case graph must make the material dependencies concrete.

## Diagnostic anchors

Use an L1 node, a producer/consumer edge, an interaction, or a residual outside the representation. Configuration is represented through the same graph: it is the role/content of an artifact or an effective operating condition, not a fourth attribution category. Express interactions as `factor A × factor B → changed artifact/action mechanism → outcome`, with observable conditions. A defective configuration artifact is traced to its producing action; incorrect delivery is an edge problem; individually acceptable constraints that become incompatible together are an interaction.

Separate three diagnostic levels: failure localization (where a node, edge, or interaction deviated), causal provenance/origin (the upstream action, source, capability, policy, or external condition that produced it), and transferable mechanism (recurrence conditions and an intervention that addresses it). Rootness is bounded by the evidence and investigation boundary. Preserve multiple jointly necessary or amplifying causes and distinguish causal origin from intervention target. If no mechanism is sufficiently supported, report root cause undetermined rather than inferring one.

The six functions describe work that the system must realize. The responsible actor may be a human, model, harness, tool, evaluator, or a combination; infer that allocation from the case.

Case specificity comes from artifact content, versions, actions, and evidence. The archived [L2 taxonomy](archive/original-l2.mmd) illustrates possible subfunctions; it is not a required diagnostic traversal or attribution code.
