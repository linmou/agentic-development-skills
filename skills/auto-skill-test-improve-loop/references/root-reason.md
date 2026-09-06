# Causal diagnosis, ladder, and edition

## Surface vs root

| Surface | Root |
|---------|------|
| rewrote draft without learn interrupt | caller step not checkable; goal conflict favors draft |
| checked learnt/ without running $skill | false done via related files |
| skill not in session list | harness discovery, not skill body |

A new surface after patch is not success if the supported causal mechanism still prevents the gold observable.

## Open-world causal diagnosis

Invoke `$competing-explanations-causal-research` through its versioned Request/Response contract. Set `outcome` to the exact missing gold for one identified run, environment revision, and tested target-skill variant. Supply the case, trace, score, dependency manifest, environment record, repository state, and relevant prior runs as evidence seeds rather than accepted explanations.

Do not limit the research to predefined layers, actors, mechanisms, relationships, or intervention types. Generate plausible rival models before selecting a target; distinguish direct observations from inferences; seek support and refutation symmetrically; and preserve material uncertainty. Prior failure labels, human theories, and earlier diagnoses remain evidence seeds, not conclusions.

`ROOT.md` records:

- the frozen outcome, environment revision, and tested target-skill variant;
- evidence roles and timing;
- rival causal models with mechanism chains, predictions, possible refuters, and boundary conditions;
- the bounded ruling and material uncertainty;
- the most discriminating next evidence;
- the reasoning for the next action and any selected patch target.

The causal-research response does not choose or authorize file writes by itself. The loop interprets it against the write fence and minimum-addition rule. When evidence does not support a skill edit, gather the most useful missing evidence or take another justified in-scope action instead of manufacturing a patch target.

## Re-diagnosis after reruns

Every failed Step 8 rerun reopens the causal comparison. Freeze the new outcome and add the new trace, score, dependency observations, environment revision, tested target-skill variant, patch diff, and prior diagnosis as evidence seeds. Let the agent determine the next action from the updated evidence and bounded ruling; do not encode a fixed failure-to-action branching table and do not automatically climb the ladder.

When execution reveals a previously unknown dependency or environment condition, preserve its timing and evidence. Update the dependency/environment record and keep comparisons matched to a frozen revision. A later successful run may corroborate a repair without proving that the skill patch caused the improvement.

## Minimum addition ladder (SoT)

**Goal:** smallest text change that flips ecological gold — not the fullest theme rewrite.

| Rank | May edit | Use when |
|------|----------|----------|
| **M0** | One hard-gate row or 1–2 sentences | Single obligation, path, false-done line |
| **M1** | Short block in primary `SKILL.md` only | Need classify → act → done-when in one place |
| **M2** | Primary + one reference that step already points to | Updated diagnosis supports changing both the primary and its referenced SoT |
| **M3** | Multi-file / redesign | Updated diagnosis supports redesign and the human approves it |

```text
write ladder (one line each)
  → apply lowest untried rank in worktree
  → ecological re-run
  → fail → re-diagnose before choosing the next action
  → pass → stop (no consistency files)
```

If a fat patch already passed: keep a copy → reset baseline → M0 → M1 … → keep **smallest** pass.

**Anti-patterns:** multi-reference “consistency” on first try; calling M2 “minimum” because it feels complete; rewriting whole steps when one gate row would flip gold.

## Edition bounds

Every changed line must serve the evidence-supported causal intervention. Name files before edit. Prefer insert/replace local paragraphs. No drive-by reformat/rename/delete.

```text
diagnosed mechanism and bounded ruling:
why this target is supported:
will change:
will not change:
checkable criterion after patch: (yes/no gold that was false, now true)
```

Ask human before redesign (M3). Surgical scope applies **only under quarantine paths** (`worktree_skill_path` or `.eft/…/skills-copy/`). Never edit `original_skill_path` in the patch loop — see `references/ecological-cases.md` § Quarantine.

## When to stop

Stop with either a supported minimum patch whose ecological POS and NEG pass, or a supported no-patch ruling that records the unresolved outcome and next evidence/action. In both cases: remaining risk one line · RESULTS written · live originals unpatched until promote.
