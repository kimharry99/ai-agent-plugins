# Codex Plugin Expansion Plan

## 1. Introduction

### 1.1 Context

[High-level] This repository currently works as a Claude Code plugin marketplace, but Codex needs its own plugin manifests and marketplace metadata before these same workflows can be installed and discovered from Codex.

[Detail] The existing plugin roots are `python-harness/`, `custom-reviewer/`, and `git-skills/`. Each root already has a Claude manifest under `.claude-plugin/plugin.json`, skills under `skills/`, and documentation in `README.md`. Codex ingestion requires `.codex-plugin/plugin.json` with valid interface metadata and accepts skills through the existing `skills/` layout, but it does not accept Claude-only manifest fields such as hooks in `plugin.json`. The work must preserve the Claude marketplace while adding Codex-facing metadata and validation.

### 1.2 Goal

[High-level] Add a Codex-compatible plugin layer for all existing plugin packages without breaking current Claude Code installation paths.

[Detail] Success means all three plugin roots contain valid `.codex-plugin/plugin.json` files, a Codex marketplace file exists for local installation/discovery, README instructions explain both Claude and Codex usage, and the Codex validator passes for every plugin root. The minimum verification target is:

- `python3 /home/dmkim/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py python-harness`
- `python3 /home/dmkim/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py custom-reviewer`
- `python3 /home/dmkim/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py git-skills`

### 1.3 Non-goals

[High-level] This pass is a packaging and compatibility expansion, not a rewrite of the plugin behaviors.

[Detail] The plan does not redesign review orchestration, rewrite hook logic, convert Claude-specific slash-command UX into a different command framework, publish to a remote marketplace, or change the existing `.claude-plugin/marketplace.json` contract except where documentation must mention Codex alongside Claude. If Codex hooks need a different runtime contract than Claude hooks, this pass will document that limitation instead of inventing an unverified hook adapter.

## 2. Body

### 2.1 Proposed Approach

[High-level] Keep each existing plugin directory as the canonical plugin root and add Codex metadata beside the existing Claude metadata, then validate each root independently.

[Detail] The implementation should treat the current layout as the source of truth:

```text
ai-agent-plugins/
├── .claude-plugin/marketplace.json
├── .agents/plugins/marketplace.json        # new Codex marketplace catalog
├── python-harness/
│   ├── .claude-plugin/plugin.json
│   ├── .codex-plugin/plugin.json           # new
│   ├── hooks/
│   ├── rules/
│   └── skills/
├── custom-reviewer/
│   ├── .claude-plugin/plugin.json
│   ├── .codex-plugin/plugin.json           # new
│   ├── agents/
│   ├── context/
│   ├── docs/
│   └── skills/
└── git-skills/
    ├── .claude-plugin/plugin.json
    ├── .codex-plugin/plugin.json           # new
    └── skills/
```

The Codex manifests should include only fields accepted by the local validator: `name`, `version`, `description`, `author`, optional `keywords`, `skills`, and `interface`. The `skills` field should be `skills`, matching the validator's normalized contract path. `hooks` should not be added to Codex `plugin.json`; for `python-harness`, hook behavior should be described as Claude-only unless a Codex hook contract is found locally and can be validated.

### 2.2 Implementation Todo

[High-level] The Codex layer was built in small, reviewable steps so validation failures identified a single class of issue at a time.

[Detail] Completion state after implementation:

- [x] Create `.codex-plugin/plugin.json` for `custom-reviewer` with display metadata, capabilities, starter prompts, and `skills: "skills"`.
- [x] Create `.codex-plugin/plugin.json` for `git-skills` with display metadata focused on GitHub PR lifecycle skills and `skills: "skills"`.
- [x] Create `.codex-plugin/plugin.json` for `python-harness` with display metadata for Python rule guidance and `skills: "skills"`, while deliberately omitting `hooks`.
- [x] Create `.agents/plugins/marketplace.json` as the repo-local Codex marketplace catalog with entries for all three plugins, installation policy `AVAILABLE`, authentication policy `ON_INSTALL`, and category `Productivity`.
- [x] Update the root `README.md` so the repository is described as a Claude Code and Codex plugin collection, with separate installation sections for each host.
- [x] Update each plugin README only where host behavior differs, especially the `python-harness` hook limitation under Codex.
- [x] Run the Codex plugin validator for all three plugin roots and fix any manifest/schema failures.
- [x] Run JSON syntax checks for every new or changed JSON file.
- [x] Review the final diff to ensure no Claude plugin metadata was removed and no generated placeholder text remains.

### 2.3 Alternatives Considered

[High-level] The chosen approach favors preserving the existing repository layout over a larger canonical directory migration.

[Detail]

- Alternative A: Move all plugin roots under `plugins/<name>/` to match the Codex scaffold's default marketplace examples. This would align with a fresh Codex scaffold but would force updates to the existing Claude marketplace, documentation, and any local user paths. It is higher risk for a packaging-only expansion.
- Alternative B: Duplicate each plugin under a new Codex-only `plugins/` tree. This avoids moving the Claude roots but creates two copies of every skill and README, making future maintenance error-prone.
- Alternative C: Add Codex metadata beside the existing Claude metadata. This keeps one canonical copy of each plugin and makes validation local to each plugin root. This is the selected approach, with the explicit validation step deciding whether marketplace paths need adjustment.

### 2.4 Risks / Trade-offs

[High-level] The main trade-off is preserving the current layout even though Codex scaffold examples prefer a `plugins/<name>/` marketplace path.

[Detail]

- Risk: Codex marketplace ingestion may require `source.path` values shaped exactly like `./plugins/<name>`. Mitigation: validate plugin roots first, then test the marketplace file shape locally; if marketplace ingestion rejects root-level plugin paths, add a follow-up migration to `plugins/<name>/` rather than silently duplicating content.
- Risk: `python-harness` relies on Claude hook events that may not exist in Codex. Mitigation: omit unsupported hook fields from Codex manifests and document Codex support as skill/rule guidance only until a validated Codex hook contract is available.
- Risk: Existing skill documents contain Claude-specific tool names and instructions. Mitigation: do not rewrite behavior in bulk during packaging; instead, scan for host-specific language and update only text that would mislead Codex users about available commands or hooks.
- Risk: Marketplace metadata could drift from plugin manifests. Mitigation: keep plugin names identical to directory names and manifest names, and run JSON checks plus manual diff review before implementation is considered complete.

### 2.5 Test / Validation Plan

[High-level] Validate both machine-readable manifests and the user-facing documentation path.

[Detail] Run these checks after implementation:

```bash
python3 /home/dmkim/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py python-harness
python3 /home/dmkim/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py custom-reviewer
python3 /home/dmkim/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py git-skills
python3 -m json.tool python-harness/.codex-plugin/plugin.json >/tmp/python-harness-codex-plugin.json
python3 -m json.tool custom-reviewer/.codex-plugin/plugin.json >/tmp/custom-reviewer-codex-plugin.json
python3 -m json.tool git-skills/.codex-plugin/plugin.json >/tmp/git-skills-codex-plugin.json
python3 -m json.tool .agents/plugins/marketplace.json >/tmp/my-codex-marketplace.json
git diff --check
```

Manual validation should confirm that Claude install instructions still point to `.claude-plugin/marketplace.json`, Codex instructions point to the new Codex marketplace catalog, and `python-harness` does not claim Codex hook enforcement unless that behavior has been proven.

## 3. Conclusion

### 3.1 Summary

[High-level] This plan adds Codex packaging to the existing Claude plugin collection by placing validated `.codex-plugin/plugin.json` files beside the current Claude manifests, adding a Codex marketplace catalog, and documenting host-specific behavior.

[Detail] The approach solves the immediate discoverability and installation gap while keeping one canonical copy of each plugin's skills and docs. The accepted trade-off is that the current root-level plugin layout may need a later marketplace-path migration if Codex ingestion proves stricter than the local plugin validator; the validation plan makes that failure explicit.

### 3.2 Open Questions

[High-level] One marketplace-path detail may require confirmation during implementation, but it does not block manifest work.

[Detail] The implementation owner must decide, after local Codex marketplace testing, whether `.agents/plugins/marketplace.json` may reference the existing root-level plugin directories directly or whether the repository should be migrated to a canonical `plugins/<name>/` layout in a separate change.
