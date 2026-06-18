---
name: write-reviewable-plan
description: Write or revise implementation, experiment, documentation, operation, or research plans so they are ready for custom-reviewer plan-review. Use when Codex is asked to create a plan, draft a spec, prepare a plan-reviewable document, or update a plan before review. This skill guides plan document structure and writing quality only; use plan-review when the user asks to review an existing plan.
---

# write-reviewable-plan

Draft or revise a plan so it is ready for `plan-review`.

## Scope

Use this skill for plan writing. It owns document structure, reader flow, and
validation concreteness. It does not run the reviewer pipeline, spawn reviewer
subagents, or apply architecture review expectations that are not genuinely
part of the plan.

For the detailed plan format, follow
`@${CLAUDE_PLUGIN_ROOT}/docs/plan_format.md`. That document is shared with the
`plan-format` review context, so plans written with this skill and plans
reviewed by `plan-review` use the same structural contract.

## Workflow

1. Establish the plan's purpose before writing implementation details:
   context, goal, intended audience, non-goals, and success criteria.
2. Write the plan with the required top-level phases in this order:
   `1. Introduction`, `2. Body`, `3. Conclusion`.
3. Use the recommended subsections from `docs/plan_format.md` when they fit
   the task. Omit irrelevant subsections, but include a short acknowledgement
   when a relevant planning question has a brief answer.
4. Keep each substantial section big-picture-first. Start with a simple
   `[High-level]` statement, then add `[Detail]` specifics such as files,
   commands, artifacts, owners, or edge cases.
5. Put validation in the Body. Name concrete commands, review gates, manual
   checks, acceptance criteria, or artifacts to inspect.
6. Keep the Conclusion as a recap and decision log. Do not introduce new
   requirements, files, arguments, or validation steps there.

## Writing Rules

- Start with why and what before how.
- Compare alternatives when there is a real choice, and state why the selected
  path is preferable.
- Pair risks with mitigations, fallbacks, or explicit acceptance decisions.
- Add task-specific subsections when useful, such as `Edit Targets`,
  `Data Sources`, `Manual Verification`, `Rollout`, `Dependencies`, or
  `Decision History`.
- Do not force software-architecture content into non-code plans. Architecture
  belongs in the plan only when it is part of the work being planned.

## Before Finishing

Check that the plan:

- Contains `1. Introduction`, `2. Body`, and `3. Conclusion` in order.
- Gives high-level context before technical details.
- Has enough context for a reviewer who did not see the preceding
  conversation.
- Includes concrete validation in the Body.
- Uses the Conclusion only for summary and open questions.
