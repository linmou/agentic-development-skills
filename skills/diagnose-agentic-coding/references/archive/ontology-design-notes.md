<!-- Archived design notes. The normative artifact graph is ../artifact-flow.md. -->

To better diagnose the root cause and provide suggestions for future refine, i want do decompose function nodes in L1 ontology taxonomies into (actor, input, output) triplets. 
So the original L1 ontology graph can be tranfered into an artifact produce-consumption graph.  
Here artifacts may have different forms in various pipelines, maybe docs, codes, or agent thoughts, the key is their definition. When diagnosing by this (actor, artifact, action) ontology, You need to first diagnose the functional actions with the supported artifacts. 
The The AL2 ontology right now is not the main focus or attention area. It works as the explanation or demonstration for the L1 ontology. Right now, you should focus more on the L1 ontology since it has been transformed to the new Actor, Artifact, and Action ontology.

System State (SYS) is a first-class external state entity alongside the six semantic artifacts. It represents the actual target system at a grounded version or time. Keep SYS separate from State Model (SM), the agent's representation, and Execution Record (ER), the action log. Execution consumes SYS_t and may produce SYS_{t+1} alongside ER; verification uses evidence from SYS_{t+1}. Inspection results are evidence about SYS, not necessarily the complete SYS. Change Sets are optional derived evidence, not a mandatory artifact type.

| L1 Function                              | Actor         | Inputs                                                                               | Output artifact / state effect | Artifact meaning                                                          | Consumed by           |
| ---------------------------------------- | ------------- | ------------------------------------------------------------------------------------ | -------------------------- | ------------------------------------------------------------------------- | --------------------- |
| **1. Objective Alignment & Governance**  | Human + Agent | Human intent, task context                                                           | **Objective Contract**     | What should be achieved and under what constraints                        | 2, 3, 4, 5, 6         |
| **2. Problem & State Understanding**     | Agent         | Objective Contract, SYS observations/evidence, Execution Record, Adaptation Directive | **State Model**            | Agent's current representation of the problem/system                      | 3, 4, 6               |
| **3. Solution Formation**                | Agent         | Objective Contract, State Model, Verification Record_{d}, Adaptation Directive           |**Solution Specification** | What change/action the agent intends to perform                           | 4                     |
| **4. Action Execution & Coordination**   | Agent         | Objective Contract, State Model, Solution Specification, Verification Record_{d}, SYS_t | **Execution Record + SYS_{t+1}** | What actions occurred and the resulting target state | 2, 5, 6 |
| **5. Monitoring, Adaptation & Recovery** | Agent         | Objective Contract, Execution Record, Verification Record                            | **Adaptation Directive**   | What should be reconsidered, retried, revised, or recovered               | 2, 3, 4, 6            |
| **6. Verification & Completion**         | Agent         | Objective Contract, State Model, Execution Record, Adaptation Directive_{d}, SYS_{t+1} evidence | **Verification Record** | How success is assessed against the resulting state, evidence obtained, and completion status | 3_{d}, 4_{d}, 5, Completion |



| Artifact                   | Question it answers                               |
| -------------------------- | ------------------------------------------------- |
| **Objective Contract**     | What should happen?                               |
| **State Model**            | What is currently true / what is the problem?     |
| **Solution Specification** | What do we intend to do?                          |
| **Execution Record**       | What actually happened?                           |
| **Adaptation Directive**   | What should change next?                          |
| **Verification Record**    | Did it satisfy the objective, and how do we know? |


Examples: 
| Abstract artifact          | Simple agentic-coding example                                                                              |
| -------------------------- | ---------------------------------------------------------------------------------------------------------- |
| **Objective Contract**     | “Add password-reset functionality; preserve existing login behavior; all relevant tests must pass.”        |
| **State Model**            | “Reset endpoint does not exist; authentication is handled by `AuthService`; email service already exists.” |
| **Solution Specification** | “Add reset-token generation and endpoint using the existing email service.”                                |
| **Execution Record**       | “Modified `auth.py` and `routes.py`; application runs; one test currently fails.”                          |
| **Adaptation Directive**   | “Failure suggests token expiration handling is incorrect; reconsider implementation.”                      |
| **Verification Record**    | “Password-reset tests: 5/6 pass; expiration test fails; task not complete.”                                |

SYS example: `SYS_t = auth.py at commit abc123`; execution records a patch application; `SYS_{t+1} = auth.py at commit def456` is inspected independently. A tool-reported success in ER does not establish that `def456` contains the intended change.
