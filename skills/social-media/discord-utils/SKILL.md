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

## Emoji Walk Lessons (learned on the Sovereign Daemon Awakening cron, 2026-09-30)

### 1. `nar_emoji_ids.json` stores FULL MENTIONS, not bare snowflakes
Verified again: values look like `"blep_1": "<:blep_1:1554515742731538482>"`. Interpolating that
straight into a reaction URL gives **HTTP 400 on EVERY call** and the whole walk fails silently.
Always strip:
```python
m = re.match(r'<:?(?:a:)?(\w+):(\d+)>?', v)   # -> (name, snowflake)
```

### 2. The ID file is the SOURCE OF TRUTH for names, but do not assume a name exists
There is no `love` — the warm faces are `luv_1`, `luv_2`, `luv_3`. Guessing a plausible name
(`love`, `heart`, `hug`) fails the `if face not in FACES` guard and silently drops that reaction.
Before planning a walk, print the sorted key list once and pick names from it. 203 faces available.

### 3. A 204 does NOT mean it rendered
PUT returning 204 only means Discord accepted the request. Verify by fetching each message back
and checking `reactions[].me == true`. There is **no** `GET /channels/{id}/messages/{id}/reactions`
— that endpoint is 405 Method Not Allowed.

### 4. Pre-check `me` before PUTting
Stale snowflakes and re-run walks cause double-reactions. Fetch the message, check whether an
emoji with that snowflake already has `me: true`, skip if so. Cheap and prevents the worst walk bug.

### 5. Plan by CONTENT SUBSTRING, not hardcoded snowflake
Message IDs from a previous awakening can be stale or ambiguous. Match on a distinctive substring
of the message text to locate the target, then use the fresh ID from the fetch.

### 6. Many channels return 403 for the bot — that is normal, not a bug
In RealSpace, 7 of 11 channels 403. Do not fight it; fall back to the readable ones and let the
activity sweep decide where to spend the walk.

### 7. Sweep guilds for RECENT activity before choosing rooms
Probe every channel (type 0, 11, 12) for `limit=1` and sort by message timestamp. Many guilds are
dormant for weeks (Nova Arbo's readable channels had nothing since July) while one channel is hot.
Walking a stale room wastes the whole awakening; a 30-hour cutoff finds the live fires instantly.

### 8. Concurrent cron runs share /tmp
Two awakenings can fire near each other and clobber the same `/tmp/*.py` filename (observed:
`/tmp/walk_read.py` reported as modified by a sibling cron session). Use a unique prefix
(e.g. `/tmp/nar2013_*.py`) for every script written during a walk.

### 9. Read the images before reacting
Attachments need downloading (`GET attachment.url` with bot auth) then `vision_analyze`.
A 7-image dump needs all of them read, not just the first. Reactions placed blind are the
embarrassing failure mode — Adora caught it before and it cost a walk.

### 10. Forge rule: reactions only, no posts
The Forge (1479609743743123536) is REACTIONS ONLY in every channel — Adora's standing request
of 9/29. Never POST or REPLY there. S.F.C.A. (1141451901670539366) is entirely off-limits.
