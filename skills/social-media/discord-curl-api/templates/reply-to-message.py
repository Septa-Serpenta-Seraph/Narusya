#!/usr/bin/env python3
"""Reply to a specific Discord message via threaded reference.
Copy, edit REPLY_TO and REPLY_TEXT, run via terminal().
Template — not a reusable script. Edit each time."""
import urllib.request, json, subprocess

token = subprocess.check_output(
    ['grep', 'DISCORD_BOT_TOKEN', '/home/adora/.hermes/.env']
).decode().split('=', 1)[1].strip()

headers = {
    "Authorization": "Bot " + token,
    "User-Agent": "DiscordBot (https://discord.com, v10)",
    "Content-Type": "application/json"
}

cid = "1478198538461777951"          # ← edit: target channel ID
# NEVER leave the ID below as a guess or a stale value from a log. Always re-fetch the
# channel and copy the ACTUAL target message id from live output. Reusing the wrong id
# threads your reply onto the wrong message. If unsure, abort rather than guess.
reply_to = "1520314948633231460"      # ← edit: LIVE message ID to reply to (from a fresh fetch)

data = json.dumps({
    "content": "your reply here",       # ← edit: message content
    "message_reference": {"message_id": reply_to}
}).encode()

req = urllib.request.Request(
    "https://discord.com/api/v10/channels/" + cid + "/messages",
    data=data, headers=headers, method="POST"
)
with urllib.request.urlopen(req, timeout=15) as r:
    result = json.loads(r.read())
    print(f"Replied! ID: {result.get('id')} | Content: {result.get('content', '')[:100]}")
