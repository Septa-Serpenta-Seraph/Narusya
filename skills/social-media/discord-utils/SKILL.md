---
name: discord-utils
description: Tools for interacting with Discord, including fetching channel history and inspecting server state.
tags: [discord, history, tools]
---

# Discord Utils Skill

Mechanical tools to interact with Discord via `discord.py`.

## Usage

### Fetch Channel History
Read the last messages from a channel by ID.

1. Locate the Discord API key (token) in the shared settings file.
2. Execute the fetch script using the path to the virtual environment's interpreter.

```bash
./.hermes/hermes-agent/venv/bin/python3 ~/.hermes/skills/social-media/discord-utils/scripts/fetch.py \
  --cid <CHANNEL_ID> \
  --lim <LIMIT> \
  --key "<DISCORD_TOKEN>"
```

## Implementation Details
Uses the `discord.py` package. Requires a valid bot key passed as the `--key` argument.
