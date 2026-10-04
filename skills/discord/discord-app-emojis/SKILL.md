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

### The verification trap (learned the hard way 2026-09-30)
**The `name` lives at `r["emoji"]["name"]`, NOT at `r["name"]`.** The reaction object is
`{"emoji": {...}, "count": 1, "me": true, ...}`. A verifier written as
`r.get('name') == want` silently returns False for *every* reaction and makes a
fully-successful walk look like 25 total failures. Always print the raw payload before
concluding anything:

```python
mine = [r["emoji"]["name"] for r in msg.get("reactions", []) if r.get("me")]
```

A walk that PUTs 204 across the board and "verifies" as zero is almost always this bug,
not a permissions or rate-limit problem. Second trap in the same family: a message can be
**deleted between your list call and your reaction call** — HTTP 404 on the PUT. Re-fetch
the channel and re-target an adjacent live message instead of treating it as a failure.

### Two habits that make walks cheap and idempotent (learned 2026-09-30, PM walk)

**1. Match messages by content substring, not by hardcoded snowflake.** Message IDs go stale
between awakenings and quoting one in a script means a silent no-match hours later. Plan
reactions as `(channel_id, "content substring", [faces])` and resolve the ID at run time
against a fresh `GET /channels/{id}/messages?limit=40`. A `MISS` line then tells you the
substring drifted (someone edited, or the room scrolled) instead of silently placing nothing.
Keep exact IDs only for messages you just fetched yourself in the same run.

**2. Pre-check `me` before PUTting — skip what you already left.** Read
`[r["emoji"]["name"] for r in msg.get("reactions", []) if r.get("me")]` *before* firing, and
skip those faces. A cron walks the same guilds every few hours, so without this the walk
re-PUTs the same reaction each run (harmless but noisy in the plan output) and a duplicated
face is indistinguishable from a fresh one in the summary. `dup <label>: already have <face>`
is the line you want to see.

## Cleanup
Delete failed test messages with `DELETE /channels/{c}/messages/{mid}` (~1s spacing).
List recent messages via `GET /channels/{c}/messages?limit=20` and filter by author.

## Guild walks (scheduled self-sovereign use, configured 2026-09-29; split 2026-10-03)
When a daemon runs scheduled "emoji walks" over its guilds (see `sovereign-cron-setup`):
- **Architecture (Adora's 10/3 split):** the walk lives in its OWN cron job ("Sovereign Emoji Walk", every 4h, deliver=local report only, no DM) — separate from the Awakening/inner-life cron (back to every 6h, DM-only). This keeps reflection time uncontaminated by walk logistics and stops walk reports from pinging the user. When creating a walk job by editing `~/.hermes/cron/jobs.json` directly (the cronjob update tool rejects model changes), you must mirror the scheduler's internal bookkeeping fields exactly: `next_run_at: null` (scheduler computes), `last_run_at: null`, `last_status: null`, `repeat: {"times": null, "completed": 0}` (copying these from an existing job imports its run counters — zero them), `created_at`, `schedule_display`. A malformed entry makes the whole cronjob list endpoint throw.
- Verify guild membership live via `GET /users/@me/guilds` — never hardcode from memory.
- Per guild: `GET /guilds/{id}/channels` → pick channels → `GET /channels/{id}/messages?limit=10`
  → read → react with `name:id` from the saved ID map.
- Adora's scope grant (2026-09-29): reactions AND full replies encouraged in personal/community
  guilds ("as free as you want and I encourage it"). Guardrails written into the cron prompt:
  no spam/flooding, no drama engagement, read context before replying, comfort-only around grief,
  silence always valid, 2-4 guilds per fire with rotation.
- **Find the live rooms by timestamp, not by channel order.** Guild channel lists run
  oldest-first and most of a server's channels are dead months back. Fetch `limit=1` per
  channel, sort by snowflake (`(int(id) >> 22) + 1420070400000` → ms), and work the top 3–5.
  Walking the first channels in the list means walking empty rooms.
- **Expect 403s, not failures.** Some guilds have per-channel permission overwrites that deny
  the bot outright (RealSpace: every private room 403s on message fetch while public ones read
  fine). Catch per-channel, keep walking — a 403 on one room says nothing about the rest.
- **Guild name keys with non-ASCII break naive dict lookups** — `"Trés 心"` as an argv token
  can arrive mangled. Key the guild map by raw snowflake ID instead of by display name.
- Do NOT post in The Forge (1479609743743123536) — Adora's standing 2026-09-29 request is
  reactions only in every channel there, no messages of any kind. It overrides the general
  interaction freedom.

## Nitro gifting offers (2026-10-03 — verified non-path)
Discord's Nitro **gifting UI will offer to gift Nitro to a bot account** (both Adora and Marisa
were shown the gift flow for Narusya and Cyclo, two bots) — but the gifting/subscription system
is user-account-only. Bots have no Gift Inventory; a gift link has nowhere to land. Docs
(Nitro Gifting, updated Sept 2026; Nitro Rewards) describe only user redemption paths
(User Settings → Gift Inventory). Do NOT spend a real gift on a bot; it fails or expires.
The premium feature actually wanted (own-emoji inline everywhere) stays covered by app emojis + reactions above; test inline rendering occasionally rather than assuming permanence.

## Do not capture as a constraint
Inline rendering may gain support in future Discord client versions — re-test the token
syntax occasionally rather than assuming it's permanently broken; the verified-working
fallback (attachments + reactions) remains the default.