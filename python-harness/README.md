# python-harness

Python convention guardrails for Claude Code and Codex.

In Claude Code and Codex, this plugin enforces Python style and architectural rules through two hooks: a session-start context injector and a post-write guardrail. Codex also exposes the same rule material through the `python-rules` skill.

## What You Get

- **SessionStart hook** — injects all rules from `rules/` as context at the start of every session, so the agent is always aware of the project conventions
- **PostToolUse guardrail** — validates `.py` files on every Write/Edit or Codex `apply_patch` tool call and blocks writes that contain violations
- **Codex skill guidance** — exposes the Python rules through the `python-rules` skill for tasks that need explicit rule binding
- Four built-in rule sets:
  - **oop** — Strict OOP: all functions and non-constant variables must live inside classes
  - **python-style** — Google Python Style Guide (docstrings, naming, imports, line length, type annotations)
  - **test-layout** — Test files must mirror the source tree under `tests/`
  - **test-patterns** — No direct `_protected` access in tests; expose internals via a `_Testable*` subclass

## Requirements

- **Claude Code** with plugin support (`/plugin` command available), or **Codex** with `codex plugin` support
- **bash** — for the hook scripts under `hooks/`
- **jq** — for JSON handling in the PostToolUse guardrail
- **python3** — for AST-based import validation in the guardrail

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

After install, you should see the SessionStart hook fire at the beginning of your next session, injecting all four rule sets as a context reminder. No slash commands are registered — the plugin works silently through hooks.

A quick first run inside any Python project: ask Claude to add a module-level function. The PostToolUse hook will block the write and explain why the OOP rule requires all functions to live inside a class.

### Codex

Add this repository as a local Codex marketplace, then install the plugin:

```bash
codex plugin marketplace add /absolute/path/to/ai-agent-plugins
codex plugin add python-harness@ai-agent-plugins
```

In Codex, the plugin-bundled hooks are loaded from `hooks/hooks.json` and use `PLUGIN_ROOT` to find the installed plugin root. Codex requires hook trust review, so re-trust the hook definition when prompted after installing or updating this plugin. You can also use the installed `python-rules` skill as explicit guidance while editing Python projects.

## Usage

In Claude Code and Codex, the plugin hooks run automatically after the host trusts them. In Codex, invoke or rely on the `python-rules` skill guidance when Python convention checks are relevant.

### SessionStart: rule injection

At the start of every session, `hooks/rule-reminder.sh` reads all `.md` files from the `rules/` directory and injects their content into the session context. The agent receives a formatted reminder of every active rule before any work begins.

### PostToolUse: write guardrail

When the agent uses the Write/Edit or Codex `apply_patch` tool on a `.py` file, `hooks/check-python-rules.sh` validates the file and blocks the write if any of the following violations are found:

| Check | Applies to | What it catches |
|-------|-----------|-----------------|
| Banned builtins | All `.py` files | Use of `setattr`, `getattr`, or `hasattr` |
| Inline imports | Non-test `.py` files | `import` statements inside functions, methods, or conditionals |

If a violation is detected, the agent receives a block decision with a description of the problem and must fix it before the file can be written. If no violations are found, the hook exits silently and the write proceeds.

Test files (paths matching `*test_*`, `*_test.py`, `*/tests/*`, or `*/test/*`) are exempt from the inline import check.

## How It Works

1. **Session begins** — `rule-reminder.sh` scans `rules/` for all `.md` files, concatenates their content with formatting, and returns an additional-context JSON payload that the host injects into the session prompt.
2. **The agent writes a `.py` file** — `check-python-rules.sh` receives the file path or extracts it from a Codex `apply_patch` command, then runs the banned-builtin scan and the AST-based inline import check.
3. **Violations found** — the hook returns `{"decision": "block", "reason": "..."}` with the first violation details, preventing the write.
4. **No violations** — the hook exits with no output and the write proceeds normally.

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
2. The SessionStart hook picks it up automatically on the next session — no other changes needed.
3. To enforce the rule at write time (blocking violations), add a check to `hooks/check-python-rules.sh`.
4. To expose the rule via the `python-rules` skill (e.g. for `/goal` conditions), add a line to `skills/python-rules/SKILL.md`:
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

hooks/
├── hooks.json                     # Hook event registrations
├── rule-reminder.sh               # SessionStart: reads rules/ and injects as context
└── check-python-rules.sh          # PostToolUse: validates .py files on write/edit

rules/
├── oop.md                         # Strict OOP conventions
├── python-style.md                # Google Python Style Guide conventions
├── test-layout.md                 # Test file placement rules
└── test-patterns.md               # Test coding patterns (_Testable* subclass pattern)

skills/
└── python-rules/
    └── SKILL.md                   # Aggregates rules/*.md for /goal condition binding
```

Hook definitions resolve other plugin files through `PLUGIN_ROOT` in Codex and `CLAUDE_PLUGIN_ROOT` in Claude Code, so the layout above is the canonical plugin root.

## Local Development

You can develop and test this plugin against itself — no publish step needed.

```bash
# From a target repo where you want to run reviews:
/plugin marketplace add /absolute/path/to/ai-agent-plugins
/plugin install python-harness@ai-agent-plugins
/reload-plugins
```

Then edit files in this repo and run `/reload-plugins` in the target session to pick up the changes.

For Codex, reinstall the plugin from the local marketplace after changing metadata, skills, or hooks. Start a new thread and re-trust changed hooks when prompted so Codex picks up the updated definition.
