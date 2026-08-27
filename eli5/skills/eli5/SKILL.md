---
name: eli5
description: Create a picture-led HTML explanation of a topic at a selected Grade Level. Use when the user invokes $eli5 or asks for a visual explanation for 5th grade through graduate level.
---

# eli5

Usage: $eli5 [grade-level] <topic>
Explain like I'm someone who knows nothing about this topic, using an HTML artifact with big pictures and few words.

## Grade Level

Grade Level is the only audience or depth setting.
Default to `5th` when no level is stated.

Support these values:

| Level | Explanation contract |
|---|---|
| `5th` | Explain only the core principle with a familiar analogy. |
| `middle` | Define basic terms and explain the process step by step. |
| `high` | Explain a multi-step mechanism and major constraints using standard terminology. |
| `college` | Connect an accurate conceptual model to practical applications and trade-offs. |
| `graduate` | Cover assumptions, precise mechanisms, exceptions, and limitations. |
