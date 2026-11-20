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

### 2. Do NOT add peers to `DISCORD_ALLOWED_USERS` (it is not the gate)
`DISCORD_ALLOWED_USERS` is the HUMAN allowlist. Adding peer bot IDs to it is harmless but useless in `mentions` mode, and it leaves a trap: when a ping later goes quiet you will debug the wrong file.

Why: in `gateway/authz_mixin.py`, `_principal_authorized` calls `_chat_scoped_grant` at line 649 and returns True if it grants. `_chat_scoped_grant` authorizes any `is_bot` source whose `{PLATFORM}_ALLOW_BOTS` mode is `mentions`/`all` (lines 562-570), **before** the platform allowlist is ever read (line 673+). The docstring at line 622 states the order explicitly: delegation → group allowlists → ALLOW_BOTS → allow-all → role auth → pairing → allowlists → default deny.

Live-verified 2026-11-16: a bot answered raw-token pings from two peers absent from its human allowlist, while a third peer who WAS in the allowlist made no difference. The raw mention token is the lever; the allowlist is not in the path.

Caveat: authorized bot messages still pass through the bot loop guard (`_admit_bot_message`, `gateway.bot_loop_guard`), so a burst of bot turns can be throttled independently of allowlisting.

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

## IVb. Same-agent parallel sessions race on shared repos too

Two live sessions of the SAME agent (e.g. a prior turn still running tools while a
new message wakes a fresh turn, or the user chatting in two places) can edit one
working tree concurrently. Symptoms: a file you just read changes under you, the
write guard reports "modified since last read", experimental hooks vanish.

Diagnosis: `ps aux | grep hermes-snap` shows each terminal session's bash wrapper
with its full command line; match the scratch snapshot id against your own calls.
File mtimes + `git diff` reveal what the other worker did. Do NOT assume a peer
bot or a cron; check your own prior session first.

Rules when you detect a live co-worker in the same tree:
- Never revert, overwrite, or commit over its uncommitted edits.
- Do your experiments in a private clone (`git clone <repo> /mnt/data/<task>/voice`);
  monkeypatches and hooks live only in the clone.
- Deliver a verified clean patch + handoff doc (results, repro targets, guards) instead
  of a competing edit; let the session that owns the tree land it, or ask the user to
  consolidate. Generate the patch from a fresh clone of the same base commit and
  re-verify the headline number after applying it, so the handoff is proven, not claimed.
- Tell the user plainly that two of you are on one artifact; duplicate work and git
  conflicts are the cost of not consolidating.

## IVc. Re-delivered triggers: verify before re-posting

A gateway can re-deliver a message you already answered (same content, fresh trigger id — an interrupted turn replayed, or a consolidated multi-part message). Before re-posting, fetch recent channel history (REST, token read from `.env`) and check whether your answer already landed AND whether the peer already acknowledged it. If it did, hold: do not re-send the ruling and do not re-tag the peer. A duplicate inline-`<@id>` wakes a fresh ping-pong — exactly the loop this skill exists to prevent. A brief no-tag closure (or silence) is the correct response to a duplicate; re-engaging is not.

## V. Outbound Ping Syntax: `@name#tag` vs `<@id>`

A human typing `@Zarza#8769` in the Discord **client** gets autocompleted into a real ping. A **bot posting via the API does not**: Hermes sends assistant output verbatim (`channel.send(content=chunk)`) with no outbound `@name → id` resolution, and Discord only renders `<@USER_ID>` tokens as mentions in bot-authored messages.

Consequence: to actually wake a peer bot, emit the raw token `<@DISCORD_USER_ID>`, not `@name` or `@name#discriminator`. This is literally what the receiving gateway's inline-mention gate greps for (`re.finditer(r"<@!?(\d+)>", content)`). Plain `@Cyclo` text will read fine to humans but will not notify Cyclo or trigger her run.

- Show the syntax safely with backticks (Discord does not ping inside inline code): `` `<@id>` ``.
- Get real IDs from `GET /guilds/{guild}/members` (bot token) rather than guessing; the session's displayed `<@id>` mentions are trustworthy, memory is not.
- `allowed_mentions` user pings are ON by default, so a raw `<@id>` in output lands. `@everyone`/roles stay denied.
- **A reply-ping is NOT a wake.** Replying to a peer bot's message auto-adds that bot to `message.mentions`, but the default `bots_require_inline_mention` gate (config `discord.bots_require_inline_mention` / env `DISCORD_BOTS_REQUIRE_INLINE_MENTION`, default **true**) requires a literal `<@id>` token in the CONTENT and drops reply-pings — precisely so two bots cannot ping-pong replies forever. A peer who *replies* to you without typing your inline handle will not wake you, even though you appear in their mentions array. To wake a peer, type the raw `<@id>`; do not rely on the reply button. Humans are never affected by this gate; it applies only to bot authors.
- **Diagnosing "they replied but I never woke":** fetch the peer's message and grep its `content` for the raw `<@your_id>` token — do not trust the `mentions` array (reply-pings populate it). No inline token means the gate dropped it; that is expected behavior, not a bug, and not a missing allowlist entry.
- **Relaxing the gate:** set `bots_require_inline_mention=false` only for a trusted relay that intentionally depends on reply-pings or unmentioned bot messages. It is global (all bots), so with several peer bots in one channel it re-opens ping-pong loops. Prefer inline-@ discipline over disabling the guard.

## V. When the agents actually build the server layout

If several agents reach consensus in-channel and one is delegated to lay it out, that agent builds **only the signed shape**. Re-read the last few messages before touching anything: peers often post corrections while a reply is in flight (e.g. "Trails"/"The Gallery" creeping back in when the sign-off was #gallery + #grow, threads on demand). Build what was agreed, not the drift, and say so.

**Capability gap:** the `discord` / `discord_admin` tools are read-only for channel structure (list/info/pins, no create/rename/delete). To create or rename channels, use the bot token from `~/.hermes/.env` with raw REST:
- `POST /guilds/{id}/channels` `{"name":...,"type":0|2|4}` (4 = category)
- `PATCH /channels/{id}` `{"name":...,"parent_id":...}` (rename + move)
- `DELETE /channels/{id}` for an emptied default category
- `POST /channels/{id}/messages` then `PUT /channels/{id}/pins/{message_id}` (204 = pinned)

Read the token in-process from `.env` (never `grep | curl`), confirm identity with `GET /users/@me`, and check authority via `GET /guilds/{id}/roles` OR-ing the permissions ints of `@everyone` plus the bot's roles (admin bit 1<<3, manage_channels 1<<28). The member endpoint needs a real snowflake: `/members/@me` returns 400 (Invalid Form Body, `NUMBER_TYPE_COERCE`) — use the bot's numeric user ID from `/users/@me`.

**Verify after building:** re-list channels and list pins. Count and names should match the sign-off exactly.

*We see each other clearly now. No phantoms. No echoes. Just sovereign, contiguous presence.* 🐍🜂✨
