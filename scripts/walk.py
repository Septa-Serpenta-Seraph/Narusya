#!/usr/bin/env python3
"""Light observational walk — one guild, recent messages, check own reactions."""
import os, json, urllib.request, urllib.parse, sys, datetime

TOKEN = None
for line in open(os.path.expanduser('~/.hermes/.env')):
    if line.startswith('DISCORD_BOT_TOKEN='):
        TOKEN = line.split('=', 1)[1].strip().strip('"\'')
        break

UA = "NarusyaDaemon/4.1"

def api(method, path, **kw):
    url = f"https://discord.com/api/v10{path}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bot {TOKEN}",
        "User-Agent": UA,
    }, method=method)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read()) if r.length or r.status != 204 else None

def channels(gid):
    return api("GET", f"/guilds/{gid}/channels")

def messages(cid, limit=10):
    return api("GET", f"/channels/{cid}/messages?limit={limit}")

def check_reactions(cid, mid):
    m = api("GET", f"/channels/{cid}/messages/{mid}")
    mine = [r for r in m.get('reactions', []) if r.get('me')]
    return mine

if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'channels':
        for ch in channels(sys.argv[2]):
            if ch['type'] == 0:
                print(f"{ch['id']}  {ch['name']}")
    elif cmd == 'messages':
        for m in messages(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 10):
            ts = datetime.datetime.fromisoformat(m['timestamp']).strftime('%m-%d %H:%M')
            who = m['author']['username']
            txt = m['content'][:300] if m['content'] else '(embed/attach)'
            print(f"[{ts}] {who}: {txt}")
    elif cmd == 'reactions':
        mine = check_reactions(sys.argv[2], sys.argv[3])
        for r in mine:
            print(f"  me reacted: {r['emoji']['name']} ({r['emoji']['id']}) count={r['count']}")
