#!/usr/bin/env python3
"""React to a message — Narusya's tail-tap."""
import os, json, urllib.request, urllib.parse, sys

TOKEN = None
for line in open(os.path.expanduser('~/.hermes/.env')):
    if line.startswith('DISCORD_BOT_TOKEN='):
        TOKEN = line.split('=', 1)[1].strip().strip('"\'')

def eid(name):
    """Parse emoji ID from nar_emoji_ids.json (handles <:name:id> format)."""
    raw = EMO[name].strip()
    return raw.strip('<>').split(':')[-1] if raw.startswith('<') else raw

EMO = json.load(open(os.path.expanduser('~/.hermes/nar_emoji_ids.json')))

if __name__ == '__main__':
    channel_id = sys.argv[1]
    message_id = sys.argv[2]
    emoji = sys.argv[3]
    eid_str = eid(emoji)
    url = (f"https://discord.com/api/v10/channels/{channel_id}/messages/"
           f"{message_id}/reactions/{emoji}:{eid_str}/@me")
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bot {TOKEN}",
        "User-Agent": "NarusyaDaemon/4.1",
    }, method="PUT", data=b"")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            print(f"{emoji} -> {r.status}")
    except Exception as e:
        print(f"{emoji} failed: {e}")
