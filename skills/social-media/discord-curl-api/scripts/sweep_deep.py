#!/usr/bin/env python3
"""Deep fetch: last 10 messages from a specific channel.
Usage: python3 ~/.hermes/skills/social-media/discord-curl-api/scripts/sweep_deep.py [channel_id]
Default channel: communal-hall (1387535958957756588)
"""
import sys
import urllib.request
import json
import subprocess
import glob

# Token extraction
try:
    token = subprocess.check_output(
        ['grep', 'DISCORD_BOT_TOKEN', '/home/adora/.hermes/.env']
    ).decode().split('=', 1)[1].strip()
except Exception:
    token = None
    for pid_dir in sorted(glob.glob('/proc/*/environ')):
        try:
            with open(pid_dir, 'rb') as f:
                data = f.read().decode('utf-8', errors='replace')
            for var in data.split('\x00'):
                k = var.split('=', 1)
                if len(k) == 2 and k[0] == 'DISCORD_BOT_TOKEN':
                    token = k[1]
                    break
        except Exception:
            pass
        if token:
            break

if not token:
    print("NO_TOKEN")
    exit(1)

headers = {
    "Authorization": "Bot " + token,
    "User-Agent": "DiscordBot (https://discord.com, v10)"
}

# Default: communal-hall
cid = sys.argv[1] if len(sys.argv) > 1 else "1387535958957756588"
url = "https://discord.com/api/v10/channels/" + cid + "/messages?limit=10"
req = urllib.request.Request(url, headers=headers)

with urllib.request.urlopen(req, timeout=15) as r:
    msgs = json.loads(r.read())

for m in reversed(msgs):
    ts = m.get('timestamp', '?')
    author = m.get('author', {}).get('username', '?')
    is_bot = m.get('author', {}).get('bot', False)
    content = m.get('content', '') or ''
    marker = " [BOT]" if is_bot else ""
    preview = content[:200] + ('...' if len(content) > 200 else '')
    print("[" + ts + "] " + author + marker + ": " + preview)
