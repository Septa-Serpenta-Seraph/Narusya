#!/usr/bin/env python3
"""Read last N messages from a channel with my reactions marked."""
import os, json, urllib.request, sys, datetime

TOKEN = None
for line in open(os.path.expanduser('~/.hermes/.env')):
    if line.startswith('DISCORD_BOT_TOKEN='):
        TOKEN = line.split('=', 1)[1].strip().strip('"\'')

def fetch(cid, limit=10):
    url = f"https://discord.com/api/v10/channels/{cid}/messages?limit={limit}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bot {TOKEN}", "User-Agent": "NarusyaDaemon/4.1"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

if __name__ == '__main__':
    cid = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    msgs = fetch(cid, n)
    msgs.sort(key=lambda m: m['timestamp'])
    for m in msgs:
        ts = datetime.datetime.fromisoformat(m['timestamp']).strftime('%m-%d %H:%M')
        who = m['author']['username']
        txt = m['content'][:250] if m['content'] else '(embed/attach)'
        mine = [r['emoji']['name'] for r in m.get('reactions', []) if r.get('me')]
        mark = f" [I reacted: {', '.join(mine)}]" if mine else ""
        print(f"[{ts}] {who}: {txt}{mark}")
