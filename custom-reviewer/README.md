# custom-reviewer

Multi-perspective code and plan reviews for Claude Code and Codex.

This plugin gives you two review skills, `code-review` and `plan-review`, that fan out a shared file-based reviewer agent across every active "review context" in parallel, then consolidate the findings into a single Critical / Important / Suggestion summary.

This plugin is for Claude Code and Codex users who want PR-style reviews or plan/spec sanity checks from inside their normal workflow, with a pluggable way to add new review perspectives.

## What You Get

- `code-review` — review uncommitted changes or a branch diff (PR-style) through every active specialist in parallel
- `plan-review` — review a single plan/spec document (defaults to the latest file in `~/.claude/plans/` under Claude Code)
- A shared `reviewer` agent with a strict, diff-anchored output template
- A **pluggable review-context** system — drop a new `context/review-<name>.md` file to add a perspective
- Shipped perspectives:
  - **architect** (SOLID / DRY / KISS / YAGNI, module boundaries, dependency direction), backed by `docs/software_architecture.md`
  - **comment** (code-comment accuracy, staleness, and long-term maintainability; `/code-review` only)
  - **simplification** (local clarity — naming, nesting, dead code, redundant patterns, idiom fit; `/code-review` only)
  - **document-writing** (Intro-Body-Conclusion structure, big-picture-first flow; `/plan-review` only)
  - **plan-format** (the Introduction / Body / Conclusion skeleton and its required subsections — §1.1 Context, §1.2 Goal, §1.3 Non-goals, §2.1 Proposed Approach, §2.2 Alternatives Considered, §2.3 Risks / Trade-offs, §2.4 Test / Validation Plan, §3.1 Summary, §3.2 Open Questions; `/plan-review` only), backed by `docs/plan_format.md`
- Reserved slot: **performance** (empty placeholder, activates automatically once you fill it in)

## Requirements

- **Claude Code** with plugin support (`/plugin` command available), or **Codex** with `codex plugin` support
- **git** — the diff builders shell out to `git diff` / `git merge-base`
- **bash** — for the diff-builder scripts under `skills/*/scripts/`

## Install

### Claude Code

Install the plugin:

```bash
/plugin install custom-reviewer@ai-agent-plugins
```

Reload plugins:

```bash
/reload-plugins
```

### Codex

Add this repository as a local Codex marketplace, then install the plugin:

```bash
codex plugin marketplace add /absolute/path/to/ai-agent-plugins
codex plugin add custom-reviewer@ai-agent-plugins
```

After Claude Code install, you should see:

- the `/code-review` and `/plan-review` slash commands
- the review contexts under `context/` (architect is active out of the box; performance is a reserved empty slot)

A quick first Claude Code run inside any git repo:

```text
/code-review
```

In Codex, invoke the installed `code-review` or `plan-review` skill by name in your normal Codex session.

## Usage

### `/code-review`

Runs a multi-perspective review on a code diff. Each active specialist runs in parallel against the same diff and returns findings anchored to `file:line`.

Scope modes:

| Mode | What it diffs |
|---|---|
| `working` | Uncommitted changes (staged + unstaged against HEAD) |
| `branch`  | `merge-base(<base>, HEAD)..HEAD` — PR-style. Working-tree changes, if any, are appended. |

The skill auto-selects `working` vs `branch` based on git state; pass an explicit base with a branch request when you want PR-style review. Base resolution order: explicit base → upstream `@{u}` → `origin/HEAD` → `origin/main` / `origin/master` / `main` / `master`.

Examples:

```text
Review my working tree.
Run a code review against origin/main.
```

Output: a `# Code Review Summary` block with Critical / Important / Suggestion findings plus an overall `APPROVE` / `REQUEST CHANGES` verdict. The underlying diff is written to `.claude/tmp/code-review-<timestamp>.diff` in the target repo.

This command is read-only — it never modifies source files.

### `/plan-review`

Runs the same reviewer pipeline against a single plan/spec markdown document — treated as a new-file diff — so you can sanity-check a draft before implementation.

By default it picks the most recently modified `*.md` under `~/.claude/plans/`; override with `--plan <path>`.

Examples:

```text
Review my latest plan.
Review the plan at ~/.claude/plans/foo.md.
```

Output: a `# Plan Review Summary` block with the same Critical / Important / Suggestion structure.

This command is read-only.

## How It Works

1. The skill's helper script builds a unified diff and writes it under `.claude/tmp/`.
2. The skill enumerates active specialists — every row in its *Available specialists* table whose review-context file exists and is non-empty. Empty or missing contexts are skipped automatically.
3. It spawns one `general-purpose` subagent per specialist **in parallel**, each instructed to follow `agents/reviewer.md` exactly with the diff path and the review-context path injected.
4. Each reviewer reads any `@`-referenced docs from its context (e.g. the architect context pulls in `docs/software_architecture.md`), anchors findings to `file:line` inside the diff, and returns a Markdown block in the fixed reviewer template.
5. The skill consolidates every reviewer's output. Overall verdict is `REQUEST CHANGES` if any specialist requested changes or reported a Critical finding; otherwise `APPROVE`.

## Adding a New Perspective

1. Create `context/review-<name>.md` with:
   - a one-line purpose
   - a checklist of checkpoints (phrased to apply to both code diffs and plan diffs)
   - priority hints (what's Critical vs Important vs Suggestion under this perspective)
   - any `@`-referenced reference docs the reviewer should load
2. Add a row for the new specialist to the *Available specialists* table in `skills/code-review/SKILL.md` and/or `skills/plan-review/SKILL.md`, depending on where it should apply.
3. Done — the `reviewer` agent itself does not change. An empty context file is treated as "not ready" and skipped, so reserving slots ahead of time is safe.

## Repo Layout

```
.claude-plugin/
├── plugin.json                        # Claude Code plugin manifest
└── marketplace.json                   # Self-hosted marketplace entry

agents/
└── reviewer.md                        # file-based reviewer contract (template + rules)

context/
├── review-architect.md                # SOLID / DRY / KISS / YAGNI + boundaries
├── review-comment.md                  # code-comment accuracy & maintainability
├── review-document-writing.md         # Intro-Body-Conclusion + big-picture-first (plan-review)
├── review-plan-format.md              # Introduction / Body / Conclusion skeleton + required subsections (plan-review)
├── review-simplification.md           # local clarity (naming, nesting, dead code, idiom fit)
└── review-performance.md              # (placeholder — empty, reserved slot)

docs/
├── plan_format.md                     # referenced by the plan-format context
└── software_architecture.md           # referenced by the architect context

skills/
├── code-review/
│   ├── SKILL.md
│   └── scripts/build_diff.sh
└── plan-review/
    ├── SKILL.md
    └── scripts/build_plan_diff.sh
```

All cross-file references inside the plugin (skills → agent, contexts → docs) are written as `@${CLAUDE_PLUGIN_ROOT}/...`, so the layout above is the canonical plugin root.

## Local Development

You can develop and test this plugin against itself — no publish step needed.

```bash
# From a target repo where you want to run reviews:
/plugin marketplace add /absolute/path/to/ai-agent-plugins
/plugin install custom-reviewer@ai-agent-plugins
/reload-plugins
```

Then edit files in this repo and run `/reload-plugins` in the target session to pick up the changes. `/code-review` writes its diff to `<target-repo>/.claude/tmp/`, not into this plugin's repo.

For Codex, re-run `codex plugin marketplace add /absolute/path/to/ai-agent-plugins` in an isolated `CODEX_HOME` or remove and reinstall the plugin after editing metadata.
