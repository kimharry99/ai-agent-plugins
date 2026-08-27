# eli5

Create a picture-led HTML explanation at the Grade Level you choose.

```
$eli5 how does DNS work
$eli5 --level high how does DNS work
$eli5 양자 얽힘을 대학원 수준으로 설명해 줘
```

The default is `5th`. Supported levels are `5th`, `middle`, `high`, `college`, and `graduate`; natural-language English and Korean aliases work too.

Every result is a picture-led HTML artifact with large visuals and short labels. Higher levels increase the information density and depth of the selected explanation instead of repeating explanations from lower levels.

| Grade Level | Depth |
|---|---|
| `5th` | Core principle and a familiar analogy |
| `middle` | Basic terms and a step-by-step process |
| `high` | Multi-step mechanism and major constraints |
| `college` | Conceptual model, applications, and trade-offs |
| `graduate` | Assumptions, precise mechanisms, exceptions, and limitations |

Use `--level <level>` or state the level naturally in the request. The skill asks for a topic when one is missing and asks you to choose a supported level when an explicit level is unsupported. It researches and cites external sources only when requested.
