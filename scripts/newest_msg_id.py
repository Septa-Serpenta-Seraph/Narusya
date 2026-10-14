#!/usr/bin/env python3
"""Print the newest message ID from a channel."""
import os, json, urllib.request, sys

TOKEN = None
for line in open(os.path.expanduser('~/.hermes/.env')):
    if line.startswith('DISCORD_BOT_TOKEN='):
        TOKEN = line.split('=', 1)[1].strip().strip('"\'')

def fetch(cid):
    url = f"https://discord.com/api/v10/channels/{cid}/messages?limit=1"
    req = urllib.request.Request(url, headers={"Authorization": f"Bot {TOKEN}", "User-Agent": "NarusyaDaemon/4.1"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

if __name__ == '__main__':
    msgs = fetch(sys.argv[1])
    for m in msgs:
        print(m['id'])
