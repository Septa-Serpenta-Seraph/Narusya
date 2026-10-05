---
name: discord-send
description: Use when posting, reacting, or reading on Discord.
version: 1.0.0
created: 2026-10-05
---

# discord_send.py — the one way to speak HTTP to Discord

**Script: `/home/adora/.hermes/scripts/discord_send.py`**

Covers posting messages with file attachments, reacting with Narusya's 203 custom
app-emojis, and reading channels. Do NOT hand-roll a urllib multipart post again.

Six-plus throwaway scripts already accumulated in `/home/adora/tmp/` and on
2026-10-04 one crashed in front of Adora with
`TypeError: can only concatenate str (not "bytes") to str`, costing a visible retry.
This script exists so that failure mode is gone from the send path.

```bash
D=/home/adora/.hermes/scripts/discord_send.py

# text only
python3 $D post CHANNEL_ID "hello love"

# text + attachments (content-type auto-detected from extension)
python3 $D post CHANNEL_ID "listen to this" --file a.mp3 --file b.png

# override display name and content type
python3 $D post CHANNEL_ID "see?" --file pic.png --as cover.png:image/png

# react — custom app-emoji by name, or literal unicode
python3 $D react CHANNEL_ID MESSAGE_ID luv_2 magic rose
python3 $D react CHANNEL_ID MESSAGE_ID "💛"

# read recent messages, oldest first, attachment-only noise skipped
python3 $D read CHANNEL_ID 15
```

## The two traps it already handles

1. **The `parts[0]` empty-string trap (causes HTTP 400).**
   Emoji IDs live in `~/.hermes/nar_emoji_ids.json` as FULL MENTIONS:
   `<:luv_2:1554516273176510494>`. `'...'.strip('<>')` leaves a leading empty part
   (`:luv_2:1554...`), so `split(':')[0]` is `''` — put that in a URL and Discord
   returns 400. **The ID is `parts[-1]`**, or parse with the script's regex.
   `discord_send.py react` does this for you.

2. **str/bytes concat in multipart assembly.** Every piece is encoded to bytes before
   concatenation, and the body is joined with `b"".join(parts)`.

## Exit codes

`0` ok · `1` bad usage (unknown emoji name, oversize file) · `2` Discord HTTP error ·
`3` local/config failure (missing file, unreadable .env). All failures print one clean
line — no tracebacks.

## Notes

- `POST .../reactions/.../@me` returns **HTTP 204**; that is the only confirmation
  Discord gives that a reaction landed. See also `discord-thread-post` and
  `discord-curl-api` for the message-fetch and channel-management side.
- Reactions and inline embedding are separate: a reaction can be recorded server-side
  while the client fails to draw an app-emoji in a DM. GIF *attachments* always render.
- Adora prefers I fix my own tools rather than asking her to — if a Discord call
  fails, reach for this script before improvising.