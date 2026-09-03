---
name: knowledge-db-work-record
description: Use when asked to archive work records, save task summaries, record debugging findings, preserve experiment results, or add handoff notes to the user's Knowledge DB.
---

# Knowledge DB Work Record

Use this skill to write concise work records into the user's lightweight
Knowledge DB.

## Location

Read the Knowledge DB root from the applicable `AGENTS.md` instructions. The
instructions must define it using this label:

```text
Knowledge DB root: /absolute/path/to/knowledge-db
```

Record directory:

```text
<Knowledge DB root>/10_records
```

Before writing, read the Knowledge DB README when available:

```text
<Knowledge DB root>/README.md
```

## Availability

Before reading or writing, verify that the Knowledge DB path above is mounted
and accessible. If it is unavailable, stop and report that the SMB share is
not mounted or accessible. Do not fall back to the former local path or any
other copy.

## Workflow

1. Identify the project from the current repo, prompt, branch, or referenced
   document path.
2. Gather concrete evidence from the active work: changed files, commands run,
   test results, failed attempts, decisions, open questions, and next steps.
3. Create a new Markdown record in `10_records/`; do not edit prior records
   unless the user explicitly asks.
4. Use minimal frontmatter only:

```yaml
---
type: record
date: YYYY-MM-DD
project: project-name
summary: One concise sentence.
---
```

Do not add a `status` field.

## Body Guidance

Keep the body free-form and source-aware. Include only information that helps a
future human or LLM resume the work:

- context and objective
- decisions made and why
- failed attempts or rejected paths
- commands, outputs, and verification results
- exact paths to important source files or generated artifacts
- next actions or unresolved risks

Use Korean when the surrounding task is in Korean unless the user requests a
different language.

## Stopping Condition

Finish when a new record exists, follows the README/frontmatter rules, and the
final response names the record path.
