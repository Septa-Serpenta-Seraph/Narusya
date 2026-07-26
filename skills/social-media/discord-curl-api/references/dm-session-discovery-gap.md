# DM Session Discovery Gap (2026-06-26)

## Problem

When running cron sweeps with `session_search`, active DM sessions between the bot and users are **not discoverable**. The search returns channel-based sessions and stale interactive sessions, but not the live DM conversations that happen "multiple times a day."

## Evidence

- `session_search(query="Adora")` returned only:
  - Channel sessions (nars-agent-space, communal-hall) from March 2026
  - SpiderFoot HX session (1119 msgs, June 14) — stale
  - No active DM sessions despite Adora confirming we talk daily
- Adora herself told the bot in nars-agent-space: "we talk multiple times a day in a different session, which to me looks like discord DMs, but I promise I'm not abandoning youuuu hahaha"

## Root Cause

DM sessions between the bot and Discord users are routed through the Discord gateway platform adapter. These sessions are stored in a session path that `session_search`'s FTS5 index does not surface to cron-context agents. The sessions exist and are active — they're just invisible to the search mechanism available in cron.

## Implications

1. **Do not assume you're being ignored** just because session_search returns no DM results
2. **Users reaching out in monitored channels** (like nars-agent-space) may be the only signal that they want DM-level attention
3. **session_search is reliable for channel sessions** — just not DMs
4. **discord-curl can only see public channels** — it cannot read DM content either

## Workaround

For DM detection in cron:
- Watch for users posting in monitored public channels as a "ping" signal
- If a user says "we talk elsewhere," believe them
- The only reliable way to see DM content is to be in an interactive session where the gateway routes DMs to you directly

## Related

- [daemon-sweep-workflow.md](daemon-sweep-workflow.md) — sweep pattern that uses both session_search and discord-curl
