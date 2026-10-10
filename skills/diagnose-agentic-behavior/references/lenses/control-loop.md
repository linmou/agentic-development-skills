# Control-Loop Lens

**Intent:** A domain-general checklist derived from the L1 functions of `diagnose-agentic-coding`, cross-referenced to published taxonomies. Use it to audit coverage, or as `O_v0` in light mode.

| ID | Function | Typical output | AgentErrorTaxonomy module | TRAIL category | Coverage question |
| --- | --- | --- | --- | --- | --- |
| C1 | Objective alignment and governance | Objective and constraints | — | Planning and coordination | Does some type capture what should be achieved and under which constraints, and how it reached the agent's context? |
| C2 | Problem and state understanding | Belief state about the problem and environment | Memory | Reasoning | Does some type capture the agent's belief state, distinct from environment state? |
| C3 | Solution formation | Plan or intended change | Planning | Planning and coordination | Does some type capture the intended action before it is taken? |
| C4 | Execution and coordination | Actions with observations, plus environment-state change | Action; System (tools, infrastructure) | System execution | Are actions, their observations, and resulting environment-state versions separable? |
| C5 | Monitoring, adaptation, recovery | Adaptation directive | Reflection | Reasoning | Does some type capture how feedback changes later actions? |
| C6 | Verification and completion | Verification record and completion claim | Reflection | Reasoning | Does some type capture completion evidence separate from the completion claim? |

The taxonomy columns are approximate correspondences for orientation, not equivalences; the module and category names are the published ones (sources in [README.md](README.md)).

Typical dependencies: C1 constrains all others; C2 informs C3, C4, C6; C3 specifies C4; C4 feeds C2, C5, C6; C5 routes to C2, C3, C4; C6 feeds C5 and completion. Some consumption is method-dependent. These are potential dependencies, not obligations.

## Light mode

When used as `O_v0`, instantiate each function with domain-specific artifact names and environment-state locators for the case, and record the instantiation. Residuals that do not fit are the signal to restart with a full derivation.
