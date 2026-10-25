# Canonical Diagnostic Definitions

**Intent:** Define where a failure operates, how its causal mechanism is attributed, and how any generalization is bounded.

## Node, Edge, and Interaction

These concepts describe **where and how a failure mechanism operates**, not necessarily its ultimate causal origin.

### Node: Action Transformation

**Definition:** A Node is a concrete `(actor, action)` event, classified by an L1 functional category. It consumes available inputs and may produce artifacts, modify System State, or both.

**Node failure:** An action produces an inappropriate result relative to a supported case-specific expectation.

**Is:**

- Incorrect interpretation or use of an available artifact.
- Incorrect reasoning, decision-making, execution, or verification.
- Incorrect artifact production or System State modification.

**Is not:**

- An L1 function alone, without a concrete action instance.
- Automatically responsible for an incorrect output when its input was already defective.
- Automatically a model failure; actors may include agents, humans, harnesses, tools, or evaluators.

### Edge: Artifact Handoff

**Definition:** An Edge represents the transfer or provision of an identifiable artifact instance from its source to a consuming action.

The abstract ontology defines **potential semantic dependencies**. A case graph reconstructs actual or potentially missing handoffs.

**Edge failure:** A causally relevant artifact handoff is missing or defective.

**Is:**

- Missing delivery of a needed artifact.
- Incorrect routing, truncation, or version delivery.
- Failure to make a relevant artifact available to its intended consumer.

**Is not:**

- A mandatory workflow transition.
- A failure merely because a potential dependency was not exercised.
- Incorrect interpretation of an artifact that was correctly delivered; that belongs to the consuming Node.

### Interaction: Joint Causal Mechanism

**Definition:** An Interaction is a causal mechanism in which the effect of one factor depends on another factor or combination of factors.

Factors may include artifacts, Nodes, Edges, System State, capabilities, or operating conditions.

**Is:**

- A failure arising from incompatible instructions and tool constraints.
- A failure dependent on the combination of a model behavior and harness policy.
- A mechanism whose outcome changes when the relevant combination changes.

**Is not:**

- A third kind of physical graph location.
- Mere coexistence of multiple errors.
- A sequential causal chain without evidence of joint dependence.
- Necessarily a combination of individually correct factors.

Node and Edge identify structural locations. Interaction identifies a causal relationship involving one or more such locations and other factors. These classifications may coexist.

Configuration is not an additional attribution category. Configuration information can be represented as artifacts, operating conditions, or properties of actions and handoffs.

## Multi-Level Failure Attribution

The diagnostic method has three distinct levels. Each answers a different question.

### Level 1: Error Location

**Definition:** Identify the concrete action, artifact handoff, or interaction where an observed deviation arose or manifested.

**Question:** *Where and how did the observed behavior deviate from what was required?*

**Is:**

- Locating relevant Node and Edge instances.
- Identifying affected artifact versions and System State transitions.
- Establishing deviations using case-specific expectations and evidence.

**Is not:**

- Automatically identifying the upstream root cause.
- Assigning responsibility to the actor at the error location.
- Treating unused potential edges as failures.

**Output:** Localized failure mechanism(s), evidence, and uncertainty.

### Level 2: Root Causal Mechanism

**Definition:** Trace the localized failure upstream to the deepest evidence-supported causal mechanism(s), within the investigation boundary, that explain why the failure occurred.

**Question:** *Why did this failure occur, and what produced or enabled the causal mechanism?*

**Is:**

- Tracing causal provenance through artifacts, actions, actors, capabilities, and operating conditions.
- Considering origins such as user instructions, model capabilities or behavioral tendencies, harness design, and third-party environments.
- Preserving competing explanations, multiple causes, and interactions.
- Using evidence and discriminating tests to evaluate causal claims.

**Is not:**

- Simply identifying a defective artifact.
- Necessarily finding one responsible actor.
- Tracing indefinitely to the earliest event.
- Assuming the most upstream actor is responsible.
- Equating the root cause with the easiest intervention target.
- Claiming a root cause when the evidence supports only hypotheses.

**Output:** Supported or provisional causal mechanisms, their provenance, competing explanations, and unresolved upstream causes.

When evidence is insufficient, report **root cause undetermined** rather than inventing an explanation.

### Level 3: Generalization Conditions

**Definition:** Identify the conditions under which a supported or hypothesized causal mechanism could recur in other tasks, agents, workflows, or environments.

**Question:** *When would the same causal mechanism produce similar failures again?*

**Is:**

- Identifying transferable behavioral or system-level mechanisms.
- Specifying relevant capability, artifact, configuration, task, and environmental conditions.
- Defining recurrence predictions and possible preventive interventions.
- Distinguishing observed transferability from hypotheses requiring validation.

**Is not:**

- Assuming that one observed failure proves a stable model tendency.
- Claiming a mechanism applies to every task or model.
- Merely repeating the original incident at a more abstract level.
- Treating a proposed intervention as empirically validated.

**Output:** Generalization conditions, confidence limitations, testable recurrence predictions, and potential interventions.

## Relationship Between the Levels

| Level | Primary object | Main result |
| --- | --- | --- |
| 1. Error Location | Node / Edge / Interaction | Localized deviation |
| 2. Root Causal Mechanism | Causal provenance and mechanism | Why the deviation occurred |
| 3. Generalization Conditions | Mechanism and its boundary conditions | Where it may recur and how to prevent it |

**Example: An agent modifies the wrong repository.**

- **Level 1:** An execution action modified the wrong System State.
- **Level 2:** The agent used relative paths while the harness supplied an incorrect working directory. Their interaction caused the failure.
- **Level 3:** Similar failures may recur when repository identity is implicit and execution depends on an unverified working directory.

The proposed intervention is to validate repository identity before modification. This is an intervention target, not a replacement for the causal explanation.

## Cross-Cutting Principles

1. **Potential dependencies are not obligations.** Missing handoffs require case-specific evidence of causal relevance.
2. **Location is not causation.** A localized deviation does not automatically identify its originating mechanism.
3. **Causation is not necessarily singular.** Preserve multiple causes and interactions.
4. **Rootness is evidence-bounded.** Trace upstream only as far as evidence and investigation scope justify.
5. **Transferability must be qualified.** A single case can suggest generalization conditions without proving them.
6. **Causal inference is delegated.** `competing-explanations-causal-research` evaluates competing mechanisms; `diagnose-agentic-coding` reconstructs their artifact/action paths and reports their diagnostic and generalization implications.
