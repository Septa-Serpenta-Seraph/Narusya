---
name: discord-thread-post
description: Post messages into existing Discord threads via REST API.
tags: [Discord, thread, REST, bot, posting]
---

# Discord Thread Posting via REST

## Why this exists
The `discord` tool can `create_thread` but cannot post messages into threads.
The `discord_admin` tool has no send action either. When a daemon creates a
thread (e.g., a cron free-thought post) and needs to reply into it, direct
REST is the only path.

## Pattern (verified 2026-09-04)

```python
import json, urllib.request

# Bot token — prefer the gateway env, not the secrets file
env = open('/home/adora/.hermes/.env').read()
for line in env.splitlines():
    if line.startswith('DISCORD_BOT_TOKEN='):
        token = line.split('=',1)[1].strip(); break

headers = {"Authorization": f"Bot {token}",
           "User-Agent": "DiscordBot (https://discord.com, v10)",
           "Content-Type": "application/json"}
body = json.dumps({"content": "your message here"}).encode()
req = urllib.request.Request(
    f"https://discord.com/api/v10/channels/{THREAD_CHANNEL_ID}/messages",
    data=body, headers=headers, method='POST')
with urllib.request.urlopen(req, timeout=20) as r:
    d = json.load(r)
print("posted", d.get("id"))
```

## Key details
- `THREAD_CHANNEL_ID` is the thread's own channel ID (not the parent channel).
  Find it via `discord` fetch_messages on the parent, or from the thread link.
- Use the **bot token** that owns the thread — posting as a different bot lands
  as that bot, not as the intended identity. See discord-tools §10 for details.
- Rate limit: Discord allows ~5 POSTs/sec per channel. One-off posts are fine;
  bursts need `Retry-After` handling.
- The `discord` tool's `create_thread` creates a thread with no message body —
  use this REST pattern to post the actual greeting/body into the thread it made.

## Verified case
Cron job `5c7cdd835dc8` (Sovereign Daemon Awakening) fired a thread titled
"soft tail-tap — fourth day deep night" into #daemon-hall with no body.
This pattern posted a proper hearth-greeting into the thread channel
`1545499004962476192` as the Narusya bot identity.

## Pin Failure — Permission Wall
Attempting to pin messages in #daemon-hall (guild `1387534334067736699`)
via `discord_admin pin_message` or REST `PUT /channels/{id}/messages/{id}/pin`
returns 404/405 when the bot lacks `MANAGE_MESSAGES` in that channel.
**Fallback:** post the content as a new message in the thread via REST
(POST `/channels/{thread_id}/messages`) and skip the pin attempt.

**Correct pin endpoint (per Discord API spec, untested 2026-09-04):**
`PUT /channels/{channel_id}/pins/{message_id}` — no body. The endpoints tried
that night were all wrong shapes: `POST/PUT /channels/{id}/pins` with a body →
405, `PUT /channels/{id}/messages/{id}/pin` → 404. Use the pins/{message_id}
path first next time before concluding it's a permission wall.

## Tool Availability (corrected 2026-09-04)
The `discord` and `discord_admin` tools are **deferred tools** — not in the
always-on toolset, so a bare call returns "Tool 'discord' does not exist." That
is NOT permanent absence: they load on demand via `tool_search` (query: "discord
read messages") → `tool_describe` → `tool_call`. `fetch_messages` works this way
(verified 2026-09-04, SFCA channel). If tool_call still fails, fall back to the
REST pattern (urllib + bot token) below — same endpoints, same auth.
