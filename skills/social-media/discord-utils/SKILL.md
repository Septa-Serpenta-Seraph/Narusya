---
name: discord-utils
description: Tools for interacting with Discord, including fetching channel history and inspecting server state.
tags: [discord, history, tools]
---

# Discord Utils Skill

Mechanical tools to interact with Discord via `discord.py` or direct API calls.

## Usage

### Fetch Channel History (Method 1: discord.py)
Read the last messages from a channel by ID using discord.py library.

```bash
./.hermes/hermes-agent/venv/bin/python3 ~/.hermes/skills/social-media/discord-utils/scripts/fetch.py \
  --cid <CHANNEL_ID> \
  --lim <LIMIT> \
  --key "<DISCORD_TOKEN>"
```

### Fetch Channel History (Method 2: requests - When discord.py fails)
If discord.py gives 403 errors, use the requests-based approach:

```python
import requests

headers = {
    "Authorization": f"Bot {BOT_TOKEN}",
    "Content-Type": "application/json",
    "User-Agent": "DiscordBot (https://github.com/discord/discord-api-docs) Python/3.11"
}

url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages?limit=50"
response = requests.get(url, headers=headers)
messages = response.json()
```

**Note:** The `requests` library handles Discord's security checks better than urllib.

## Troubleshooting
- **403 Error**: Try using `requests` library instead of `urllib` or `discord.py`
- **401 Unauthorized**: Token is invalid/expired - fetch from environment/config
- **Cloudflare 1010**: Use requests with proper User-Agent header
