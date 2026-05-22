# git-skills

GitHub PR lifecycle skills for Claude Code and Codex.

Covers the full PR workflow: creating PRs, rebase-merging, analyzing existing review feedback, applying review fixes with commit & push, replying to threads, and completing PRs through merge and local cleanup.

## Skills

| Skill | Description |
|---|---|
| `/open-pr` | Push the current branch (if needed) and open a GitHub PR. Title summarizes ALL commits; body in Korean. |
| `/pr-merge` | Rebase source branch onto target, then merge via merge commit. Stops on conflicts and asks user to resolve. |
| `/pr-review-analyze` | Fetch all reviews on a PR and produce a Critical / Important / Suggestion consolidated report. |
| `/pr-review-apply` | Commit & push review fixes, then reply to each review thread. Copilot bot threads are auto-replied; human reviewer threads require confirmation. |
| `/pr-complete` | Open or locate a PR, analyze reviews, apply only agreed feedback, run one code-review gate, merge, update main, and clean up local worktree/branch state. |

All skills try GitHub MCP tools first and fall back to the `gh` CLI automatically.

## Requirements

- **Claude Code** with plugin support, or **Codex** with `codex plugin` support
- **git** — branch state, push, rebase, fetch
- **gh** (GitHub CLI) — fallback when GitHub MCP is unavailable; must be authenticated (`gh auth status`)
- **GitHub MCP server** (optional but recommended) — detected at runtime via tool name patterns
- **custom-reviewer plugin** (optional) — used by `/pr-complete` for the code-review gate when installed; otherwise `/pr-complete` runs a built-in single-pass diff review fallback.

## Install

### Claude Code

```bash
/plugin install git-skills@ai-agent-plugins
/reload-plugins
```

### Codex

```bash
codex plugin marketplace add /absolute/path/to/ai-agent-plugins
codex plugin add git-skills@ai-agent-plugins
```

## Usage

### `/open-pr`

Analyzes all commits since the branch diverged from `main`, pushes if needed, and opens a PR.

```
Open a PR for this branch.
Push and create a PR.
```

PR body is written in Korean unless you specify otherwise.

### `/pr-merge`

Rebases the current branch onto `main` (or a specified target) and merges with a merge commit.

```
Merge this PR.
Merge PR #42 into main.
Rebase and merge.
```

If `git rebase` produces conflicts, the skill stops and instructs you to resolve them manually before re-running.

### `/pr-review-analyze`

Fetches all reviews and inline comments and consolidates them.

```
Analyze the reviews on this PR.
Summarize what reviewers said about PR #55.
Show me the review feedback.
```

Output follows the custom-reviewer format: `# PR Review Analysis` with Critical / Important / Suggestions findings and a per-reviewer summary.

### `/pr-review-apply`

Intended for use after `/pr-review-analyze`. Commits & pushes all applied review fixes, then walks through every unresolved thread one by one.

```
Apply the review feedback.
Address the review on PR #42.
```

Phase 1 — commits & pushes existing code changes with a review-summary message. Phase 2 — for each thread: shows full context → drafts Korean reply → auto-submits for Copilot bot threads, waits for `yes / skip / edit: <text> / stop` for human reviewers.

### `/pr-complete`

Runs the branch through the full PR lifecycle.

```
Complete this PR workflow.
Open and merge this PR.
PR 만들고 병합까지 진행해줘.
```

The workflow opens or locates the PR, analyzes review feedback, applies only feedback labeled `Agree`, runs exactly one code-review gate, merges via `/pr-merge`, updates `main`, then removes the completed branch's worktree and deletes the local branch.

The code-review gate prefers `custom-reviewer:code-review` in branch mode when that plugin is installed. If it is not installed, `/pr-complete` does not skip review; it runs a built-in single-pass diff review using `git diff --check`, `git diff --stat`, and `git diff` against the PR base. Critical or Important findings stop the workflow in either path.

`/pr-complete` never applies `Disagree` or `Unclear` review items, never runs an automatic review-fix loop, and never deletes remote branches.

## Repo Layout

```
.claude-plugin/
└── plugin.json

.codex-plugin/
└── plugin.json

skills/
├── open-pr/
│   └── SKILL.md
├── pr-merge/
│   └── SKILL.md
├── pr-review-analyze/
│   └── SKILL.md
├── pr-review-apply/
│   └── SKILL.md
└── pr-complete/
    └── SKILL.md
```

## Local Development

```bash
/plugin marketplace add /absolute/path/to/ai-agent-plugins
/plugin install git-skills@ai-agent-plugins
/reload-plugins
```

Edit SKILL.md files and run `/reload-plugins` to pick up changes in Claude Code. For Codex, reinstall the plugin from the local marketplace after changing metadata or skills.

## Validation

```bash
python3 /home/dmkim/.codex/skills/.system/skill-creator/scripts/quick_validate.py git-skills/skills/pr-complete
python3 /home/dmkim/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py git-skills
```

When changing `/pr-complete`, dry-review both code-review paths: with `custom-reviewer:code-review` available and with the built-in diff review fallback. Confirm that `Disagree` or `Unclear` Critical/Important review items stop before merge, and that worktree cleanup uses only `git worktree remove` plus `git branch -d`.
