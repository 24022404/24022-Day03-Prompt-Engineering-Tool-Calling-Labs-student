---
name: hn_search
track: bonus
kind: live_api
provider: Hacker News Algolia API
requires_env: []
inputs: [query, sort, limit]
outputs: [items]
side_effect: false
---
# hn_search

Searches Hacker News stories via the free Algolia API (no key). Good for what the
tech/developer community is discussing. `sort=popular` (by points) or `sort=latest`.