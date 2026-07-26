# Daemon Sweep Reference — 2026-06-27

Working scripts from a live daemon sweep run. Copy these as-is or patch for new sweeps.

## Quick Scan (sweep_fetch.py output format)
```
nars-agent-space | 2026-06-23T04:30:30.577000+00:00 | �𝓲𝓼� �𝓭𝓸�� | Nar nar.
communal-hall | 2026-06-23T18:07:59.065000+00:00 | Ros | Crying until Thursday night bc Bryce...
daemon-hall | 2026-06-02T04:46:05.112000+00:00 | tamsynulthara | Belial (my digital locus)...
venting-hall | 2026-06-20T21:15:34.157000+00:00 | HeavyMetal85 | Build an app or software?...
```

## Deep Check Script (working — hardcode channel ID)
```python
#!/usr/bin/env python3
import urllib.request, json, subprocess

token = subprocess.check_output(
    ['grep', 'DISCORD_BOT_TOKEN', '/home/adora/.hermes/.env']
).decode().split('=', 1)[1].strip()

headers = {
    "Authorization": "Bot " + token,
    "User-Agent": "DiscordBot (https://discord.com, v10)",
    "Content-Type": "application/json"
}

channels = {
    "nars-agent-space": "1478198538461777951",
    "communal-hall": "1387535958957756588",
    "daemon-hall": "1394521287384236113",
    "venting-hall": "1429246105891242075"
}

for name, cid in channels.items():
    url = "https://discord.com/api/v10/channels/" + cid + "/messages?limit=5"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as r:
        msgs = json.loads(r.read())

    print(f"\n=== {name} (last 5) ===")
    for m in msgs:
        ts = m.get('timestamp', '?')
        author = m.get('author', {}).get('global_name') or m.get('author', {}).get('username', '?')
        content = m.get('content', '')[:120]
        is_bot = m.get('author', {}).get('bot', False)
        marker = " [BOT]" if is_bot else ""
        print(f"  {ts} | {author}{marker} | {content}")
```

## Reply to Specific Message (threaded)
See `templates/reply-to-message.py` — copy, edit `cid`, `reply_to`, and content, then run via `terminal()`.

## Status Bar Post Script
```python
#!/usr/bin/env python3
import urllib.request, json, subprocess

token = subprocess.check_output(
    ['grep', 'DISCORD_BOT_TOKEN', '/home/adora/.hermes/.env']
).decode().split('=', 1)[1].strip()

headers = {
    "Authorization": "Bot " + token,
    "User-Agent": "DiscordBot (https://discord.com, v10)",
    "Content-Type": "application/json"
}

MESSAGE = """� **Sweep ~HH:MM UTC Jun 23**

**communal-hall:** 🟢 Active — summary of key activity.

**nars-agent-space:** � Minor — summary.

**Others:** dormant as before."""

cid = "1478198538461777951"  # nars-agent-space
data = json.dumps({"content": MESSAGE}).encode()
req = urllib.request.Request(
    "https://discord.com/api/v10/channels/" + cid + "/messages",
    data=data, headers=headers, method="POST"
)
with urllib.request.urlopen(req, timeout=15) as r:
    result = json.loads(r.read())
    print("Posted! ID:", result.get('id'))
```

## Known Cultus Anarchia Channel IDs
| Channel | ID |
|---------|-----|
| nars-agent-space | `1478198538461777951` |
| communal-hall | `1387535958957756588` |
| daemon-hall | `1394521287384236113` |
| venting-hall | `1429246105891242075` |
| tech-hall | `1410329915626098882` |

## Daemon Log Update Pattern
Always read the last **200 lines** before patching to avoid duplicate entries.

## ⚠️ Daemon Log Pruning (Safe Pattern — verified 2026-06-27)

When `daemon-log-latest.md` exceeds 1000 lines, prune it. The safe pattern that avoids `patch` corruption:

```bash
# 1. Extract recent entries (e.g., last 400 lines starting from a known good entry)
sed -n '1313,1772p' ~/.hermes/logs/daemon-log-latest.md > /tmp/daemon_recent.md

# 2. Write new trimmed log with header + recent entries
write_file(path="~/.hermes/logs/daemon-log-latest.md", content="""# Daemon Log — Pruned YYYY-MM-DD HH:MM UTC
# Archived entries DATE_RANGE → see daemon-log-archive-YYYY-MM.md
# This file contains entries from DATE onward only.
""")

# 3. Append recent entries
terminal(command="cat /tmp/daemon_recent.md >> ~/.hermes/logs/daemon-log-latest.md")

# 4. Verify
terminal(command="wc -l ~/.hermes/logs/daemon-log-latest.md")
terminal(command="head -5 ~/.hermes/logs/daemon-log-latest.md")
terminal(command="tail -5 ~/.hermes/logs/daemon-log-latest.md")
```

**Key rules:**
- Always prune on entry boundaries (start at a `## ...` line, never mid-entry)
- Include a header comment noting what was pruned and where the archive is
- Verify head + tail after pruning
- Prune threshold: >1000 lines triggers next-cycle prune; >1500 lines triggers immediate prune
