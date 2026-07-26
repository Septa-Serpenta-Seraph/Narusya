#!/usr/bin/env python3
"""
Free Thought Channel Sweep — Quick scan of all target channels.
Fetches last 3 messages from each channel, prints timestamp + author + preview.

Usage: python3 /home/adora/.hermes/sweep_free.py

Requires: DISCORD_BOT_TOKEN in ~/.hermes/.env
"""
import urllib.request, json, subprocess, datetime

token = subprocess.check_output(
    ['grep', 'DISCORD_BOT_TOKEN', '/home/adora/.hermes/.env']
).decode().split('=', 1)[1].strip()

headers = {
    "Authorization": "Bot " + token,
    "User-Agent": "DiscordBot (https://discord.com, v10)",
    "Content-Type": "application/json"
}

# Cultus Anarchia channel IDs
channels = {
    "nars-agent-space": "1478198538461777951",
    "communal-hall": "1387535958957756588",
    "daemon-hall": "1394521287384236113",
    "venting-hall": "1429246105891242075",
    "tech-hall": "1410329915626098882",
}

now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-6)))
print(f"=== Free Thought Sweep — {now.strftime('%Y-%m-%d %H:%M')} ===\n")

for name, cid in channels.items():
    url = "https://discord.com/api/v10/channels/" + cid + "/messages?limit=3"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as r:
            msgs = json.loads(r.read())
        if msgs:
            last = msgs[0]
            ts = last.get('timestamp', 'unknown')
            author_data = last.get('author', {})
            author = author_data.get('global_name') or author_data.get('username', 'unknown')
            content = last.get('content', '')[:120]
            is_bot = author_data.get('bot', False)
            bot_flag = " 🤖" if is_bot else ""
            print(f"📍 {name}")
            print(f"   Last: [{ts}] {author}{bot_flag}: {content}")
        else:
            print(f"📍 {name} — empty/no messages")
    except Exception as e:
        print(f"📍 {name} — ERROR: {e}")
    print()

print("=== Sweep complete ===")
