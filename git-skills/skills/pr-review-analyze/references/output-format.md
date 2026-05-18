# PR Review Analysis — Output Format

Use this template verbatim when producing the final analysis.

## Full report (reviews exist)

```markdown
# PR Review Analysis

**PR:** #<number> — <title>
**Reviewers:** <comma-separated reviewer login names>
**Reviews:** <n> reviews, <n> inline comments
**Overall Verdict:** APPROVE | REQUEST CHANGES

---

## Consolidated Findings

### Critical
- [<reviewer>] `<file>:<line>` — <description>
- [<reviewer>] (general comment) — <description>

### Important
- [<reviewer>] `<file>:<line>` — <description>

### Suggestions
- [<reviewer>] `<file>:<line>` — <description> *(nit)*

---

## Per-Reviewer Summary

### <reviewer-login> — APPROVE | REQUEST CHANGES | COMMENT
**Verdict:** <review state>
**Overview:** <1-2 sentence summary of this reviewer's overall stance>

#### Issues raised
- `<file>:<line>` — <description> [Critical | Important | Suggestion]

#### Praise / positive observations
- <observation>
```

## Empty report (spool-aborted fallback only)

Only emit this if the user aborted `scripts/wait-for-reviews.sh`. The spool script in SKILL.md is mandatory in all other zero-review cases.

```markdown
# PR Review Analysis

**PR:** #<number> — <title>
**Reviews:** 0 reviews, 0 comments

No reviews have been submitted on this PR yet (spool was aborted).
```

## Notes

- **Overall Verdict** = `REQUEST CHANGES` if any reviewer submitted `CHANGES_REQUESTED` OR any Critical finding exists; otherwise `APPROVE`.
- Resolved/outdated comments are included but marked `[resolved]` after the description.
- If a comment has no file/line (top-level PR comment), use `(general comment)` for the location.
- Every reviewer who submitted at least one review or comment must appear in the Per-Reviewer Summary.
