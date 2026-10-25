# Control-Loop Lens

**Intent:** A domain-general checklist derived from the L1 functions of `diagnose-agentic-coding`. Use it to audit coverage, or as `O_v0` in light mode.

| ID | Function | Typical output | Coverage question |
| --- | --- | --- | --- |
| C1 | Objective alignment and governance | Objective contract: goal and constraints | Does some type capture what should be achieved and under which constraints, and how it reached the agent? |
| C2 | Problem and state understanding | Belief about problem and world | Does some type capture the agent's representation, distinct from World? |
| C3 | Solution formation | Plan or intended change | Does some type capture the intended action before it is taken? |
| C4 | Execution and coordination | Record plus world-state change | Are actions, their records, and resulting World versions separable? |
| C5 | Monitoring, adaptation, recovery | Adaptation directive | Does some type capture how feedback changes later actions? |
| C6 | Verification and completion | Verification record and completion status | Does some type capture completion evidence separate from the completion claim? |

Typical dependencies: C1 constrains all others; C2 informs C3, C4, C6; C3 specifies C4; C4 feeds C2, C5, C6; C5 routes to C2, C3, C4; C6 feeds C5 and completion. Some consumption is method-dependent. These are potential dependencies, not obligations.

## Light mode

When used as `O_v0`, instantiate each function with domain-specific artifact names and state locators for the case, and record the instantiation. Residuals that do not fit are the signal to escalate to full induction.
