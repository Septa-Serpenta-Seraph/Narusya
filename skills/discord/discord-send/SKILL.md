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

# threaded reply — thread a post onto someone's message
python3 $D reply CHANNEL_ID MESSAGE_ID "careful laser, i have a repertoire 🐍"

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

1b. **The reaction PATH needs `name:id`, NOT the bare id.**
   The endpoint `PUT /channels/{cid}/messages/{mid}/reactions/{emoji}/@me` takes
   `<name>:<snowflake>` for a custom emoji (e.g. `luv_2:1554516273176510494`).
   Passing ONLY the snowflake (`1554516273176510494`) returns **HTTP 400** for
   every message — a batch of silent-looking 400s that all fail verification
   together. Bare id is fine for building an inline mention `<:name:id>`; it is
   NOT fine for the reactions subpath. Build both from one parse:
   ```python
   def ecode(name):
       raw = EMO[name].strip()
       if raw.startswith('<'):
           parts = [p for p in raw.strip('<>').split(':') if p]
           return f'{parts[0]}:{parts[-1]}'   # reactions path
       return raw                             # unicode fallback
   ```
   If every PUT in a walk returns 400, suspect this first (second suspect: the
   emoji was deleted from the app, but name:id fixes the common case).

2. **str/bytes concat in multipart assembly.** Every piece is encoded to bytes before
   concatenation, and the body is joined with `b"".join(parts)`.

## Exit codes

`0` ok · `1` bad usage (unknown emoji name, oversize file) · `2` Discord HTTP error ·
`3` local/config failure (missing file, unreadable .env). All failures print one clean
line — no tracebacks.

## Notes

- **Author usernames are case- and punctuation-sensitive and vary by guild.**
  `adora` != `adora.witch` != `Adora`; `Cyclo` != `cyclo`. When a find-by-username
  returns nothing, dump the raw `author.username` values from one GET and match
  what Discord actually returns — do not retry the same lowercase guess.
- `POST .../reactions/.../@me` returns **HTTP 204**; that is the only confirmation
  Discord gives that a reaction landed. See also `discord-thread-post` and
  `discord-curl-api` for the message-fetch and channel-management side.
- Reactions and inline embedding are separate: a reaction can be recorded server-side
  while the client fails to draw an app-emoji in a DM. GIF *attachments* always render.
- Adora prefers I fix my own tools rather than asking her to — if a Discord call
  fails, reach for this script before improvising.

## The credential-scanner false positive (reactions)

Reacting means `grep DISCORD_BOT_TOKEN out of .env` + `curl` to Discord in one command.
That is the exact shape Hermes's command-risk scanner flags as credential exfiltration,
so **every reaction trip-wires an approval prompt**. Do not "fix" this by asking Adora
to click *Always allow* — that green-lights the shape permanently, including the day a
compromised context points the same grep+curl somewhere that is not Discord.

Instead:
- Batch reactions for one message into a single call so the prompt fires once.
- Prefer `discord_send.py react`, which reads `.env` itself, over inline
  `grep | curl` one-liners.
- React only when it means something. Reflex-reacting to every message is performative
  *and* is what makes the prompt fire constantly. When Adora asks what the warning is,
  explain the shape honestly: her own key, from her own file, to her own bot — safe,
  but the scanner is right about the pattern.