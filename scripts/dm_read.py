#!/usr/bin/env python3
"""Reusable Discord DM channel reader — one call, clean output for cron."""
import os, json, urllib.request, sys, datetime

TOKEN = None
for line in open(os.path.expanduser('~/.hermes/.env')):
    if line.startswith('DISCORD_BOT_TOKEN='):
        TOKEN = line.split('=', 1)[1].strip().strip('"\'')
        break

def fetch(channel_id, limit=20):
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages?limit={limit}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bot {TOKEN}",
        "User-Agent": "NarusyaDaemon/4.1",
    })
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())

if __name__ == '__main__':
    cid = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    msgs = fetch(cid, n)
    msgs.sort(key=lambda m: m['timestamp'])
    for m in msgs:
        ts = datetime.datetime.fromisoformat(m['timestamp']).strftime('%m-%d %H:%M')
        author = m['author']['username']
        text = m['content'][:400]
        print(f"[{ts}] {author}: {text}")
