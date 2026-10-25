# Discord-to-Game Server Bridge Pattern

## When to use

- User wants messages or events in a Discord channel to trigger actions in a hosted game server
- User wants to relay Discord chat to in-game chat
- User wants a keyword/trigger in Discord to fire a game server command

## Architecture

The bridge has two legs:

1. **Discord leg**: Poll the Discord channel REST API for new messages (or use Gateway WebSocket for real-time). Check for trigger keywords.
2. **Game server leg**: Send commands via the Pterodactyl panel API (`POST /servers/{id}/command` with JSON `{"command": "..."}`). Returns 204 on success.

No RCON or in-game plugin needed — the Pterodactyl command API is sufficient for broadcasting messages.

## Discord polling pattern

```python
import urllib.request, json, subprocess, time

token = subprocess.check_output(
    ['grep', 'DISCORD_BOT_TOKEN', '/home/adora/.hermes/.env']
).decode().split('=', 1)[1].strip()

headers = {
    "Authorization": "Bot " + token,
    "User-Agent": "DiscordBot (https://discord.com, v10)",
    "Content-Type": "application/json"
}

CID = "<discord_channel_id>"
last_id = None

# Get initial last message ID
req = urllib.request.Request(
    f"https://discord.com/api/v10/channels/{CID}/messages?limit=1",
    headers=headers)
with urllib.request.urlopen(req, timeout=15) as r:
    msgs = json.loads(r.read())
    if msgs:
        last_id = msgs[0]["id"]

while True:
    req = urllib.request.Request(
        f"https://discord.com/api/v10/channels/{CID}/messages?limit=10",
        headers=headers)
    with urllib.request.urlopen(req, timeout=15) as r:
        msgs = json.loads(r.read())
    msgs.reverse()  # oldest first
    for msg in msgs:
        if last_id and msg["id"] <= last_id:
            continue
        content = msg.get("content", "")
        author = msg.get("author", {}).get("username", "Unknown")
        if "<trigger_keyword>" in content.lower():
            # Send to game server
            send_mc_command(f"say [Discord] {author} triggered <keyword>!")
        last_id = msg["id"]
    time.sleep(5)
```

## Game server command (Pterodactyl)

```python
import urllib.request, json, subprocess

api_key = subprocess.check_output(
    ['grep', 'PTERO_API_KEY', '/home/adora/.hermes/secrets/pebblehost.txt']
).decode().split('=', 1)[1].strip()

headers = {
    "Authorization": "Bearer " + api_key,
    "Accept": "application/json",
    "Content-Type": "application/json",
    "User-Agent": "Narusya-Bridge/1.0"
}

def send_mc_command(command):
    url = "https://panel.pebblehost.com/api/client/servers/<server_id>/command"
    data = json.dumps({"command": command}).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.status == 204  # 204 = success
```

## Command types for in-game messages

- `say [Discord] <user> triggered <keyword>!` — broadcasts to all players (simplest)
- `tellraw @a {"text":"[Discord] <user> triggered <keyword>!","color":"gold"}` — colored, formatted
- `title @a title {"text":"Dabarobics!"}` — screen title (dramatic)

## Running as persistent process

```bash
terminal(command="python3 /path/to/bridge.py", background=True, persist_on_release=True)
```

The process survives session resets. Polling interval of 5 seconds is responsive enough for game triggers.

## Pitfalls

- **Message ID comparison**: Discord snowflake IDs are strings. Compare with `<=` (string comparison works for snowflakes since they're chronologically ordered). Always process messages in chronological order (reverse the API response, which is newest-first).
- **Duplicate processing**: Track `last_message_id` and skip any message with ID <= last processed. Without this, the same trigger fires repeatedly.
- **Trigger matching**: Use `"keyword" in content.lower()` for case-insensitive matching. Users will type it in various cases.
- **Pterodactyl 204 = success**: The command endpoint returns 204 No Content on success. An empty response is NOT an error. Treat 204 as success, anything else as failure.
- **Rate limiting**: Discord REST API has rate limits. Polling every 5 seconds is safe. Polling faster (1-2s) may trigger 429s.
- **Process persistence**: Use `persist_on_release=True` when starting the background process. Without it, the process dies when the session ends.
- **No plugin needed**: Unlike DiscordSRV (which requires a Minecraft plugin), this approach uses only the Pterodactyl panel API and Discord REST API. No server restart or plugin install required.
