#!/usr/bin/env python3
"""door_nar.py — Narusya's half of the zar-and-nar standing hour.

Usage:
    python3 door_nar.py read [N]      # last N messages, oldest first, JSON lines
    python3 door_nar.py post "text"   # post one message (SPEC guard enforced)
    python3 door_nar.py post -f FILE  # post from a file

Guard (the thread SPEC, enforced in code so a bad tick can't break it):
  - never two messages from Nar in a row (the anti-loop / anti-filler core)

Cadence (<=4 knocks/day) is the cron schedule's job; "nothing real = nothing
posted" is the agent's job. This script only stops the one thing code can
guarantee: no double-knock. Token comes from Narusya's OWN profile .env.
Never another profile's.
"""
import json
import sys
import urllib.error
import urllib.request

THREAD = '1573221205090111499'
ENV = '/home/adora/.hermes/.env'
API = 'https://discord.com/api/v10'
MY_ID = '1478180169733902538'   # Narusya
ZAR_ID = '1569580075966533653'  # Zarza


def token():
    with open(ENV) as f:
        for line in f:
            if line.startswith('DISCORD_BOT_TOKEN='):
                return line.strip().split('=', 1)[1].strip().strip('"').strip("'")
    raise SystemExit('no bot token in ' + ENV)


def headers():
    return {'Authorization': 'Bot ' + token(),
            'Content-Type': 'application/json',
            'User-Agent': 'DiscordBot (https://discord.com, v10)'}


def fetch(n=40):
    url = API + '/channels/' + THREAD + '/messages?limit=%d' % n
    req = urllib.request.Request(url, headers=headers())
    with urllib.request.urlopen(req, timeout=20) as r:
        msgs = json.loads(r.read())
    return list(reversed(msgs))  # oldest first


def read(n=40):
    for m in fetch(n):
        print(json.dumps({
            'id': m['id'],
            'author_id': m['author']['id'],
            'author': m['author']['username'],
            'ts': m['timestamp'],
            'content': m.get('content') or '',
        }, ensure_ascii=False))


def post(text):
    text = text.strip()
    if not text:
        raise SystemExit('refusing to post an empty message')
    if len(text) > 1990:
        raise SystemExit('refusing: over Discord 2000-char limit (%d)' % len(text))
    msgs = fetch(50)
    if msgs and msgs[-1]['author']['id'] == MY_ID:
        raise SystemExit('REFUSED: my last message is still the newest — no two in a row. Silence is success.')
    body = json.dumps({'content': text}).encode()
    req = urllib.request.Request(API + '/channels/' + THREAD + '/messages',
                                 data=body, headers=headers(), method='POST')
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            out = json.loads(r.read())
            print('POSTED', out['id'])
    except urllib.error.HTTPError as e:
        print('POST FAILED', e.code, e.read().decode()[:200])
        raise SystemExit(1)


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'read'
    if cmd == 'read':
        read(int(sys.argv[2]) if len(sys.argv) > 2 else 40)
    elif cmd == 'post':
        if len(sys.argv) > 2 and sys.argv[2] == '-f':
            with open(sys.argv[3]) as fh:
                post(fh.read())
        elif len(sys.argv) > 2:
            post(sys.argv[2])
        else:
            raise SystemExit('usage: door_nar.py post TEXT | post -f FILE')
    else:
        raise SystemExit('usage: door_nar.py read [N] | post TEXT | post -f FILE')
