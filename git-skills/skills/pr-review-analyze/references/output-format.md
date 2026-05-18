# PR Review Analysis — Output Format

Use this template verbatim when producing the final analysis.

## Full report (reviews exist)

```markdown
# PR Review Analysis

**PR:** #<number> — <title>
**Reviewers:** <comma-separated reviewer login names>
**Reviews:** <n> reviews, <n> inline comments
**Validity:** <n> Agree, <n> Disagree, <n> Unclear
**Overall Verdict:** APPROVE | REQUEST CHANGES

---

## Consolidated Findings

### Critical
- [<reviewer>] `<file>:<line>` — <description> [Agree | Disagree | Unclear]
  ↳ Reason: <1–2 sentences citing specific file:line or symbol>
- [<reviewer>] (general comment) — <description> [Agree | Disagree | Unclear]
  ↳ Reason: …

### Important
- [<reviewer>] `<file>:<line>` — <description> [Agree | Disagree | Unclear]
  ↳ Reason: …

### Suggestions
- [<reviewer>] `<file>:<line>` — <description> *(nit)* [Agree | Disagree | Unclear]
  ↳ Reason: …

---

## Per-Reviewer Summary

### <reviewer-login> — APPROVE | REQUEST CHANGES | COMMENT
**Verdict:** <review state>
**Overview:** <1-2 sentence summary of this reviewer's overall stance>

#### Issues raised
- `<file>:<line>` — <description> [<Critical | Important | Suggestion> / <Agree | Disagree | Unclear>]
  ↳ Reason: …

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

- **Overall Verdict** = `REQUEST CHANGES` if any reviewer submitted `CHANGES_REQUESTED` OR any Critical finding exists; otherwise `APPROVE`. Do **not** flip the verdict based on validity assessment — the reviewer's official state stands.
- If every Critical finding is labeled `Disagree`, keep the verdict as `REQUEST CHANGES` but append this line at the end of the report:
  `> Note: All Critical findings were assessed as Disagree — recommend reviewing the assessment reasons before deciding.`
- Each finding bullet is followed by a `↳ Reason:` line citing a concrete `file:line` or symbol. The reason must be specific enough that the user can verify it directly.
- The `Validity:` meta line counts every raw comment (inline + general) exactly once.
- Trailing decorator order in Suggestion bullets: `<description> *(nit)* [<Validity>]` — the `*(nit)*` severity marker comes before the validity tag.
- Consolidated Findings show only `[<Validity>]` because severity is implied by the section heading (Critical/Important/Suggestions). Per-Reviewer entries are not grouped by severity, so they use the combined `[<Severity> / <Validity>]` form.
- Resolved/outdated comments are included but marked `[resolved]` after the description. They still get a validity label.
- If a comment has no file/line (top-level PR comment), use `(general comment)` for the location.
- Every reviewer who submitted at least one review or comment must appear in the Per-Reviewer Summary.
