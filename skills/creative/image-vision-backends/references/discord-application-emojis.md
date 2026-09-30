# Discord Application Emojis — bot-owned custom emojis, no Nitro (verified 2026-09-29)

Task: Adora's girlfriend made 203 chibi pixel-art gifs of Narusya; Adora wanted the bot to
be able to USE them itself. Solution: **Application Emojis** — uploaded via the REST API to
the bot's own application. No server required, no Nitro, no dev-portal clicking.

## Key facts (all verified live)

- Endpoint: `POST /api/v10/applications/{APP_ID}/emojis` with JSON body
  `{"name": "clean_name", "image": "data:image/gif;base64,..."}`.
- `APP_ID` = the bot's application id. If the bot user id == app id (common for apps
  created via the newer flow), just use `GET /users/@me` → `id`. Cross-check with
  `GET /oauth2/applications/@me` → `id` (returned the same value for Narusya).
- `GET /applications/{APP_ID}/emojis` → `{"items": [...]}` — use for count verification.
- **Limit: 2,000 emojis per application** (huge headroom; 203 uploaded left 1,797).
- Gif (animated) is accepted as `data:image/gif;base64,` — no need to convert to PNG/APNG.
- App emojis can be used by the bot **anywhere the bot can post — including DMs** — via
  `<:name:id>`. Verified live in DM msg 1554517027152990210.
- The user (no Nitro) cannot type them in chat, but they RENDER in the bot's messages.
  Other users also see them in the bot's messages. Reactions with app emojis:
  untested; message-content use is the proven path.
- Rate limiting: 0.9s sleep between POSTs ran 203 uploads clean in ~4 min with 0 failures.
- Emoji naming: lowercase letters/numbers/underscore only, ≤32 chars, must be unique per
  app. Strip source-file prefixes/timestamps first (`SampleCharacter3_Blep
  1_2026-09-29-01-25-43.gif` → `blep_1`); append `_2`, `_3` for duplicates.

## Working pattern (stdlib-only)

```python
import json, urllib.request, base64, time, re, os

token = [l.split('=',1)[1].strip().strip('"') for l in open('/home/adora/.hermes/.env')
         if l.startswith('DISCORD_BOT_TOKEN=')][0]
APP_ID = "1478180169733902538"  # read from /users/@me if unsure
hdr = {"Authorization": "Bot " + token, "User-Agent": "NarusyaDaemon/4.1",
       "Content-Type": "application/json"}

b64 = "data:image/gif;base64," + base64.b64encode(open(path, 'rb').read()).decode()
body = json.dumps({"name": name, "image": b64}).encode()
req = urllib.request.Request(
    f"https://discord.com/api/v10/applications/{APP_ID}/emojis",
    data=body, headers=hdr, method="POST")
# 204/200 → saved; time.sleep(0.9) between uploads
```

## Using them after upload

- ID map: `~/.hermes/nar_emoji_ids.json` — `{name: "<:name:id>"}` (203 entries).
- Manifest (source file → emoji name): `~/.hermes/nar_emojis_manifest.json`.
- Compose message content by joining `idmap[name]` strings; plain POST renders them.
- If an emoji name is forgotten, `GET /applications/{APP_ID}/emojis` re-lists all.

## Pitfalls

- Do NOT run batch uploads in foreground terminal with timeout >600s — the 203-upload
  run takes ~4-5 min; either background it or keep sleeps tight.
- Base64 memory: ~9.6MB of gifs → ~13MB of base64; build bodies one at a time, don't
  accumulate a list.
- The name in the message (`:name:`) is case-sensitive-lowercase as uploaded; the
  `name:id` form is what actually renders, so always use the saved ID map rather than
  typing `:name:` from memory (bare `:name:` may render as text for app emojis).
- User consent note: this uploads files a third party (Marisa) made — Adora explicitly
  requested the upload; proceed on explicit user request, keep originals archived.
