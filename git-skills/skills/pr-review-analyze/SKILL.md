---
name: pr-review-analyze
description: Fetch and analyze all reviews on a GitHub pull request. Evaluates each comment's validity against the actual code at HEAD (Agree / Disagree / Unclear with reasoning) and consolidates feedback into Critical / Important / Suggestion categories with a per-reviewer summary. Use when the user says "analyze PR reviews", "summarize review feedback", "what did reviewers say", "show me the review comments", or "/pr-review-analyze".
---

# pr-review-analyze

## Pre-flight: identify the PR

Resolve the PR number in this priority order:

1. User-supplied PR number (e.g. `#123` or `123` in the invocation).
2. Current branch: discover via GitHub MCP `*get_pull_request*` or `gh pr view --json number,title -q '[.number,.title]'`.
3. If neither works, ask the user for the PR number.

Also collect the PR title and base branch name.

## Tool discovery

At runtime, scan the available tool list for tools matching the patterns below. Use the first match found for each operation.

| Operation | MCP pattern | gh CLI fallback |
|---|---|---|
| Get PR details | `*get_pull_request*` | `gh pr view <PR> --json number,title,state,baseRefName,headRefName` |
| List reviews | `*list_pull_request_reviews*` or `*get_pull_request_reviews*` | `gh api repos/{owner}/{repo}/pulls/<PR>/reviews` |
| List inline review comments | `*list_pull_request_review_comments*` or `*get_review_comments*` | `gh api repos/{owner}/{repo}/pulls/<PR>/comments` |

Fetch reviews and inline comments in parallel once the PR number is resolved.

To resolve `{owner}` and `{repo}` for gh CLI fallbacks: `git remote get-url origin` and parse the GitHub URL.

## Spooling — wait for reviews (MANDATORY when reviews are empty)

If reviews length > 0, skip this section.

If reviews length == 0, you **MUST** run the bundled spool script using the Bash tool before producing any output. Do not substitute the empty-report template — that template is reserved only for when the user aborts the script (e.g. Ctrl-C).

```bash
bash scripts/wait-for-reviews.sh <owner> <repo> <PR>
```

The script blocks, polling every 60s, and exits with status 0 once at least one review exists. After it exits, re-fetch reviews and inline comments in parallel, then proceed with the full-report analysis.

## Severity categorization

Classify each review and comment using these rules, in priority order:

| Signal | Severity |
|---|---|
| Review state is `CHANGES_REQUESTED` | The review verdict is Critical; its individual comments default to Important unless clearly a nit |
| Comment body contains keywords: `bug`, `broken`, `incorrect`, `crash`, `security`, `vulnerability`, `data loss`, `exploit` | Critical |
| Nit indicator prefix in comment body: `nit:`, `nit -`, `minor:`, `optional:`, `s/` | Suggestion |
| Trivial style remark (whitespace, typo in a comment, trivial rename suggestion) | Suggestion |
| All other comments | Important |

Resolved/outdated comments are still included but marked `[resolved]` in the output.

## Validity assessment

After categorizing severity, evaluate each **raw comment** against the actual code at HEAD and assign one of three validity labels with a 1–2 sentence reason. A raw comment is a single inline or general comment as posted by a reviewer — evaluate them individually, not the consolidated rollup.

### Labels

| Label | Meaning |
|---|---|
| `Agree` | After reading the code, the reviewer's claim is factually correct and the suggestion is a reasonable improvement. |
| `Disagree` | The reviewer is mistaken about the facts (case is already handled elsewhere, behavior is intentional, claim contradicts the code), or the tradeoff they propose is clearly worse. |
| `Unclear` | The code alone is insufficient to judge — depends on design intent, external system behavior, or business requirements. State in the reason what additional information is needed. |

### Gathering context for each comment

- **Inline comment:** Read the **entire file** at `file:line` (not just nearby lines). The reviewer's premise may depend on code far from the cited line.
- **Symbol mentioned in body:** If the comment names a function, type, or flag, Grep for callers/references and read the most relevant ones to confirm the claim.
- **PR diff cross-check:** Determine whether the cited line is part of this PR's diff or pre-existing code. A comment about pre-existing code is often `Unclear` (out of scope) unless the PR touches the surrounding behavior.
- **General (top-level) comment:** Read the PR diff overview and any files the comment explicitly or implicitly references.

### Efficiency

- Deduplicate reads: if multiple comments reference the same file, read it once.
- For >5 comments, batch Read/Grep calls in parallel.
- Stop expanding context once the label is defensible — don't chase callers indefinitely.

### Constraints

- **Ground every judgment in the code at HEAD.** Cite a specific `file:line` or symbol in the reason. Never guess.
- Prefer `Unclear` over a confident guess when intent is genuinely ambiguous.
- Do not modify source files, write PR replies, or push commits during analysis. This skill only evaluates.

## Output format

Before producing output, read `references/output-format.md` and follow the full-report template verbatim (including verdict rules).

## Rules

- Fetch reviews and inline comments in parallel once the PR number is known.
- Never fabricate or infer reviewer intent beyond what the review text states.
- Include resolved comments but mark them `[resolved]`.
- Every reviewer who submitted at least one review or comment must appear in the Per-Reviewer Summary.
- Validity assessment must be grounded in the actual code at HEAD. If a comment references code outside the diff, read that code before judging.
- Use `Unclear` instead of guessing when design intent, business rules, or external behavior is required to judge.
- Do not modify any source files or the PR during analysis.
