# ai-agent-plugins

A personal plugin marketplace for Claude Code and Codex.

## Plugins

| Plugin | Description |
|---|---|
| [python-harness](./python-harness/) | Python convention guidance for OOP, style, test layout, and test patterns. |
| [custom-reviewer](./custom-reviewer/) | Multi-perspective code reviews, reviewable plan drafting, and plan reviews. |
| [git-skills](./git-skills/) | GitHub PR lifecycle skills for opening PRs, merging, analyzing reviews, and applying feedback. |
| [worktree-habit](./worktree-habit/) | Worktree-first guidance for creating feature worktrees before editing on `main`. |
| [ssh-slurm](./ssh-slurm/) | Read-only SLURM guidance and generic SBATCH script generation. |
| [eli5](./eli5/) | HTML picture explainers with big visuals and very few words. |

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

`ssh-slurm` is currently packaged as a Codex MCP plugin rather than a Claude Code plugin.

## Codex Installation

Add this repository as a local Codex marketplace, then install individual plugins:

```bash
codex plugin marketplace add /absolute/path/to/ai-agent-plugins
codex plugin add python-harness@ai-agent-plugins
codex plugin add custom-reviewer@ai-agent-plugins
codex plugin add git-skills@ai-agent-plugins
codex plugin add worktree-habit@ai-agent-plugins
codex plugin add ssh-slurm@ai-agent-plugins
codex plugin add eli5@ai-agent-plugins
```

Codex reads marketplace metadata from `.agents/plugins/marketplace.json` and plugin metadata from each plugin's `.codex-plugin/plugin.json`.

## Plugin Structure

Cross-product plugins keep Claude Code and Codex metadata side by side. Codex-only plugins may omit Claude Code metadata:

```text
plugin-name/
├── .claude-plugin/
│   └── plugin.json      # Claude Code plugin metadata
├── .codex-plugin/
│   └── plugin.json      # Codex plugin metadata
├── skills/              # Shared skill definitions
├── agents/              # Agent definitions where supported
└── README.md            # Documentation
```
