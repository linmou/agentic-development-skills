# Rubric Entry Template (Dependencies-Based)

Single schema source for one rubric entry. How to fill it: `construction-principles.md`.

## Design Principle
A rubric entry is valid only when it is grounded in project context and intent assumptions.
Rules are written for anchors 5 / 3 / 1; levels 4 / 2 are implied and pinned by counter pairs (P5, P7).

## Required Fields
- `applicability`: where/when this rubric is valid.
- `decision_rule`: how to score or decide, with concrete score examples.
- `dependencies`: which context + intent assumptions this rubric depends on.
- `lifecycle`: retirement/sunset boundary metadata.

## Template
```md
### Rubric Entry
- id: RUB-<short-name>
- title: <clear rubric name>

- applicability:
  - include:
    - <where this rubric should be applied>
  - exclude:
    - <where this rubric should NOT be applied>

- decision_rule:
  - score_5_rule: <explicit high-quality condition>
  - score_5_support_examples:
    - <support example that matches score_5_rule>
  - score_5_counter_examples:
    - ["N/A for score 5 upper neighbor (+)", "<counter- should be scored as 4 (-)>"]
  - score_3_rule: <explicit partial condition>
  - score_3_support_examples:
    - <support example that matches score_3_rule>
  - score_3_counter_examples:
    - ["<counter+ should be scored as 4 (+)>", "<counter- should be scored as 2 (-)>"]
  - score_1_rule: <explicit poor/missing condition>
  - score_1_support_examples:
    - <support example that matches score_1_rule>
  - score_1_counter_examples:
    - ["<counter+ should be scored as 2 (+)>", "N/A for score 1 lower neighbor (-)"]
  - fail_fast: <optional hard fail condition>

- dependencies:
  - context_refs:
    - <natural-language context in context.md>
  - intent_refs:
    - <natural-language intent from intent list>

- lifecycle:
  - sunset_condition: <optional retirement condition>
```

## JSON Template (Preferred for Storage)
Use this JSON shape for the Response `entry` and for any caller that stores entries as files.

```json
{
    "id": "RUB-<short-name>",
    "title": "<clear rubric name>",
    "applicability": {
        "include": ["<where this rubric should be applied>"],
        "exclude": ["<where this rubric should NOT be applied>"]
    },
    "decision_rule": {
        "score_5_rule": "<explicit high-quality condition>",
        "score_5_support_examples": [
            "<support example that matches score_5_rule>"
        ],
        "score_5_counter_examples": [
            ["N/A for score 5 upper neighbor (+)", "<counter- should be scored as 4 (-)>"]
        ],
        "score_3_rule": "<explicit partial condition>",
        "score_3_support_examples": [
            "<support example that matches score_3_rule>"
        ],
        "score_3_counter_examples": [
            ["<counter+ should be scored as 4 (+)>", "<counter- should be scored as 2 (-)>"]
        ],
        "score_1_rule": "<explicit poor/missing condition>",
        "score_1_support_examples": [
            "<support example that matches score_1_rule>"
        ],
        "score_1_counter_examples": [
            ["<counter+ should be scored as 2 (+)>", "N/A for score 1 lower neighbor (-)"]
        ],
        "fail_fast": "<optional hard fail condition>"
    },
    "dependencies": {
        "context_refs": [
            "<natural-language context from context memory>"
        ],
        "intent_refs": [
            "<natural-language intent from intent list>"
        ]
    },
    "lifecycle": {
        "sunset_condition": "<optional retirement condition>"
    }
}
```

### JSON Rules
- Use valid JSON only (no comments, no trailing commas).
- Use 4-space indentation.
- `score_X_support_examples` must be a list.
- `score_X_counter_examples` must be a list of pairs: `[[counter+, counter-], ...]`.
- Each counter pair should contrast one main feature and stay adjacent-level (`X+1` / `X-1`).
- Shape is checked by `scripts/validate_rubric_entry.py`.

## Transformed Examples (from `references/rubric.md`)

Note: JSON template is source-of-truth for storage. Markdown examples are for readability only.

### Example 1 — Task Decomposition
```md
### Rubric Entry
- id: RUB-TASK-DECOMPOSITION
- title: Task decomposition completeness and role mapping

- applicability:
  - include:
    - Adapted blueprint includes multi-step task planning.
  - exclude:
    - Single-action requests with no decomposition need.

- decision_rule:
  - score_5_rule: Blueprint has 3-10 explicit subtasks, each mapped to AI/human/hybrid, with human-unique input slots.
  - score_5_support_examples:
    - "8 subtasks listed; each has role tag and a human-context input field."
  - score_5_counter_examples:
    - ["N/A for score 5 upper neighbor (+)", "8 subtasks listed and all role-mapped, but no human-context input slot is provided. (-)"]
  - score_3_rule: Subtasks exist but role mapping or human-unique slots are incomplete.
  - score_3_support_examples:
    - "5 subtasks in a list and 4 of them have role mapping."
  - score_3_counter_examples:
    - ["5 subtasks in a list and all 5 of them have role mapping. (+)", "5 subtasks in a list and 2 of them have role mapping. (-)"]
    - ["5 subtasks with 4 role mappings and clear human-context input slots. (+)", "5 subtasks with 4 role mappings but no human-context input slots. (-)"]
  - score_1_rule: Tasks are vague/lumped with no usable decomposition.
  - score_1_support_examples:
    - "One paragraph describing work; no subtask list."
  - score_1_counter_examples:
    - ["A short subtask list exists but role mapping is mostly missing. (+)", "N/A for score 1 lower neighbor (-)"]
  - fail_fast: No explicit subtask list.

- dependencies:
  - context_refs:
    - AI and human's accuracy for E2E task is limited and easy to be fatigue.
  - intent_refs:
    - Decompose tasks to build clear workflow.

- lifecycle:
  - sunset_condition: Replace when decomposition standard is migrated.
```

### Example 1 (JSON) — Task Decomposition
```json
{
    "id": "RUB-TASK-DECOMPOSITION",
    "title": "Task decomposition completeness and role mapping",
    "applicability": {
        "include": [
            "Adapted blueprint includes multi-step task planning."
        ],
        "exclude": [
            "Single-action requests with no decomposition need."
        ]
    },
    "decision_rule": {
        "score_5_rule": "Blueprint has 3-10 explicit subtasks, each mapped to AI/human/hybrid, with human-unique input slots.",
        "score_5_support_examples": [
            "8 subtasks listed; each has role tag and a human-context input field."
        ],
        "score_5_counter_examples": [
            [
                "N/A for score 5 upper neighbor (+)",
                "8 subtasks listed and all role-mapped, but no human-context input slot is provided. (-)"
            ]
        ],
        "score_3_rule": "Subtasks exist but role mapping or human-unique slots are incomplete.",
        "score_3_support_examples": [
            "5 subtasks in a list and 4 of them have role mapping."
        ],
        "score_3_counter_examples": [
            [
                "5 subtasks in a list and all 5 of them have role mapping. (+)",
                "5 subtasks in a list and 2 of them have role mapping. (-)"
            ],
            [
                "5 subtasks with 4 role mappings and clear human-context input slots. (+)",
                "5 subtasks with 4 role mappings but no human-context input slots. (-)"
            ]
        ],
        "score_1_rule": "Tasks are vague/lumped with no usable decomposition.",
        "score_1_support_examples": [
            "One paragraph describing work; no subtask list."
        ],
        "score_1_counter_examples": [
            [
                "A short subtask list exists but role mapping is mostly missing. (+)",
                "N/A for score 1 lower neighbor (-)"
            ]
        ],
        "fail_fast": "No explicit subtask list."
    },
    "dependencies": {
        "context_refs": [
            "AI and human's accuracy for E2E task is limited and easy to be fatigue."
        ],
        "intent_refs": [
            "Decompose tasks to build clear workflow."
        ]
    },
    "lifecycle": {
        "sunset_condition": "Replace when decomposition standard is migrated."
    }
}
```

### Example 2 — AI Improvement Loop Tightening
```md
### Rubric Entry
- id: RUB-AI-IMPROVEMENT-LOOP
- title: AI behavior tightening across iterations

- applicability:
  - include:
    - Tasks with iterative co-improvement cycles.
  - exclude:
    - One-shot outputs without iterative revision.

- decision_rule:
  - score_5_rule: Mid-loop context/rubric update mechanism is explicit and alignment improves across rounds.
  - score_5_support_examples:
    - "Round 2 and 3 show explicit rubric updates and fewer correction comments."
  - score_5_counter_examples:
    - ["N/A for score 5 upper neighbor (+)", "Rounds include explicit updates, but mismatch reduction is weak and inconsistent. (-)"]
  - score_3_rule: Feedback loop exists but behavior tightening is weak or inconsistent.
  - score_3_support_examples:
    - "Feedback is recorded, but next round still repeats prior mismatch patterns."
  - score_3_counter_examples:
    - ["Feedback is recorded and next round reduces most mismatch patterns. (+)", "Feedback is recorded, but next round shows almost no measurable change. (-)"]
  - score_1_rule: Static one-shot generation with no update loop.
  - score_1_support_examples:
    - "Single pass output and no iteration record."
  - score_1_counter_examples:
    - ["At least one explicit revision loop exists, but quality gain is minimal. (+)", "N/A for score 1 lower neighbor (-)"]
  - fail_fast: No mechanism to feed human feedback back into AI behavior.

- dependencies:
  - context_refs:
    - AI must improve with iteractive human feedback on AI performance.
  - intent_refs:
    - Reduce repeat errors and improve alignment.

- lifecycle:
  - sunset_condition: Retire if loop protocol is replaced by a new iteration framework.
```

### Example 3 — Effort Minimization
```md
### Rubric Entry
- id: RUB-EFFORT-MINIMIZATION
- title: Human effort reserved for high-value interventions

- applicability:
  - include:
    - Workflows with clear AI-executable bulk operations.
  - exclude:
    - The most safety-critical and high risk steps requiring mandatory human execution. 

- decision_rule:
  - score_5_rule: Human effort is focused on steering/judgment (<30%), while bulk execution is offloaded to AI.
  - score_5_support_examples:
    - "Human only sets constraints and final ranking; AI executes drafting, sampling, and summarization."
  - score_5_counter_examples:
    - ["N/A for score 5 upper neighbor (+)", "Human only sets constraints and ranking, but still performs one avoidable manual extraction step. (-)"]
  - score_3_rule: Partial offloading exists but human still does avoidable micro-management.
  - score_3_support_examples:
    - "AI drafts output, but human manually rewrites most sections line-by-line."
  - score_3_counter_examples:
    - ["AI drafts output and human edits only key decision sections. (+)", "AI drafts output, but human also performs most routine formatting and extraction. (-)"]
  - score_1_rule: Human performs most mechanical work without need.
  - score_1_support_examples:
    - "Human executes routine formatting and extraction steps that AI could perform."
  - score_1_counter_examples:
    - ["AI handles part of routine operations, but human still performs many mechanical steps. (+)", "N/A for score 1 lower neighbor (-)"]
  - fail_fast: Workflow requires avoidable human micro-steps by design.

- dependencies:
  - context_refs:
    - Human only have limited time for a work and dont want to do the same thing again and again.
  - intent_refs:
    - Minimize human effort while maintaining quality.

- lifecycle:
  - sunset_condition: Revisit if quality drops under aggressive automation.
```
