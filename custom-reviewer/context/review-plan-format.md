# Review Context: Plan Format

**Purpose.** Enforce the team's plan-document format in the diff — the required Introduction / Body / Conclusion structure and the required subsections (§1.1 through §3.2) defined in `docs/plan_format.md`. Assume the decision-making phase is over; this context checks *formal conformance only*, not whether the chosen approach is technically correct (that is the architect's job).

## References

- `@${CLAUDE_PLUGIN_ROOT}/docs/plan_format.md` — the three phases (Introduction, Body, Conclusion), the nine required subsections (§1.1 Context, §1.2 Goal, §1.3 Non-goals, §2.1 Proposed Approach, §2.2 Alternatives Considered, §2.3 Risks / Trade-offs, §2.4 Test / Validation Plan, §3.1 Summary, §3.2 Open Questions), per-subsection violation signals, and flexibility rules for added subsections. Consult it while evaluating every checkpoint below.

## Scope

Evaluate only the structure of plan documents that are added or modified in the diff. Do not surface findings about subsections outside the diff unless the new changes invalidate the overall skeleton (e.g., a required subsection was deleted).

This context is **complementary** to `review-document-writing`: writing enforces general Intro-Body-Conclusion / Big-Picture-First principles on any document, while plan-format enforces the plan-specific subsection skeleton on top. Overlapping findings (e.g., "no introduction at all") may legitimately surface from both perspectives — plan-review does not deduplicate.

## Checkpoints

1. **Phase ordering.** Does the document follow Introduction → Body → Conclusion in that order? Out-of-order phases are a structural violation even if every subsection exists.
2. **Required-subsection presence.** Are all nine required subsections from `docs/plan_format.md` present under the correct phase? Per-subsection violation signals are listed in the reference — apply them when a subsection is present but degenerate (e.g., a Context that has no "why", or a Summary that introduces new material).
3. **High-level / Detail two-layer coverage.** Within each subsection, does the author provide both a `[High-level]` (or equivalent macro) statement *and* `[Detail]` specifics? Either layer missing weakens the subsection.
4. **Big-Picture-First in §2.1 Proposed Approach.** The Body phase's first subsection must lead with an architecture / big-picture summary before drilling into components and specs. Direct dive into API specs / algorithms / data structures violates this and is a Critical violation per `docs/plan_format.md`.
5. **§2.4 Test / Validation placement and concreteness.** Test / Validation must live in **Body** (as §2.4), not Conclusion. The plan should name runnable commands or concrete scenarios; abstract phrases ("we will test it", "unit tests pass") without executable steps fail this checkpoint.
6. **§3.1 Summary discipline.** Conclusion's Summary recaps the plan — it must connect §1.1 → §2.1 → §2.4 in a paragraph, must not introduce new arguments / files / decisions not present in §§1–2, and must not omit any of the three threads it is supposed to weave together.
7. **Flexibility-rule compliance for added subsections.** Plans may add subsections beyond the nine (Critical files, Reused utilities, etc.). When they do, verify that the added subsections (a) sit under whichever phase fits their function, (b) do not displace any required subsection, (c) preserve Intro → Body → Conclusion ordering, and (d) obey big-picture-first within their own content.
8. **No-drop discipline.** A required subsection must not be omitted just because it seems trivially short — a one-line acknowledgement under the subsection header is acceptable, an outright missing header is not.

## Priority hints

- **Critical** — Missing §1.1 Context, §2.1 Proposed Approach, §2.4 Test / Validation Plan, or §3.1 Summary (the plan ends abruptly with no recap, leaving readers to reconstruct the essence themselves). §2.1 dives straight into API specs / algorithms without any high-level architecture summary (direct Big-Picture-First violation flagged in the reference). The plan's introduction phase as a whole is absent (file opens directly with the Approach / specs). Test / Validation is placed under Conclusion instead of Body — the phase boundary is broken.
- **Important** — Missing §1.2 Goal, §2.2 Alternatives Considered, or §2.3 Risks / Trade-offs on a non-trivial plan. Within any present subsection, the `[High-level]` or `[Detail]` layer is entirely missing. Risks listed without mitigations, or alternatives listed without comparison. The §3.1 Summary introduces new material not in §§1–2, or omits one of the three threads (problem / approach / verification). An added non-standard subsection breaks the Intro-Body-Conclusion ordering.
- **Suggestion** — Missing §1.3 Non-goals or §3.2 Open Questions (acceptable on small plans but a recurring weakness if always omitted). Added subsections obey ordering but read awkwardly out of place. A required subsection is technically present but reduced to a stub when one informative line would serve readers better.
