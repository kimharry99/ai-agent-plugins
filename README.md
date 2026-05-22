# ai-agent-plugins

A personal plugin marketplace for Claude Code and Codex.

## Plugins

| Plugin | Description |
|---|---|
| [python-harness](./python-harness/) | Python convention guidance for OOP, style, test layout, and test patterns. Claude Code also gets hook enforcement. |
| [custom-reviewer](./custom-reviewer/) | Multi-perspective code and plan reviews via specialist review contexts. |
| [git-skills](./git-skills/) | GitHub PR lifecycle skills for opening PRs, merging, analyzing reviews, and applying feedback. |
| [worktree-habit](./worktree-habit/) | Worktree-first guidance for creating feature worktrees before editing on `main`. |

## Claude Code Installation

Add this repository as a marketplace in Claude Code, then install individual plugins:

```text
/plugin marketplace add kimharry99/ai-agent-plugins
```

Install only the plugins you need:

```text
/plugin install python-harness@ai-agent-plugins
/plugin install custom-reviewer@ai-agent-plugins
/plugin install git-skills@ai-agent-plugins
/plugin install worktree-habit@ai-agent-plugins
```

## Codex Installation

Add this repository as a local Codex marketplace, then install individual plugins:

```bash
codex plugin marketplace add /absolute/path/to/ai-agent-plugins
codex plugin add python-harness@ai-agent-plugins
codex plugin add custom-reviewer@ai-agent-plugins
codex plugin add git-skills@ai-agent-plugins
codex plugin add worktree-habit@ai-agent-plugins
```

Codex reads marketplace metadata from `.agents/plugins/marketplace.json` and plugin metadata from each plugin's `.codex-plugin/plugin.json`.

## Plugin Structure

Each plugin keeps Claude Code and Codex metadata side by side:

```text
plugin-name/
├── .claude-plugin/
│   └── plugin.json      # Claude Code plugin metadata
├── .codex-plugin/
│   └── plugin.json      # Codex plugin metadata
├── hooks/               # Claude Code hook definitions where supported
├── skills/              # Shared skill definitions
├── agents/              # Agent definitions where supported
└── README.md            # Documentation
```
