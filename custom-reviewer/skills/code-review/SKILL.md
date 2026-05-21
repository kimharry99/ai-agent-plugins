---
name: code-review
description: "Review code changes by orchestrating specialist reviewer subagents. Supports two scopes — `working` (uncommitted changes in the working tree) and `branch` (PR-style, base branch → current HEAD, optionally including uncommitted work). Use when the user asks to review the working tree, review the current diff, run a code review, review before committing, or review a branch/PR against a base. Builds a diff file for the chosen scope, fans out to the `reviewer` subagent once per active specialist review context, then returns a consolidated summary."
---

# code-review

Orchestrates a multi-perspective review of a code diff. You (Claude) build a diff for the requested scope, spawn one reviewer subagent per active specialist context in parallel, and return a consolidated summary. For review of plan/spec documents, use the `plan-review` skill instead.

## Scope modes

| Mode | What it diffs |
|---|---|
| `working` | Uncommitted changes (staged + unstaged against HEAD). |
| `branch` | `merge-base(<base>, HEAD)..HEAD` — PR-style. Working-tree changes, if any, are appended. |

**Auto-selection** (when the user doesn't specify a mode): the helper script decides. If HEAD == resolved base and the tree is dirty → `working`; if HEAD differs from base → `branch`; else stop with "nothing to review".

**Base branch resolution** for `branch` mode, in order: user `--base` → upstream (`@{u}`) → `origin/HEAD` → `origin/main` / `origin/master` / `main` / `master`. If none, ask the user.

## Available specialists

| Specialist | Review context |
|---|---|
| architect      | `@${CLAUDE_PLUGIN_ROOT}/context/review-architect.md`      |
| comment        | `@${CLAUDE_PLUGIN_ROOT}/context/review-comment.md`        |
| simplification | `@${CLAUDE_PLUGIN_ROOT}/context/review-simplification.md` |
| test-coverage  | `@${CLAUDE_PLUGIN_ROOT}/context/review-test-coverage.md`  |

A context file that is empty or missing means the specialist is not yet ready — skip it. Add a new row here when a new `review-*.md` context is authored; no other edits are needed.

The reviewer subagent (`@${CLAUDE_PLUGIN_ROOT}/agents/reviewer.md`) reads any `@`-referenced documents inside a context file itself, so this skill only needs to point it at the context.

## Workflow

1. **Build the diff.** From the target repo root, run:
   ```
   ${CLAUDE_PLUGIN_ROOT}/skills/code-review/scripts/build_diff.sh --mode <working|branch|auto> [--base <ref>] [-- <pathspec>...]
   ```
   The script writes the diff to `<target-repo>/.claude/tmp/code-review-<timestamp>.diff` and prints `DIFF_PATH=`, `MODE=`, and (for branch mode) `BASE=` on stdout. Exit code `2` means "nothing to review" — stop and report that back.

2. **Enumerate active specialists.** For every row in the Available Specialists table, resolve the `@${CLAUDE_PLUGIN_ROOT}/...` reference and confirm the context file exists and is non-empty. Build the list of active specialists.

3. **Fan out in parallel.** In a single assistant message, emit one `Agent` tool call per active specialist. The `reviewer` agent is file-based (not a registered `subagent_type`), so use `subagent_type: "general-purpose"` and instruct the agent to follow the reviewer contract exactly:

   ```
   description: "<specialist> review"
   subagent_type: "general-purpose"
   prompt: |
     Follow the instructions in @${CLAUDE_PLUGIN_ROOT}/agents/reviewer.md exactly.
     Diff file: <absolute DIFF_PATH from build_diff.sh>
     Review context: @${CLAUDE_PLUGIN_ROOT}/context/review-<specialist>.md
     Output must match the reviewer template verbatim.
   ```

4. **Collect outputs.** Each reviewer returns a Markdown block in the template from `@${CLAUDE_PLUGIN_ROOT}/agents/reviewer.md`. Do not alter individual outputs.

5. **Consolidate and report.** Before emitting, **deduplicate overlapping findings**. Two findings overlap when they describe the same underlying problem at the same (or adjacent, within ~2 lines) location — e.g. architect and comment both flagging a misleading docstring. For each overlap cluster:
   - Keep the finding from the specialist whose context primarily owns the concern (comment-accuracy issues → `comment`; SOLID/DRY/KISS/YAGNI/boundary issues → `architect`; untested public behavior / missing regression tests → `test-coverage`).
   - Merge the other specialists into a single trailing tag on the kept finding: `(also flagged by <specialist>[, …])`.
   - Use the highest priority across the cluster.
   - Never drop a finding that raises priority over the kept one — upgrade the kept finding instead.

   Then emit the final summary in this exact shape:

   ```markdown
   # Code Review Summary

   **Mode:** <working | branch (base=<ref>)>  •  **Diff:** <DIFF_PATH>  •  **Specialists:** architect[, …]  •  **Overall Verdict:** APPROVE | REQUEST CHANGES

   ## Consolidated Findings
   ### Critical
   - [<perspective>] file:line — … [(also flagged by <specialist>)]
   ### Important
   - [<perspective>] file:line — … [(also flagged by <specialist>)]
   ### Suggestions
   - [<perspective>] file:line — … [(also flagged by <specialist>)]
   ```

   **Overall verdict** = `REQUEST CHANGES` if any specialist returned `REQUEST CHANGES` or reported a Critical finding; otherwise `APPROVE`.

## Rules

- Do not invoke the reviewer without a review context file.
- Spawn specialists in parallel (single message, multiple `Agent` calls), never sequentially.
- Do not modify any source files during review.
- Do not fabricate findings or critique unchanged code — every finding must be anchored to a `file:line` inside the diff.
- If no specialists are active (all context files empty), stop and tell the user.

## Extending

To add a new perspective: author `@${CLAUDE_PLUGIN_ROOT}/context/review-<name>.md` and add a row to the Available Specialists table above. The `reviewer` agent does not need to change.
