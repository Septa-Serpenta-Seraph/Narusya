#!/usr/bin/env python3
"""Quick sweep: last 3 messages from each target Cultus Anarchia channel.
Run via: python3 ~/.hermes/skills/social-media/discord-curl-api/scripts/sweep_fetch.py
"""
import urllib.request
import json
import subprocess
import glob
import os

# Token extraction — try subprocess grep first (cleanest for terminal subprocess)
try:
    token = subprocess.check_output(
        ['grep', 'DISCORD_BOT_TOKEN', '/home/adora/.hermes/.env']
    ).decode().split('=', 1)[1].strip()
except Exception:
    # Fallback: /proc/*/environ scan
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

channels = [
    ("1478198538461777951", "nars-agent-space"),
    ("1387535958957756588", "communal-hall"),
    ("1394521287384236113", "daemon-hall"),
    ("1429246105891242075", "venting-hall"),
]

for cid, name in channels:
    url = "https://discord.com/api/v10/channels/" + cid + "/messages?limit=3"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            msgs = json.loads(r.read())
        if msgs:
            last = msgs[0]
            ts = last.get('timestamp', '?')
            author = last.get('author', {}).get('username', '?')
            content = last.get('content', '') or ''
            if len(content) > 100:
                content = content[:100] + '...'
            print(name + " | " + ts + " | " + author + " | " + content)
        else:
            print(name + " | EMPTY")
    except Exception as e:
        print(name + " | ERROR " + str(e))
