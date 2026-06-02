# Review Synthesis

This document is the shared reference for synthesizing specialist reviewer
outputs into one review result. It is used by
`@${CLAUDE_PLUGIN_ROOT}/agents/review-synthesizer.md`.

## Goals

- Preserve the recall benefits of independent specialist reviews.
- Produce one coherent final verdict.
- Make same-iteration specialist contradictions visible before automated fixes.
- Keep every final finding grounded in at least one specialist finding.

## Decision Labels

Use these labels when classifying specialist findings:

| Label | Meaning |
|---|---|
| `ACCEPT` | Include the finding in the final summary as-is or with light wording cleanup. |
| `COMBINE` | Merge the finding with another finding about the same underlying issue. |
| `DISMISS` | Exclude the finding because it is duplicate-only, unsupported, out of scope, or fully superseded by a stronger accepted finding. |
| `CONFLICT` | Preserve as an unresolved contradiction because specialists recommend incompatible fixes for the same issue or location. |
| `NEEDS_DECISION` | Preserve as a user decision because the finding requires a design/product direction choice that cannot be resolved from the diff and contexts alone. |

## Ownership

When findings overlap, choose the owner by concern:

| Concern | Owner |
|---|---|
| SOLID, DRY, KISS, YAGNI, module boundaries, dependency direction | `architect` |
| Code-comment accuracy, staleness, misleading or missing comment context | `comment` |
| Local clarity, naming, nesting, dead code, redundant patterns, idiom fit | `simplification` |
| Untested public behavior, missing regression tests, test quality | `test-coverage` |
| General document flow, Intro-Body-Conclusion, big-picture-first writing | `document-writing` |
| Required plan skeleton, subsection presence, plan-format conformance | `plan-format` |

If ownership is ambiguous, prefer the specialist whose context most directly
mentions the concern. If still ambiguous in code mode, use
`architect > comment > simplification > test-coverage`.

## Combining Findings

Findings are combinable when they describe the same underlying issue at the
same or adjacent diff location, or when one finding is a narrower statement of
the other. Keep the owner finding as the final wording, attach the other
specialists with `(also flagged by <specialist>[, ...])`, and use the highest
priority among the combined findings.

Do not combine findings that only share a line number but describe different
risks.

## Conflicts

Mark a finding as `CONFLICT` when specialists give incompatible guidance for
the same issue, such that applying one recommendation would substantially undo
or prevent the other. Examples:

- `architect` recommends extracting a helper for ownership or duplication, but
  `simplification` recommends inlining the same helper for local clarity.
- `comment` recommends documenting a behavior, but `simplification` recommends
  deleting the same comment because the behavior should be obvious.

Different severities are not conflicts by themselves. Prefer the highest
priority unless the recommended fixes are incompatible.

In `review-loop`, also mark a finding as `CONFLICT` when it contradicts a
previously applied fix listed in the synthesizer input.

## User Decisions

Mark a finding as `NEEDS_DECISION` when resolving it requires choosing a
fundamental design direction, API contract, product behavior, or plan scope
that is not determined by the diff, context files, or previous user decisions.

Do not mark routine localized fixes as `NEEDS_DECISION`.

## Plan Mode

Plan-review specialists intentionally overlap. In plan mode, preserve
complementary overlap when different specialists evaluate different aspects of
the same text. Only use `COMBINE` for true duplicate findings with the same
reasoning, or `CONFLICT` for incompatible recommendations.

## Verdict

Return `REQUEST CHANGES` if any final Critical finding remains, any specialist
requested changes for a finding that was not dismissed, or any `CONFLICT` /
`NEEDS_DECISION` finding remains. Otherwise return `APPROVE`.
