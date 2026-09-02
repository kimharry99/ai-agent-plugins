---
name: eli5
description: Create a picture-led HTML explanation for someone who knows nothing about a topic, at a selected presentation density. Use when the user invokes $eli5 or asks for a visual explanation at age-5, middle, or college density.
---

# eli5

Usage: $eli5 [explanation-level] <topic>
Create a self-contained, picture-led HTML explanation for someone who knows nothing about the topic.

## Explanation Level

Assume at every level that the reader knows nothing about the topic. The user's request determines what to explain. The selected level controls only the presentation format and information density; do not add or remove categories of content because of the level.

Default to `age5` when no level is stated.

Support these values:

| Level | Presentation contract |
|---|---|
| `age5` | Let big pictures carry the explanation and use very few words. Use concrete visuals, short labels, and short sentences in plain language. |
| `middle` | Balance pictures with concise explanatory text. Use short paragraphs, labeled diagrams, and plain-language definitions for every necessary term. |
| `college` | Use diagrams to organize a text-rich explanation. Use detailed paragraphs, precise terminology, captions, and explicit logical connections, defining every term and notation when it first appears. |
