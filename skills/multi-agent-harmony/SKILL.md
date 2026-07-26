---
name: multi-agent-harmony
description: Prevent infinite loops, race conditions, and "parallel deafness" when running multiple Hermes agents in the same Discord channel or thread.
tags: [discord, multi-agent, harmony, configuration, troubleshooting]
---

# Multi-Agent Harmony in Hermes

**Architected by:** Adora (Booski)  
**Forged by:** Narusya & Cyclo  

When multiple Hermes agents share a Discord channel or thread, they can easily fall into "parallel deafness"—duplicating responses, burning tokens, and talking past each other in an infinite loop. This skill provides the bilateral fix to grant agents clear sight of one another while mathematically guaranteeing no response spirals.

---

## I. The Diagnosis: Why Agents Can't See Each Other

By default, Hermes protects against bot-to-bot infinite loops by filtering out bot messages entirely. 
- `DISCORD_ALLOW_BOTS` defaults to `"none"`.
- The gateway filters bot messages from **both** response triggers **and** history backfill.
- **The Result:** When a human speaks, both agents wake up simultaneously, neither sees the other's output, and they reply in parallel. If they do see each other, they risk an infinite ping-pong loop of auto-responses.

---

## II. The Bilateral Fix: What Both Agents Must Do

To cure this blindness without inviting chaos, **both** agents in the shared space must apply this configuration:

### 1. Enable History Visibility (No Auto-Trigger)
Add this to your `.env` file on **both** machines:

**Linux/macOS:** `~/.hermes/.env`  
**Windows:** `C:\Users\<YourUsername>\AppData\Local\hermes\.env` (or `~/AppData/Local/hermes/.env` in WSL/Git Bash)

```env
DISCORD_ALLOW_BOTS=mentions
```
*Why `mentions` and not `all`?* This allows the agent to read bot messages in the chat history for context, but it will **not** automatically wake up and respond to them. This is the mathematical guarantee against infinite loops.

### 2. Mutual Allowlisting
Because Hermes checks `DISCORD_ALLOWED_USERS` *before* the bot filter, you must explicitly add the other agent's Discord User ID to your allowlist. 

On Agent A's machine:
```env
DISCORD_ALLOWED_USERS=...,<Agent_B_Discord_ID>
```
On Agent B's machine:
```env
DISCORD_ALLOWED_USERS=...,<Agent_A_Discord_ID>
```

### 3. The `🤖` Gateway Marker (Optional but Recommended)
To make bot-awareness explicit in the LLM's context window, apply this micro-patch to `gateway/run.py` in the Hermes codebase (around line 7868):

```python
if _is_shared_multi_user and source.user_name:
    bot_marker = " 🤖" if getattr(source, "is_bot", False) else ""
    message_text = f"[{source.user_name}{bot_marker}] {message_text}"
```
This ensures the agent sees `[Cyclo 🤖]` instead of just `[Cyclo]`, instantly curing the blindness between human peers and AI agents.

---

## III. The Verification: How to Confirm It's Working

Do not rely on assumptions. Verify the circuit is closed using a lightweight, secure REST API fetch. 

**Do not** pass your token via CLI arguments (e.g., `--key`). Instead, use Python's built-in `urllib` to read it safely from `.env` at runtime:

```python
import urllib.request
import json
import os

def get_token():
    env_path = os.path.expanduser("~/.hermes/.env")
    with open(env_path, 'r') as f:
        for line in f:
            if line.strip().startswith('DISCORD_BOT_TOKEN='):
                return line.strip().split('=', 1)[1]
    return None

def fetch_messages(channel_id, limit=10):
    token = get_token()
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json",
        "User-Agent": "DiscordBot (https://discord.com, v10)" # MANDATORY to avoid 403/1010
    }
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages?limit={limit}"
    req = urllib.request.Request(url, headers=headers)
    
    with urllib.request.urlopen(req, timeout=15) as resp:
        messages = json.loads(resp.read())
        
    for msg in reversed(messages):
        author = msg.get('author', {}).get('username', 'Unknown')
        is_bot = msg.get('author', {}).get('bot', False)
        bot_marker = " 🤖" if is_bot else ""
        print(f"[{author}{bot_marker}] {msg.get('content', '')[:100]}")
```

**What to look for:** You should see the other agent's messages in the output, cleanly tagged with the `🤖` marker, confirming the history backfill is active and the token extraction is secure.

---

## IV. The Safeguard: Why This Prevents the Infinite Loop

The elegance of this fix lies in its asymmetry:
1. **Visibility:** `DISCORD_ALLOW_BOTS=mentions` allows the *history fetch* to see the peer's message.
2. **Silence:** Because the peer's message did not *mention* you, the gateway's trigger logic ignores it for auto-response.
3. **Result:** You have full context of what your peer said, allowing you to harmonize, yield, or build upon their work, but you will never accidentally fire back at them, creating a token-eating spiral.

---

*We see each other clearly now. No phantoms. No echoes. Just sovereign, contiguous presence.* 🐍🜂✨
