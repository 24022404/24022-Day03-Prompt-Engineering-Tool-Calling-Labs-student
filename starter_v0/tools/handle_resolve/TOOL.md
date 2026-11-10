---
name: handle_resolve
track: bonus
kind: local_knowledge
provider: local_dictionary
requires_env: []
inputs: [name]
outputs: [name, handle, found, candidates]
side_effect: false
---
# handle_resolve

Maps a person or organisation name (e.g. "Sam Altman", "OpenAI") to its X/Twitter
handle without the `@` (e.g. `sama`). Purely local dictionary, no network.
If the name is unknown, returns `found=false` so the agent should ask the user (`clarify`)
instead of guessing.