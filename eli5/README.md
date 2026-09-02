# eli5

Create a picture-led HTML explanation for someone who knows nothing about a topic, at the presentation density you choose.

```
$eli5 how does DNS work
$eli5 --level middle how does DNS work
$eli5 --level college 양자 얽힘을 설명해 줘
```

The default is `age5`. Supported levels are `age5`, `middle`, and `college`; natural-language English and Korean aliases work too.

Every level assumes that the reader knows nothing about the topic. The request determines what to explain, while the selected level changes only the presentation format and information density. Every result is a self-contained, picture-led HTML artifact, with progressively more text from `age5` through `middle` to `college`.

| Explanation Level | Presentation |
|---|---|
| `age5` | Big pictures carry the explanation, with very few words, short labels, and plain-language sentences. |
| `middle` | Pictures and concise text share the explanation through short paragraphs, labeled diagrams, and plain-language definitions. |
| `college` | Diagrams organize a text-rich explanation with detailed paragraphs, precise terms, captions, and explicit logical connections. |

Use `--level <level>` or state the level naturally in the request.
