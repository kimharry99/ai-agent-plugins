# worktree-habit

Worktree-first workflow guidance for Claude Code and Codex.

The plugin helps agents avoid editing source files directly on `main`. Before a
code change, the skill checks the current branch. On `main`, it creates an
in-repo worktree under `.worktree/<worktree_name>/` with a matching
`feature/<worktree_name>` branch, then continues the same session from that
worktree.

## Skill

| Skill | Description |
|---|---|
| `worktree-habit` | Check the current branch before code changes and create a feature worktree when starting from `main`. |

## Usage

Typical requests:

```text
Use a worktree before editing on main.
Set up a feature worktree for this change.
Check whether this task needs a worktree.
```

When the current branch is `main`, the skill uses:

```bash
git worktree add .worktree/<worktree_name> -b feature/<worktree_name>
```

After creation, all subsequent commands and edits happen from:

```text
{project root}/.worktree/<worktree_name>
```

For Python projects installed with `pip install -e .`, run Python commands from
the worktree with `PYTHONPATH` pointing at the worktree first:

```bash
PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}" pytest
PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}" python -m <module_name> ...
```

## Repo Layout

```text
.claude-plugin/
└── plugin.json

.codex-plugin/
└── plugin.json

skills/
└── worktree-habit/
    └── SKILL.md
```
