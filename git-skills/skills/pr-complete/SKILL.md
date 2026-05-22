---
name: pr-complete
description: "Complete a branch PR lifecycle end to end: open the PR, analyze reviews, apply only agreed review feedback, run one code-review gate, merge the PR, update main, and clean up any worktree and local branch. Use when the user says \"complete PR workflow\", \"open and merge PR\", \"PR 만들고 병합까지\", \"PR 끝까지 처리\", or \"/pr-complete\"."
---

# pr-complete

Run the full PR lifecycle for the current branch. This skill orchestrates the
existing git-skills workflows and adds a required one-pass code-review gate
before merging.

## Pre-flight

Collect the following in parallel:

- `<BRANCH>`: `git branch --show-current`
- `<STATUS>`: `git status --short`
- `<WORKTREES>`: `git worktree list --porcelain`
- `<TARGET>`: user-specified target branch, default `main`

If `<BRANCH>` equals `<TARGET>`, stop and tell the user this workflow must run
from a feature branch.

If `<STATUS>` is dirty before opening the PR, stop and ask the user to commit or
stash the changes first. Do not include unrelated uncommitted work in the PR
workflow.

## Workflow

### Step 1 - Open or locate the PR

Run the `open-pr` workflow for the current branch.

If `open-pr` reports an existing PR, continue with that PR. If PR creation or
push fails, stop immediately and report the failure.

After this step, resolve and retain:

- `<PR_NUMBER>`: `gh pr view --json number -q .number` or MCP equivalent
- `<PR_URL>`: `gh pr view --json url -q .url` or MCP equivalent
- `<PR_BASE>`: `gh pr view --json baseRefName -q .baseRefName` or MCP equivalent

If `<PR_BASE>` cannot be determined, use `<TARGET>`.

### Step 2 - Analyze PR reviews

Run the `pr-review-analyze` workflow for `<PR_NUMBER>`.

If review analysis has no reviewer feedback after its normal waiting/spooling
rules complete, continue to Step 4.

Classify the analysis output before applying anything:

- If any Critical or Important item is labeled `Disagree`, stop and report the
  item. Do not merge.
- If any Critical or Important item is labeled `Unclear`, stop and report the
  missing decision or context. Do not merge.
- Only items labeled `Agree` are eligible for automatic application.
- Suggestions labeled `Disagree` or `Unclear` may be reported but must not block
  the workflow unless they identify a concrete merge risk.

### Step 3 - Apply only agreed review feedback

If there are no `Agree` items, skip to Step 4.

Apply the `Agree` items only. Do not modify code for `Disagree` or `Unclear`
items.

After making the code changes, follow the commit, push, and reply rules from
the `pr-review-apply` workflow with this scope restriction:

- Commit only changes that implement the agreed feedback.
- Draft the commit message from the agreed items.
- Reply only to review threads whose feedback was applied or intentionally
  addressed by the agreed changes.
- Human reviewer replies still require confirmation.
- Bot reviewer replies may be submitted automatically.

If a push, commit, or required reply fails, stop immediately and report the
failure. Do not continue to the code-review gate.

### Step 4 - Run one code-review gate

Run exactly one code-review gate before merging.

#### Code-review gate discovery

Inspect the current session's available skills and tools. If a tool-search or
skill-search facility is available, search for `custom-reviewer code-review`
before choosing the path.

Treat the custom-reviewer path as available only when you can actually invoke a
`custom-reviewer:code-review` skill, a `code-review` skill, or an equivalent
registered code-review tool in this session. Do not assume availability because
the plugin exists in a repository or marketplace.

#### Preferred path - custom-reviewer available

If an installed skill or tool named `custom-reviewer:code-review` or
`code-review` is available, run it in branch mode against `<PR_BASE>`.

Continue only if the overall verdict is `APPROVE`.

If the verdict is `REQUEST CHANGES`, or if any Critical or Important finding is
reported, stop and show the findings. Do not auto-fix findings in this workflow.

#### Fallback path - custom-reviewer unavailable

If no custom-reviewer code-review skill is available, run a built-in single-pass
diff review. This fallback is mandatory; do not skip the code-review gate.

Fetch the latest base:

```bash
git fetch origin
```

Resolve the comparison base:

```bash
git merge-base origin/<PR_BASE> HEAD
```

Let the returned SHA be `<MERGE_BASE>`, then run:

```bash
git diff --check <MERGE_BASE>..HEAD
git diff --stat <MERGE_BASE>..HEAD
git diff <MERGE_BASE>..HEAD
```

If `git diff --check` fails, stop and report the whitespace or conflict-marker
errors.

Review the diff using normal code-review stance:

- Prioritize bugs, behavioral regressions, unsafe cleanup, missing validation,
  and missing tests.
- Findings must be grounded in changed lines or directly affected behavior.
- Do not critique unrelated pre-existing code.

Classify the fallback review:

- Critical or Important findings: stop and report them. Do not merge.
- Suggestions only: report them and continue.
- No findings: continue.

When this fallback path is used, include this line in the final result:

```text
custom-reviewer plugin not available; ran built-in single-pass diff review instead.
```

### Step 5 - Merge the PR

Run the `pr-merge` workflow for `<PR_NUMBER>` and `<PR_BASE>`.

`pr-merge` owns rebase, review-thread verification, Test Plan verification,
thread resolution, and merge-commit enforcement. If it stops for any reason,
stop this workflow too and report the same blocker. Do not bypass its checks.

Retain the merge commit SHA if `pr-merge` returns one.

### Step 6 - Update main

After the PR is merged, update a main worktree.

Find the worktree whose branch is `refs/heads/<TARGET>` in the pre-flight or
current `git worktree list --porcelain` output. If no such worktree exists, use
the current repository root only if it can safely checkout `<TARGET>`.

In the target-branch worktree, run:

```bash
git checkout <TARGET>
git pull --ff-only origin <TARGET>
```

If checkout or pull fails, stop and report the failure. Do not remove worktrees
or branches until main has been updated successfully.

### Step 7 - Clean up worktree and local branch

After main is updated, clean up the completed local branch.

Use `git worktree list --porcelain` to find any worktree whose branch is
`refs/heads/<BRANCH>`.

If a feature-branch worktree exists and is not the target-branch worktree, remove
it:

```bash
git worktree remove <FEATURE_WORKTREE_PATH>
```

Then delete the local branch:

```bash
git branch -d <BRANCH>
```

Never use `git worktree remove --force` or `git branch -D` in this workflow. If
either cleanup command fails, report the path, branch, and command output. Do
not delete the remote branch.

## Final output

Report:

- PR URL
- Merge commit SHA, if available
- Whether custom-reviewer or built-in fallback review was used
- Main update result
- Worktree cleanup result
- Local branch deletion result

## Rules

- Do not merge if Critical or Important review feedback is `Disagree` or
  `Unclear`.
- Do not apply changes for review feedback that is not labeled `Agree`.
- Do not skip the code-review gate.
- Run the code-review gate exactly once.
- Do not auto-fix code-review findings in this workflow.
- Do not bypass `pr-merge` Test Plan or review-thread checks.
- Do not delete remote branches.
