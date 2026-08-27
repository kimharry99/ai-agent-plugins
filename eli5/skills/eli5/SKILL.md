---
name: eli5
description: Create a picture-led HTML explanation of a topic at a selected Grade Level. Use when the user invokes $eli5 or asks for a visual explanation for 5th grade through graduate level.
---

# eli5

Explain like I'm someone who knows nothing about this topic—without talking down to me—and calibrate the entire picture-led HTML explanation to the selected Grade Level.

## Grade Level

Grade Level is the only audience or depth setting. Support these values:

| Level | Explanation contract |
|---|---|
| `5th` | Explain only the core principle with a familiar analogy. |
| `middle` | Define basic terms and explain the process step by step. |
| `high` | Explain a multi-step mechanism and major constraints using standard terminology. |
| `college` | Connect an accurate conceptual model to practical applications and trade-offs. |
| `graduate` | Cover assumptions, precise mechanisms, exceptions, and limitations. |

Accept `--level <level>` and natural-language aliases. Normalize English aliases such as `5th grade`, `fifth grade`, `elementary`; `middle school`, `junior high`; `high school`, `senior high`; `college`, `university`, `undergraduate`; and `graduate`, `grad school`, `postgraduate`. Normalize Korean aliases such as `초5`, `초등 5학년`, `초등학생`; `중학생`, `중학교`; `고등학생`, `고등학교`; `대학생`, `대학교`, `학부`; and `대학원생`, `대학원`, `석사`, `박사` to the corresponding canonical value.

Default to `5th` when no level is stated. If the user explicitly requests an unsupported level, ask them to choose one of `5th`, `middle`, `high`, `college`, or `graduate`. If the topic is missing, ask for it.

## Execution

1. Identify the topic and Grade Level from the request.
2. Normalize any alias to a supported canonical value.
3. Compose the entire explanation at that level. Do not stack or recap lower-level explanations. Use equations or formal notation only when they clarify the topic. Research and cite external sources only when the user requests it.
4. Generate a self-contained, picture-led HTML artifact. Lead with large visual elements and keep labels short at every level; use more information-dense diagrams at higher levels when useful. Let the selected contract control vocabulary, mechanism detail, applications, trade-offs, assumptions, exceptions, and limitations.
