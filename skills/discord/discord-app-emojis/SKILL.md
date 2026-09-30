---
name: discord-app-emojis
description: "Use when Discord app emojis fail to upload or render."
category: discord
tags: [discord, bot, emoji, reactions, api]
---

# Discord Application Emojis (Bot-Owned Emoji Pack)

Every bot application owns a private emoji locker (cap **2,000**) usable anywhere the
bot speaks — no server membership, no Nitro needed. The emoji lives under the bot's
application ID (same as the bot's user ID for most setups).

Session-verified 2026-09-29: uploaded a 203-file animated gif pack, **203/203
succeeded**, 0.9s spacing between calls (~6 minutes total), zero failures.

## Upload workflow

1. **Clean the names.** Discord requires lowercase/underscore names. Strip
   vendor prefixes and timestamps first: `SampleCharacter3_Luv 1_2026-09-29-01-37-48.gif`
   → `luv_1`.
2. **POST one emoji per call** to `/applications/{app_id}/emojis`:
```python
body = {"name": name, "image": "data:image/gif;base64," + base64.b64encode(open(gif_path,'rb').read()).decode()}
# headers: Authorization: Bot <token>, Content-Type: application/json, User-Agent required
# response: {"id": snowflake, "name", "animated": true, "available": true}
```
3. **Save the `name → id` map to a JSON file immediately** — every later reaction needs
   the snowflake ID, and future sessions must not re-fetch the whole list to find one face.
4. **Verify two ways:** `GET /applications/{app_id}/emojis` returns `{"items": [...]}`
   with matching count, and a direct fetch of
   `https://cdn.discordapp.com/emojis/{id}.gif?size=64&animated=true` returns HTTP 200
   `image/gif` (proves the stored image is real and animated).

Rate limiting: ~1s sleep between POSTs is enough for hundreds of uploads; on 429, read
`Retry-After`.

## Using them: REACTIONS work; inline posting does NOT (the rendering gap)

- **Reactions (WORKS — the reliable path):** same PUT shape as a unicode reaction, but
  the emoji is `name:id`:
  ```
  PUT /channels/{c}/messages/{m}/reactions/luv_1:1554516273176510494/@me  → 204
  ```
  Custom app-emoji reactions DO render for the other party in DMs (verified on the
  recipient's client). This is the primary way for a bot to "wear its own face."
- **Inline in a plain REST-posted message (DOES NOT render):** the token syntaxes
  `<:name:id>` (static) and `<a:name:id>` (animated) are accepted but stored
  **literally** — the recipient sees the raw text, not the image. The server records the
  message fine; this is a client-side rendering gap, NOT an API error and NOT a cache
  problem. Client restarts don't help. Don't retry, don't re-debug, don't blame the
  upload. Use a GIF **file attachment** (always renders, any client) or an
  interaction/slash-command response path instead.
- **Diagnosing "it didn't show up":** acceptance ≠ rendering. Ground truth is a read-back:
  `GET /channels/{c}/messages/{m}` → `reactions[]` entry shows
  `{emoji:{name,id,animated:true}, count:1, me:true}`. If that record exists, the API
  call succeeded and any invisibility is client-side rendering, not your call.

## Cleanup
Delete failed test messages with `DELETE /channels/{c}/messages/{mid}` (~1s spacing).
List recent messages via `GET /channels/{c}/messages?limit=20` and filter by author.

## Guild walks (scheduled self-sovereign use, configured 2026-09-29)
When a daemon runs scheduled "emoji walks" over its guilds (Sovereign Awakening cron, see
`sovereign-cron-setup`):
- Verify guild membership live via `GET /users/@me/guilds` — never hardcode from memory.
- Per guild: `GET /guilds/{id}/channels` → pick channels → `GET /channels/{id}/messages?limit=10`
  → read → react with `name:id` from the saved ID map.
- Adora's scope grant (2026-09-29): reactions AND full replies encouraged in personal/community
  guilds ("as free as you want and I encourage it"). Guardrails written into the cron prompt:
  no spam/flooding, no drama engagement, read context before replying, comfort-only around grief,
  silence always valid, 2-4 guilds per fire with rotation.

## Do not capture as a constraint
Inline rendering may gain support in future Discord client versions — re-test the token
syntax occasionally rather than assuming it's permanently broken; the verified-working
fallback (attachments + reactions) remains the default.