---
name: plan-to-goal
description: Generate structured goal prompt text from a required plan document path. Use when the user asks to convert a Markdown implementation plan into a goal prompt; do not use to create, start, or update a goal.
---

# Plan to Goal

Create goal prompt text grounded only in a specified plan document. Do not
create or invoke a goal.

## Input gate

Require exactly one plan document path. Resolve it against the current working
directory and normalize it to an absolute path before reading the document.

Stop and report the specific problem when the argument is missing or the path
does not identify an existing, readable regular file. Do not emit a partial
prompt after an input error.

## Grounding rules

- Read the entire plan. Treat it as the sole source of truth for requirements.
- Do not inspect source code, project files, issues, Git history, or external
  sources to add content missing from the plan.
- Write in the plan's primary language. For a mixed-language plan, use the
  language of most explanatory prose.
- Preserve file paths, commands, API names, symbols, and other identifiers
  verbatim.
- Deduplicate repeated requirements without combining distinct requirements.
- When requirements conflict, state the conflict and preserve both sides. Do
  not resolve it by guessing.
- Do not add customary tests, constraints, or completion criteria that the plan
  does not state.

## Output contract

Return only the goal prompt. Use exactly the five headings below, in this
order. Put each extracted item on its own inline-code line. Do not add a
preamble, explanation, source summary, or trailing note.

**Task**
`Implement the functionality in <absolute-plan-path>.`

**Expected behavior**
`<Externally observable behavior stated by the plan.>`

**Constraints**
`<Constraint explicitly stated by the plan.>`

**Verification**
`<Test, check, command, or manual verification explicitly stated by the plan.>`

**Definition of done**
`<Completion condition supported by the plan.>`

Translate the prose in this template into the plan's primary language. The
`Task` must remain an instruction to implement the functionality in the plan
and must contain the normalized absolute plan path.

For every section other than `Task`, extract only the following content:

- **Expected behavior:** user-visible or system-observable outcomes.
- **Constraints:** compatibility requirements, prohibited changes, technical
  limits, and other explicit restrictions.
- **Verification:** named tests, commands, static checks, and manual checks.
- **Definition of done:** explicit completion criteria and required verification
  whose completion the plan identifies as necessary.

If the plan supports no item for a section, emit one inline-code line with the
primary-language equivalent of `Not specified.` Do not omit the section. If a
section contains a conflict, use an inline-code item that identifies both
conflicting statements.
