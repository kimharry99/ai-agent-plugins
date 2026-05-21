# my-claude-plugins

A personal plugin marketplace for Claude Code and Codex.

## Plugins

| Plugin | Description |
|---|---|
| [python-harness](./python-harness/) | Python convention guidance for OOP, style, test layout, and test patterns. Claude Code also gets hook enforcement. |
| [custom-reviewer](./custom-reviewer/) | Multi-perspective code and plan reviews via specialist review contexts. |
| [git-skills](./git-skills/) | GitHub PR lifecycle skills for opening PRs, merging, analyzing reviews, and applying feedback. |

## Claude Code Installation

Add this repository as a marketplace in Claude Code, then install individual plugins:

```text
/plugin marketplace add kimharry99/my-claude-plugins
```

Install only the plugins you need:

```text
/plugin install python-harness@my-claude-plugins
/plugin install custom-reviewer@my-claude-plugins
/plugin install git-skills@my-claude-plugins
```

## Codex Installation

Add this repository as a local Codex marketplace, then install individual plugins:

```bash
codex plugin marketplace add /absolute/path/to/my-claude-plugins
codex plugin add python-harness@my-claude-plugins
codex plugin add custom-reviewer@my-claude-plugins
codex plugin add git-skills@my-claude-plugins
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
