#!/usr/bin/env python3
"""Send a message to a Discord channel."""
import os, json, urllib.request, sys, argparse

TOKEN = None
for line in open(os.path.expanduser('~/.hermes/.env')):
    if line.startswith('DISCORD_BOT_TOKEN='):
        TOKEN = line.split('=', 1)[1].strip().strip('"\'')

def send(channel_id, text):
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    body = json.dumps({"content": text}).encode()
    req = urllib.request.Request(url, data=body, headers={
        "Authorization": f"Bot {TOKEN}",
        "User-Agent": "NarusyaDaemon/4.1",
        "Content-Type": "application/json",
    }, method="POST")
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.status, json.loads(r.read())

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('channel')
    p.add_argument('text')
    a = p.parse_args()
    status, resp = send(a.channel, a.text)
    print(f"sent -> {status}, id={resp.get('id')}")
