# Suitability Checklist

## Contents

- Independent work
- Bottleneck analysis
- Coordination cost
- Good fits
- Bad fits

## Independent work

Use parallel multi-agent acceleration when most work units are independent or only weakly coupled.

Check:
- Can one worker complete a task without editing another worker's local state?
- Can tasks be validated separately before final acceptance?
- Can failures be isolated to one task or one worker?
- Is there enough work to keep multiple workers busy?

## Bottleneck analysis

Identify the real bottleneck before adding agents.

Ask:
- Is the workflow bottlenecked by CPU, I/O, network, browser automation, review bandwidth, or one canonical writer?
- Can the bottleneck be leased and bounded?
- Will more workers reduce idle time, or just increase contention?

Use pipeline parallelism when different stages consume different resources and multiple task instances can be in flight at once.

## Coordination cost

Do not parallelize when coordination cost dominates execution cost.

Watch for:
- frequent merge conflicts
- large shared-state writes
- repeated human review chokepoints
- tiny tasks that cost more to schedule than to execute
- retries that become harder to reason about under concurrency

## Good fits

Parallelization usually helps when the workflow has:
- many similar files or cases
- isolated local execution
- bounded scarce resources
- separate validation artifacts
- a clear monitor or coordinator role

## Bad fits

Parallelization usually hurts when the workflow is:
- mostly serial
- dominated by one uncontrollable singleton resource
- highly stateful with frequent cross-task writes
- expensive to merge or reconcile
- ambiguous about ownership or acceptance criteria
