---
name: plan_format
summary: Shared reference for writing and reviewing plans — the three-phase Introduction / Body / Conclusion structure, the recommended subsections under each phase, and flexibility rules.
---

# Plan Format Reference

This document is the shared reference used by the `write-reviewable-plan` skill
and the plan-format review context
(`@${CLAUDE_PLUGIN_ROOT}/context/review-plan-format.md`). It defines the
structure plan documents should follow while drafting and the signals reviewers
look for in a diff.

A plan must follow a 3-phase structure — **Introduction → Body → Conclusion**. The three top-level phases are **mandatory** (a plan that opens with no Introduction at all, or ends with no Conclusion at all, is malformed). The subsections listed under each phase are the **recommended template**, not a required schema: a plan may omit any subsection that does not apply to the task at hand. Numbering is hierarchical: top-level numbers `1`, `2`, `3` label the (required) phases; `1.1`, `2.1`, etc. label the (recommended) subsections that belong to each phase. Each subsection is written *big-picture-first*: a `[High-level]` statement any reader can grasp, followed by `[Detail]` specifics.

The plan-format and document-writing perspectives are complementary. `review-document-writing` enforces the universal Intro-Body-Conclusion / Big-Picture-First principles on *any* document; `plan-format` (this reference) enforces the plan-specific phase requirement and the per-subsection quality bars defined below.

## Writing principles inherited from `review-document-writing`

- **Introduction** paints "why" and "what" in the simplest, most intuitive language — even readers without domain knowledge should follow it.
- **Body** presents the big picture (architecture, concept) first, then drills into components, code, and edge cases. The validation plan also lives in Body — it is part of "how we will know this works," not a separate wrap-up.
- **Conclusion** closes the discussion: it recaps the plan's essence (§3.1) and lists any items still requiring a decision (§3.2).

## Structure

### 1. Introduction

#### 1.1 Context
**Purpose.** Why is this task being initiated?
**High-level.** Background — the existing problem to be solved or the new requirement that prompted this plan.
**Detail.** Specific inconveniences or costs caused by the current situation, and the concrete outcomes expected once the requirement is met.
**Violation signals.** When present, only restates "what we will do" without explaining "why"; or written in jargon that assumes domain context the reader may not have.

#### 1.2 Goal
**Purpose.** What will ultimately change once this plan is completed?
**High-level.** One-sentence summary of the end state.
**Detail.** Specific metrics or quantitative targets that measure success.
**Violation signals.** Goal is indistinguishable from a task list ("do X, then Y"); no success criteria stated; success described only as "feature X exists" with no observable signal.

#### 1.3 Non-goals
**Purpose.** What are the clear boundaries of this task?
**High-level.** Scope edges in a sentence.
**Detail.** Specific features or specifications that are easily confused with the goal but are intentionally excluded.
**Violation signals.** When present, vacuous ("nothing else"); or excludes obvious-out-of-scope items while omitting the genuinely adjacent confusions readers would worry about.

### 2. Body

#### 2.1 Proposed Approach
**Purpose.** How will this be done?
**High-level — Architecture & Big Picture.** Summary or diagram giving an at-a-glance view of the overall flow or structural changes in the system.
**Mid-level — Core Logic & Components.** Roles and responsibilities of the core modules that constitute the big picture above.
**Deep-Detail — Technical Specs.** Specific API specifications, key algorithms, complex exception handling.
**Violation signals.** Section jumps straight to API/specs without any high-level summary (Critical — direct Big-Picture-First violation); components listed by name without their responsibilities; multiple alternative approaches mixed in here instead of being separated into §2.2.

#### 2.2 Alternatives Considered
**Purpose.** What other directions were weighed, and why was this one chosen?
**High-level.** Other major directions considered as alternatives.
**Detail.** Per-alternative technical comparison (performance, development cost, maintainability) and the explicit rationale for choosing the current approach.
**Violation signals.** Alternatives listed without comparison; the chosen approach is not explicitly justified against the listed alternatives.

#### 2.3 Risks / Trade-offs
**Purpose.** What are we accepting as a cost of this choice?
**High-level.** The biggest opportunity cost or weakness inherent in the chosen approach.
**Detail.** Specific potential vulnerabilities and the engineering mitigations for each.
**Violation signals.** Section claims "no risks" on a non-trivial plan; risks listed without mitigations; mitigations listed without identifying the risk they address.

#### 2.4 Test / Validation Plan
**Purpose.** How will success be verified?
**High-level.** Overall testing strategy.
**Detail.** Core unit-test scenarios and runnable end-to-end verification commands.
**Violation signals.** Contains only abstract phrases like "tests will pass" without runnable steps; coverage limited to "unit tests" with no end-to-end check. Validation content misplaced under Conclusion instead of Body (Critical — validation is part of *how* the work is executed and belongs in Body, regardless of whether it lives under a §2.4 header).

### 3. Conclusion

#### 3.1 Summary
**Purpose.** Wrap up the discussion by recapping the plan in one place.
**High-level.** One short paragraph that connects the dots: the problem from §1.1 → the chosen approach from §2.1 → the verification plan from §2.4. A reader who jumps to the end should understand the essence of the plan without scrolling back up.
**Detail.** The concrete effect of executing this plan and the single most important trade-off accepted (a pointer back to §2.3). Keep it terse — this section recaps, it does not introduce new material.
**Violation signals.** When present, summary introduces new arguments, files, or decisions not present in §§1–2 (Important — the summary should *recap*, not *extend*); or covers only part of the plan (e.g., only the approach) and omits the problem or the verification strategy.

#### 3.2 Open Questions
**Purpose.** What remains unresolved?
**High-level.** Major directional issues still under discussion.
**Detail.** Specific implementation or design questions for reviewers.
**Violation signals.** When present, questions listed without indicating who must decide; or questions that should have been resolved during the planning phase but were deferred without justification.

## Flexibility

The three top-level phases (Introduction, Body, Conclusion) are mandatory — a plan must contain content for each phase. The subsections above are a **recommended template** for each phase, not a required schema: a plan may omit any recommended subsection that does not apply to the task, and may freely add subsections beyond the template when they help the reader. Common additions:

- `Critical files` / `Edit targets` — explicit file paths to be modified.
- `Reused utilities` — existing functions or patterns the plan will lean on.
- `Design Decisions (user-confirmed)` — record of `AskUserQuestion` outcomes.
- `Step-by-step Implementation` — when a sequenced execution order is important enough to be part of the plan itself.
- `Migration Plan`, `Rollout Strategy`, `Dependencies`, `Glossary`, etc.

When added, place each new subsection under whichever phase fits its function (`1.x` for setup/scope material, `2.x` for design/execution material, `3.x` for closing material) and number it in sequence. Reviewers should treat added subsections favorably **as long as** they (a) preserve Introduction → Body → Conclusion ordering, and (b) obey big-picture-first within their own content.

When a recommended subsection's question *is* relevant to the plan but the answer is short, prefer a one-line acknowledgement under the subsection header ("§1.3 Non-goals — none beyond §1.2") over silent omission, so a reader can confirm the question was at least considered. Silent omission is fine only when the question genuinely does not apply.
