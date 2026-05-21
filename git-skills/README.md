# git-skills

GitHub PR lifecycle skills for Claude Code and Codex.

Covers the full PR workflow: creating PRs, rebase-merging, analyzing existing review feedback, and applying review fixes with commit & push then replying to threads.

## Skills

| Skill | Description |
|---|---|
| `/open-pr` | Push the current branch (if needed) and open a GitHub PR. Title summarizes ALL commits; body in Korean. |
| `/pr-merge` | Rebase source branch onto target, then merge via merge commit. Stops on conflicts and asks user to resolve. |
| `/pr-review-analyze` | Fetch all reviews on a PR and produce a Critical / Important / Suggestion consolidated report. |
| `/pr-review-apply` | Commit & push review fixes, then reply to each review thread. Copilot bot threads are auto-replied; human reviewer threads require confirmation. |

All skills try GitHub MCP tools first and fall back to the `gh` CLI automatically.

## Requirements

- **Claude Code** with plugin support, or **Codex** with `codex plugin` support
- **git** — branch state, push, rebase, fetch
- **gh** (GitHub CLI) — fallback when GitHub MCP is unavailable; must be authenticated (`gh auth status`)
- **GitHub MCP server** (optional but recommended) — detected at runtime via tool name patterns

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
└── pr-review-apply/
    └── SKILL.md
```

## Local Development

```bash
/plugin marketplace add /absolute/path/to/ai-agent-plugins
/plugin install git-skills@ai-agent-plugins
/reload-plugins
```

Edit SKILL.md files and run `/reload-plugins` to pick up changes in Claude Code. For Codex, reinstall the plugin from the local marketplace after changing metadata or skills.
