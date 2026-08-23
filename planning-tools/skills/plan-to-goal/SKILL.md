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

## Grounding

- Read the complete plan and treat it as the sole source of truth.
- Do not inspect source code, project files, issues, Git history, or external
  sources to add content missing from the plan.
- Write in the plan's primary language. For a mixed-language plan, use the
  language of most explanatory prose.
- Preserve paths, API names, symbols, identifiers, and shell commands verbatim.
- Do not add customary behavior, tests, constraints, or completion criteria
  absent from the plan.

## Build the global requirement ledger

Before rendering any output section, read the entire plan and build one global
ledger:

1. Split every compound statement into independently verifiable meanings. One
   independently verifiable meaning is one atomic requirement.
2. Extract requirements from summaries, body sections, constraints, validation
   plans, completion statements, and conclusions. For each atomic requirement,
   record its action, target, conditions, exceptions, requirement strength,
   values, directions, counts, paths, identifiers, commands, and source context,
   including whether it was explicitly declared as a completion condition.
3. Compare requirements across the whole plan. Merge requirements that impose
   the same final obligation, including when one is positive and the other is
   negative, one is a concise summary and the other is detailed, or one states
   the desired design and the other rejects the inverse alternative.
4. Synthesize one canonical statement for each merged group. Preserve the
   strongest requirement and the union of all unique qualifiers; do not merely
   choose the shortest or longest source sentence.
5. Prefer preservation over deletion whenever semantic equivalence is
   uncertain.

Do not merge:

- implementation behavior with its verification;
- a verification command with a distinct acceptance criterion;
- a general rule with a specific exception; or
- statements with different values, directions, conditions, or error
  conditions.

For a genuine conflict, create one explicitly marked conflict item and preserve
both sides. Do not resolve, weaken, or discard either side.

## Assign section ownership

Assign every canonical atomic requirement to exactly one section according to
its primary intent:

- **Expected behavior:** observable runtime behavior, public data contracts,
  outputs, error behavior, and required user-facing functionality.
- **Constraints:** prohibitions, compatibility guarantees, scope boundaries,
  architectural restrictions, compatibility-preserving defaults, preserved
  invariants, and explicit exceptions.
- **Verification:** tests, inspections, commands, and their acceptance criteria.
  Keep a command distinct from a separate criterion. Verification may test a
  behavior owned elsewhere because implementation and evidence are distinct
  obligations.
- **Definition of done:** unique terminal acceptance states and handoff artifacts
  that must exist at completion, such as a required review record or deliverable.

Do not repeat an implementation obligation in both **Expected behavior** and
**Constraints**.

## Exclude planning metadata

Do not place edit-target file lists, implementation ordering, alternatives
considered, explanatory context, risk descriptions, or lists of test files in
**Expected behavior** merely because they occur in the plan. Treat edit-target
lists as navigation metadata and omit them when their intended changes are
already represented by canonical requirements.

Preserve normative content found in those sections: forbidden files or modules
and mandatory sequencing belong in **Constraints**; test cases and commands
belong in **Verification**; required documentation outcomes belong in
**Expected behavior** or **Definition of done** according to their intent.

Do not repeat earlier sections in **Definition of done** and do not use a
cross-reference such as “all preceding sections must be satisfied.” When an
explicit completion statement contains behavior, checks, and a unique terminal
state, atomize it and assign each part to its owner; retain the terminal state
in **Definition of done**.

Use the primary-language equivalent of `Not specified.` in **Definition of
done** only when the source plan truly contains no explicit terminal condition
or handoff requirement. Do not emit it merely because parts of an explicit
completion statement were assigned to other sections. If an explicit completion
statement has no separate artifact, express its distinct terminal acceptance
predicate: the required evidence has established the planned behavior. Keep the
detailed behavior in **Expected behavior** and exact tests or commands in
**Verification**.

## Render the goal prompt

Return only the goal prompt. Use exactly the five unescaped Markdown headings
below, in order. Use bullet lists for prose requirements. Render paths, API
names, symbols, and identifiers as inline code where appropriate.

Render each shell command once as an executable fenced code block. Preserve
their text and line structure verbatim; do not turn commands into one-line
inline-code items. Never backslash-escape Markdown structure. When instructions
or examples demonstrate fenced Markdown, use a longer outer fence or indentation
so fences are not nested invalidly.

Translate template prose into the plan's primary language. The **Task** remains
an instruction to implement the functionality in the plan and contains the
normalized absolute path.

````markdown
## Task

- Implement the functionality in `<absolute-plan-path>`.

## Expected behavior

- <Canonical observable outcome.>

## Constraints

- <Canonical prohibition, compatibility rule, boundary, or invariant.>

## Verification

- Run:

```bash
<verbatim shell command>
```

- <Distinct manual inspection or acceptance criterion.>

## Definition of done

- <Unique terminal state or handoff artifact.>
````

If **Expected behavior**, **Constraints**, or **Verification** has no owned
requirement, emit one bullet containing the primary-language equivalent of
`Not specified.`. Never emit an empty **Definition of done** body. Use its
primary-language `Not specified.` bullet only when the plan has no explicit
completion condition or handoff artifact. Do not omit a section. Render a
conflict as one bullet beginning with the primary-language equivalent of
`Conflict:` and include both sides.

## Validate before returning

Audit the rendered prompt against the ledger:

- Every atomic source requirement maps to one canonical item.
- Every canonical item appears in exactly one section and exactly once.
- Every unique condition, strength, number, exception, identifier, and other
  qualifier from merged sources survives in its canonical item.
- Section ownership follows the primary-intent rules.
- Each command matches the source text and line structure and remains
  executable.
- **Definition of done** is non-empty and contains no repetition or
  cross-reference.

For maintenance evaluation cases covering deduplication, ownership, completion,
conflicts, commands, identifiers, and mixed-language input, see
[`references/evaluation-cases.json`](references/evaluation-cases.json).
