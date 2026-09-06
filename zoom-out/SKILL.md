---
name: zoom-out
description: Tell the agent to zoom out and give broader context or a higher-level perspective. Use when you're unfamiliar with a section of code or need to understand how it fits into the bigger picture.
disable-model-invocation: true
license: MIT
metadata:
  provenance: derived
  upstream: mattpocock/skills@801a01c:skills/engineering/zoom-out
  upstream-license: MIT
  changes: "body identical; description rewritten to state when to use it; removed upstream in 47bde84"
---

I don't know this area of code well. Go up a layer of abstraction. Give me a map of all the relevant modules and callers, using the project's domain glossary vocabulary.
