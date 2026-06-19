# python-harness

Python convention guidance for Claude Code and Codex.

This plugin packages Python style and architecture rules as documentation and
as the `python-rules` skill. It does not register runtime hooks or automatic
write-time checks.

## What You Get

- **Codex skill guidance** — exposes the Python rules through the
  `python-rules` skill for tasks that need explicit rule binding
- **Rule documents** — keeps the same rule material readable under `rules/`
- Four built-in rule sets:
  - **oop** — Strict OOP: all functions and non-constant variables must live inside classes
  - **python-style** — Google Python Style Guide (docstrings, naming, imports, line length, type annotations)
  - **test-layout** — Test files must mirror the source tree under `tests/`
  - **test-patterns** — No direct `_protected` access in tests; expose internals via a `_Testable*` subclass

## Requirements

- **Claude Code** with plugin support (`/plugin` command available), or **Codex** with `codex plugin` support

## Install

### Claude Code

Install the plugin:

```bash
/plugin install python-harness@ai-agent-plugins
```

Reload plugins:

```bash
/reload-plugins
```

After install, read the rule documents directly or reference them in prompts
when Python convention guidance is relevant. No slash commands or automatic
checks are registered by this plugin.

### Codex

Add this repository as a local Codex marketplace, then install the plugin:

```bash
codex plugin marketplace add /absolute/path/to/ai-agent-plugins
codex plugin add python-harness@ai-agent-plugins
```

In Codex, use the installed `python-rules` skill as explicit guidance while
editing Python projects.

## Usage

Use this plugin when a Python task should follow the bundled conventions. In
Codex, activate or rely on the `python-rules` skill. In Claude Code, reference
the rule documents from `rules/` in the task prompt or project guidance.

## Adding a New Rule

1. Create `rules/<name>.md` with a frontmatter header and the rule content:
   ```markdown
   ---
   globs: "*.py"
   description: "One-line description shown in session reminders"
   ---

   # Rule Title

   Rule content here.
   ```
2. To expose the rule via the `python-rules` skill (e.g. for `/goal`
   conditions), add a line to `skills/python-rules/SKILL.md`:
   ```
   @${CLAUDE_PLUGIN_ROOT}/rules/<name>.md
   ```

## Repo Layout

```
.claude-plugin/
├── plugin.json                    # Claude Code plugin manifest
└── marketplace.json               # Self-hosted marketplace entry

.codex-plugin/
└── plugin.json                    # Codex plugin manifest

rules/
├── oop.md                         # Strict OOP conventions
├── python-style.md                # Google Python Style Guide conventions
├── test-layout.md                 # Test file placement rules
└── test-patterns.md               # Test coding patterns (_Testable* subclass pattern)

skills/
└── python-rules/
    └── SKILL.md                   # Aggregates rules/*.md for /goal condition binding
```

## Local Development

You can develop and test this plugin against itself; no publish step is needed.

```bash
# From a target repo where you want to run reviews:
/plugin marketplace add /absolute/path/to/ai-agent-plugins
/plugin install python-harness@ai-agent-plugins
/reload-plugins
```

Then edit files in this repo and run `/reload-plugins` in the target session to pick up the changes.

For Codex, reinstall the plugin from the local marketplace after changing
metadata or skills.
