# Review Context: Plan Format

**Purpose.** Enforce the team's plan-document format in the diff — the mandatory Introduction / Body / Conclusion phase structure and the per-subsection quality bars defined in `docs/plan_format.md`. Assume the decision-making phase is over; this context checks *formal conformance only*, not whether the chosen approach is technically correct (that is the architect's job).

## References

- `@${CLAUDE_PLUGIN_ROOT}/docs/plan_format.md` — the three mandatory phases (Introduction, Body, Conclusion), the recommended subsection template (§1.1 Context, §1.2 Goal, §1.3 Non-goals, §2.1 Proposed Approach, §2.2 Alternatives Considered, §2.3 Risks / Trade-offs, §2.4 Test / Validation Plan, §3.1 Summary, §3.2 Open Questions), per-subsection violation signals (applied when a subsection is present), and flexibility rules for added subsections. Subsections are **not required** — only the three phases are. Consult the reference while evaluating every checkpoint below.

## Scope

Evaluate only the structure of plan documents that are added or modified in the diff. Do not surface findings about subsections outside the diff unless the new changes invalidate the overall phase structure (e.g., a whole phase was deleted).

This context is **complementary** to `review-document-writing`: writing enforces general Intro-Body-Conclusion / Big-Picture-First principles on any document, while plan-format enforces the plan-specific phase requirement and the per-subsection quality bars from the recommended template. Overlapping findings (e.g., "no introduction at all") may legitimately surface from both perspectives; the review synthesizer preserves complementary overlap and only combines true duplicates.

## Checkpoints

1. **Phase presence and ordering.** All three top-level phases — `1 Introduction`, `2 Body`, `3 Conclusion` — must be present and appear in that order. Missing a whole phase is a structural violation. (Subsections within each phase are the recommended template only — omission is allowed; do not flag a plan merely for omitting a recommended subsection.)
2. **Per-subsection quality (when present).** For any recommended subsection that **is** present in the diff, do its contents satisfy the violation signals in `docs/plan_format.md`? Examples: a Context that has no "why"; a Goal indistinguishable from a task list; a Summary that introduces new material; Risks without mitigations; Alternatives without comparison.
3. **High-level / Detail two-layer coverage.** Within each subsection that is present, does the author provide both a `[High-level]` (or equivalent macro) statement *and* `[Detail]` specifics? Either layer missing weakens a present subsection.
4. **Big-Picture-First in the Body phase.** The Body phase must lead with an architecture / big-picture summary before drilling into components and specs. A Body that opens directly with API specs / algorithms / data structures violates this and is a Critical violation per `docs/plan_format.md` — regardless of whether the high-level material lives under a `§2.1` header.
5. **Validation placement and concreteness.** Validation content must live in **Body**, not Conclusion. The plan should name runnable commands or concrete scenarios; abstract phrases ("we will test it", "unit tests pass") without executable steps fail this checkpoint. Validation content surfacing in Conclusion is a phase-boundary violation even when no `§2.4` header is used.
6. **Summary discipline (when present).** If a Summary subsection appears in Conclusion, it must recap the plan — connecting the problem (Context) → the chosen approach → the verification plan in a single paragraph, without introducing new arguments / files / decisions not present earlier, and without omitting any of the three threads it is supposed to weave together.
7. **Flexibility-rule compliance for added subsections.** Plans may add subsections beyond the recommended template (Critical files, Reused utilities, etc.). When they do, verify that the added subsections (a) sit under whichever phase fits their function, (b) preserve Intro → Body → Conclusion ordering, and (c) obey big-picture-first within their own content.

## Priority hints

- **Critical** — A whole phase is missing or out of order: no Introduction at all (the plan opens directly with the Approach or specs); no Body; no Conclusion; or phases appearing in a different order. The Body phase dives straight into API specs / algorithms without any high-level architecture summary (direct Big-Picture-First violation per the reference). Validation content is placed under Conclusion instead of Body — the phase boundary is broken.
- **Important** — A subsection that **is** present is degenerate per its violation signals: Goal indistinguishable from a task list; Risks listed without mitigations; Alternatives listed without comparison; Summary that introduces new material or omits one of the three threads (problem / approach / verification). Within any present subsection, the `[High-level]` or `[Detail]` layer is entirely missing. An added non-standard subsection breaks the Intro-Body-Conclusion ordering.
- **Suggestion** — A present subsection is reduced to a stub when one informative line would serve readers better. An added subsection obeys ordering but reads awkwardly out of place. A recommended subsection whose question clearly *applies* to the plan is silently omitted instead of getting a one-line acknowledgement (e.g., "Non-goals — none beyond §1.2").
