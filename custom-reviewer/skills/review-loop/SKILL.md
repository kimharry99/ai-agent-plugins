---
name: review-loop
description: Runs specialist reviewers, synthesizes their outputs, auto-applies tactical fixes, requests user approval for conflicts or design direction changes, and repeats until the synthesized review is approved or 10 iterations are reached. Use when the user asks for an iterative or automated review-fix cycle. For single-pass review without fixing, use `code-review` or `plan-review`.
---

# review-loop

## Invocation

```
/review-loop [--plan [<path>]]
             [--mode working|branch|auto]
             [--base <ref>]
             [--only <specialist>[,<specialist>...]]
             [-- <pathspec>...]
```

| Flag | Meaning |
|---|---|
| `--plan [<path>]` | Plan mode: review a plan/spec document. If `<path>` omitted, picks most recently modified `*.md` under `~/.claude/plans/`. |
| `--mode working\|branch\|auto` | Code mode only. Same semantics as `code-review`. Default: `auto`. |
| `--base <ref>` | Code branch mode only. Base branch/commit for the diff. |
| `--only <s>[,<s>...]` | Override specialist set. Comma-separated names from the default tables below. |
| `-- <pathspec>...` | Code mode only. Limit diff to specific paths. |

## Default Specialists

| Mode | Specialists |
|---|---|
| code | architect, comment, simplification, test-coverage |
| plan | architect, document-writing, plan-format |

## Workflow

1. **Parse args.** Determine mode (`--plan` present → plan, otherwise code). Resolve the specialist list: if `--only` is given, use exactly those specialists — if any name does not appear in the default table above, stop with an error. If `--only` is absent, use the full default set for the mode.

2. **Build initial diff.**
   - Code: `${CLAUDE_PLUGIN_ROOT}/skills/code-review/scripts/build_diff.sh --mode <auto|...> [--base <ref>] [-- <pathspec>...]`
   - Plan: `${CLAUDE_PLUGIN_ROOT}/skills/plan-review/scripts/build_plan_diff.sh [--plan <path>]`
   - Record `DIFF_PATH`, `MODE`, `BASE` (branch mode), `PLAN` (plan mode) from stdout (`KEY=value` pairs).
   - Exit code `2` = nothing to review — stop.

3. **Initialize loop state.** `iteration = 1`, `max_iterations = 10`. Track the following across iterations:
   - `declined_issues` — descriptions of directional findings the user declined.
   - `applied_changes` — one aggregated summary per iteration (all fixes applied in that iteration combined into a single entry, mirroring the Final Report's "Iteration N" rows).
   - `fixed_decisions` — structured record of every applied fix: `{file, approx_location, description, reason, iteration}`.

4. **LOOP — repeat steps a–k:**

   a. **Enumerate active specialists.** Confirm each context file exists and is non-empty; skip missing or empty context files and warn the user which specialist was skipped (if all are skipped, apply the rule in the Rules section).

   b. **Fan out in parallel.** In a single message, emit one `Agent` tool call per active specialist. Values in `< >` are substituted at runtime from the recorded variables:
      ```
      description: "<specialist> review (iteration <N>)"
      subagent_type: "general-purpose"
      prompt: |
        Follow the instructions in @${CLAUDE_PLUGIN_ROOT}/agents/reviewer.md.
        Diff file: <absolute DIFF_PATH>
        Review context: @${CLAUDE_PLUGIN_ROOT}/context/review-<specialist>.md
        [plan mode only] The diff represents a plan/spec document treated as a new file.
        Anchor findings to file:line inside the diff.
        Output must match the reviewer template verbatim.
      ```
      If `fixed_decisions` is non-empty, append to the prompt:
      ```
      Previously applied fixes in this loop — do not re-flag for the same reason;
      only flag if the fix itself introduced a new, distinct problem:
      - Iteration <N>, <file> ~<approx_location>: <description> [reason: <reason>]
      - ...
      ```

   c. **Collect outputs.** Do not alter individual reviewer outputs.

   d. **Synthesize.** Invoke one synthesizer subagent:
      ```
      description: "review-loop synthesis (iteration <N>)"
      subagent_type: "general-purpose"
      prompt: |
        Follow the instructions in @${CLAUDE_PLUGIN_ROOT}/agents/review-synthesizer.md exactly.
        Diff file: <absolute DIFF_PATH>
        Mode: review-loop
        Output header: Review Loop Iteration Summary
        Review mode: <code|plan>
        [code mode only] Scope mode: <MODE>
        [branch mode only] Base: <BASE>
        [plan mode only] Plan: <PLAN>
        Active specialists: <active specialists, comma-separated>
        Review contexts:
        - <specialist>: @${CLAUDE_PLUGIN_ROOT}/context/review-<specialist>.md
        Specialist outputs:
        <paste each specialist output verbatim, labeled by specialist>
        Previously applied fixes:
        <fixed_decisions, or "None">
        Declined issues:
        <declined_issues, or "None">
      ```

      The synthesizer classifies findings with `ACCEPT`, `COMBINE`, `DISMISS`, `CONFLICT`, or `NEEDS_DECISION` using `@${CLAUDE_PLUGIN_ROOT}/docs/review_synthesis.md`. The rest of the loop uses the synthesized priority buckets, not the raw specialist outputs.

   e-bis. **Handle conflicts and required decisions.** For each synthesized `[CONFLICT]` or `[NEEDS_DECISION]` finding, present the finding and the reason it cannot be auto-applied:
      - For `[CONFLICT]`, present the competing recommendations and ask which direction wins. If it contradicts a previous fix, include the previous fix: `contradicts fix from iteration <N>: "<previous description>"`.
      - For `[NEEDS_DECISION]`, present the finding and ask whether to apply its recommended direction.

      Apply the chosen fix and update `fixed_decisions`, `applied_changes`, `declined_issues`, and the conflict-resolution log accordingly; or add the finding to `declined_issues` if the user declines it.

   e. **Check termination (APPROVED only).** If the synthesized verdict is `APPROVE` and no Critical or Important findings remain in the synthesized output → break loop.

   f. **Classify all non-conflict synthesized findings** (Critical, Important, and Suggestions) into two buckets:

      - **Directional** (user approval required): the fix requires changing the *fundamental design direction or architecture* of a component — a different overall approach is needed, not just correcting an existing implementation (e.g. rewriting a stateless module as a class).
      - **Tactical** (auto-apply): everything else — comment fixes, dead code removal, renames, multi-file refactors, or any other localized change (e.g. renaming a method).

   g. **Handle directional findings.** For each directional finding: skip without re-prompting if its description substantially matches an entry in `declined_issues`. Otherwise:
      - Present the finding and its fix recommendation to the user.
      - If approved: apply the fix with Edit/Write tools; collect a one-line fix note (to be combined into `applied_changes` at step k); add a structured entry to `fixed_decisions`.
      - If declined: add the finding's description to `declined_issues`.

   h. **Apply tactical findings.** For each tactical finding, apply the fix directly with Edit/Write tools. When multiple findings target the same file, batch edits. Collect a one-line fix note per file touched (to be combined into `applied_changes` at step k); add a structured entry per fix to `fixed_decisions`.

   i. **Check BLOCKED.** If no fixes were applied in this iteration (all findings matched entries in `declined_issues`) and termination is not yet met → break loop with BLOCKED.

   i-bis. **Check TIMEOUT.** If `iteration >= max_iterations` → break loop. (Placing this after fix application ensures every iteration completes a full review→fix cycle before stopping.)

   j. **Rebuild diff.** Re-run the same diff-building script with the original arguments. In plan mode, always pass `--plan <PLAN>` explicitly (using the value recorded in step 2) to guarantee the same plan file is reviewed across iterations. If exit code `2` (diff is now empty), treat as APPROVED.

   k. **Consolidate iteration summary.** Combine all fix notes collected in steps g and h during this iteration into a single entry appended to `applied_changes`. Then `iteration += 1`. Go to step 4a.

5. **Emit final report** (see format below).

## Final Report Format

```markdown
# Review Loop Summary

**Mode:** <code (working | branch base=<ref>) | plan (<path>)>  •  **Iterations:** <N> / 10  •  **Status:** APPROVED | TIMEOUT | BLOCKED

### Changes Applied
- Iteration 1: <one-line summary of fixes applied>
- Iteration 2: …

### Remaining Issues  *(TIMEOUT or BLOCKED only)*
#### Critical
- [<perspective>] file:line — …
#### Important
- [<perspective>] file:line — …
#### Suggestions
- [<perspective>] file:line — …

### Conflicts Resolved  *(if any)*
- Iteration <N> vs <M>: <conflict summary and resolution>

### Declined Changes  *(if any)*
- <one-line summary of each declined directional issue>
```

## Rules

- Every fix must correspond to a finding in the consolidated review output — never introduce unsolicited changes.
- Do not generalize, refactor, or improve beyond what each finding explicitly recommends.
- Do not invoke the reviewer without a review context file.
- If no specialists are active (all context files empty or missing), stop and tell the user.
