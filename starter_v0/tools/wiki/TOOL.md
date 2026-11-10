---
name: wiki
track: bonus
kind: live_api
provider: Wikipedia REST API
requires_env: []
inputs: [title, lang]
outputs: [title, summary, url]
side_effect: false
---
# wiki

Fetches the lead summary of a Wikipedia article (background / definition of a
concept, person or company). Free public API, no key. Not for breaking news.