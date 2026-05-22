---
name: worktree-habit
description: Use a worktree-first workflow before code changes. Trigger on code changes, bug fixes, refactors, feature implementation, or explicit worktree setup requests.
---

# worktree-habit

Use this skill whenever a task may modify source files, tests, docs, plugin
metadata, generated project files, or any other repo-tracked content.

## Pre-flight gate

Before editing files or running commands that create or modify repo-tracked
files, check the current branch:

```bash
git branch --show-current
```

If the current branch is not `main`, continue in the current worktree.

If the current branch is `main`, do not edit repo files in place. Create an
in-repo worktree first, then continue the same session from that worktree.

## Worktree creation

Derive a short, lower-case, hyphen-delimited `<worktree_name>` from the task.
Use the same value for the feature branch suffix:

```bash
git worktree add .worktree/<worktree_name> -b feature/<worktree_name>
```

After the command succeeds, run all subsequent commands and file edits from:

```text
{project root}/.worktree/<worktree_name>
```

Do not create a `PLAN.md` handoff and do not require a new session. The
in-repo worktree is the active working directory for the rest of the task.

## Python worktree commands

Python projects are often installed into the active environment with:

```bash
pip install -e .
```

That editable install usually registers the original repository path in
site-packages. If code is edited in a Git worktree, Python may still import from
the original repository instead of the worktree, so changes can appear to be
missing or tests can fail for confusing reasons.

When running Python commands from a worktree, prepend the worktree root to
`PYTHONPATH` so the worktree source takes priority:

```bash
PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}" python -m <module_name> ...
```

Use the same pattern for tests, scripts, and one-off Python commands whenever
the project imports local source code:

```bash
PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}" pytest
PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}" python scripts/example.py
```

## Collision handling

Before creating a worktree, respect Git's existing checks for duplicate
branches and occupied paths. If the branch name or worktree path already
exists, stop and ask the user for an alternate name rather than guessing.

## Allowed on main

These actions are allowed before the worktree exists:

- Read-only exploration.
- Planning and answering questions.
- Checking Git branch and worktree state.
- Creating the feature branch and worktree with `git worktree add`.

These actions are not allowed on `main` before the worktree exists:

- Editing repo-tracked files.
- Creating generated project files.
- Running formatters or code generators that rewrite repo-tracked files.
- Committing or pushing feature work.
