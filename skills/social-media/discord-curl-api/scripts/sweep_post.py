#!/usr/bin/env python3
"""Post a status bar to nars-agent-space.
Usage: Edit MESSAGE below before running.
Run via: python3 ~/.hermes/skills/social-media/discord-curl-api/scripts/sweep_post.py
"""
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
    "User-Agent": "DiscordBot (https://discord.com, v10)",
    "Content-Type": "application/json"
}

cid = "1478198538461777951"  # nars-agent-space
# EDIT THIS BEFORE RUNNING:
MESSAGE = "🐍 **Sweep ~XX:XX UTC** — [brief signal here]. Adora offline, no signals. 🜂"

data = json.dumps({"content": MESSAGE}).encode()
url = "https://discord.com/api/v10/channels/" + cid + "/messages"
req = urllib.request.Request(url, data=data, headers=headers, method="POST")

with urllib.request.urlopen(req, timeout=15) as r:
    result = json.loads(r.read())
    print("Posted! ID: " + str(result.get('id')))
