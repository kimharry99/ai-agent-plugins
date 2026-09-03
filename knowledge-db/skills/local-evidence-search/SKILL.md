---
name: local-evidence-search
description: Use when asked to find prior work, search local Knowledge DB records, recover past commands or results from prior Codex sessions, or answer from locally recorded project history before speculating.
---

# Local Evidence Search

## Source Order

Prefer recent, structured evidence before session-log searching.

1. Search the Knowledge DB root configured in the applicable `AGENTS.md`
   instructions using the label `Knowledge DB root`.
2. If the Knowledge DB is insufficient, search recent Codex logs:
   `~/.codex/history.jsonl` and
   `~/.codex/sessions/`.

Use Chronicle only if a Chronicle connector or tool is actually available.
If it is unavailable, say so and do not infer evidence from it.

Before searching, verify that the Knowledge DB path is mounted and accessible.
If it is unavailable, stop and report that the SMB share is not mounted or
accessible. Do not fall back to the former local path or any other copy.

## Search Pattern

Start narrow, then pivot by mechanism.

- Search exact project names, paths, branch names, artifact names, error text,
  command names, and output filenames.
- If exact phrase search fails, pivot to nearby mechanism terms. For visual
  bugs this might mean `depth`, `alpha`, `mask`, `camera`, `overlap`,
  `visible`, `render`, or `pointcloud`.
- For time-sensitive or stateful questions, prefer the newest relevant record
  first and explicitly re-check current source state when practical.
- When the user names a concrete path, search that path first.

Do not open many old records just to be exhaustive. Stop once the evidence is
strong enough for the user's question, unless the user asked for a broad audit.

## Knowledge DB Rules

When reading Knowledge DB records, preserve the difference between source
records, syntheses, and principles.

- `10_records/` are source records.
- `20_syntheses/` are derived patterns.
- `30_principles/` are reusable rules.

Do not rewrite old records unless the user explicitly asks. For newly saved
records, use the separate `knowledge-db-work-record` skill.

## Reporting

Report the evidence path, date, and confidence. State whether the answer is:

- confirmed by source files or current repo state,
- based on past records and possibly stale,
- not found after the searched sources,
- or blocked by unavailable tooling.

For Korean prompts, answer in Korean unless the user asks otherwise.

## Stopping Condition

Finish when the answer includes the relevant local evidence, the searched
source classes, and any remaining uncertainty or next search keywords.
