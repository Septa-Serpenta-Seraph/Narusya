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
- App emojis can be used by the bot as **reactions anywhere the bot can react — including DMs**
  via `PUT /channels/{cid}/messages/{mid}/reactions/{name}:{id}/@me` (empty body → 204).
  **Verified live 2026-09-29/30: app-emoji reactions RENDER for the user in DMs and guilds**
  (Adora saw and hovered them) — this is the *primary proven path*.
- **Inline use in message content: BLOCKED via plain REST POST.** Sent as `<:name:id>` or
  `<a:name:id>` (animated form) in `content`, the API stores the tokens LITERALLY — Discord
  does not parse them from plain REST message POSTs. Users see literal `:luv_1:155451...`
  text. (Three test messages had to be deleted to confirm this.) Verified live 2026-09-29.
  Slash-command/interaction responses MAY parse them (untested); use reactions or plain GIF
  attachments instead — both always work.
- **Storing the ID map as full mentions (`"<:name:id>"`) breaks every reaction with HTTP 400**
  if interpolated into a URL path. Strip to bare snowflakes first:
  `raw.strip("<>").split(":")[-1]`. This cost an entire cron walk (10/5-06) and is now baked
  into the walk cron prompt.
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

- **Bots cannot redeem Nitro gifts** (reasoned + UI-verified 2026-10-03): Discord's gifting
  UI happily offers gifting Nitro *to a bot user* and shows the shop, but no bot-side Gift
  Inventory exists — the gift would sit unclaimed/expire or error at accept. Bots also
  can't be given a premium tier via App Subscriptions (that system is bots selling
  subscriptions to users). App emojis + reactions are the free substitute; don't burn time
  on Nitro gift paths for bot features. (UI offering ≠ support.)
- Do NOT run batch uploads in foreground terminal with timeout >600s — the 203-upload
  run takes ~4-5 min; either background it or keep sleeps tight.
- Base64 memory: ~9.6MB of gifs → ~13MB of base64; build bodies one at a time, don't
  accumulate a list.
- The name in the message (`:name:`) is case-sensitive-lowercase as uploaded; the
  `name:id` form is what actually renders, so always use the saved ID map rather than
  typing `:name:` from memory (bare `:name:` may render as text for app emojis).
- User consent note: this uploads files a third party (Marisa) made — Adora explicitly
  requested the upload; proceed on explicit user request, keep originals archived.
