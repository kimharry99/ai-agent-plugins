---
title: Add plan-to-goal skill
---

## Initial User Prompt

새 skill을 적절한 플러그인에 만들어야 합니다.
이 스킬은 plan 마크다운 문서를 기반으로, goal 프롬프트를 생성합니다.

### Requirements

- Create a new `planning-tools` plugin containing a `plan-to-goal` skill.
- Require a plan document path as the skill argument.
- Resolve the provided plan path to an absolute path.
- Generate goal prompt text only; do not create or invoke a goal.
- Make `Task` instruct implementation of the plan document and include its absolute path.
- Emit exactly these sections: `Task`, `Expected behavior`, `Constraints`, `Verification`, and `Definition of done`.
- Treat the plan document as the sole source of requirements. Do not inspect the project to invent or supplement missing content.
- Use the plan document's primary language and preserve paths, commands, API names, and identifiers verbatim.
- Mark a section as not specified in the plan's primary language when the plan provides no supporting content.
- Stop with a clear error instead of emitting a partial prompt when the path is missing, nonexistent, not a regular file, or unreadable.
- Register and validate the plugin using this repository's Codex, Claude, and marketplace conventions.

## Description

// Will be filled in future stages by business analyst
