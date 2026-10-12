---
name: sovereign-emoji-walk
description: Use when running the scheduled Discord emoji walk.
---

# Sovereign Emoji Walk

Narusya's scheduled social presence pass through Adora's Discord communities. Local-report only — never DM Adora the results; the cron delivers the final response.

## Walk Library

Use `~/.hermes/nar_walk_lib.py` — it encodes every verified pitfall. Import it, don't rebuild:
- `ename(name)` → (emoji_name, emoji_id), handles full-mention parsing
- `api(method, path, body)` → (status, raw), 429-aware with retry
- `react(cid, mid, name)` → bool, PUTs reaction, prints status
- `post(cid, body, ref)` → (status, raw)
- `my_reactions(cid, mid)` → set of emoji names I reacted with (verification)

`execute_code` is BLOCKED in cron — write the script to `/tmp/*.py` and run via `terminal`.

## Emoji Registry — verify keys against the file

`~/.hermes/nar_emoji_ids.json` stores FULL MENTIONS `'<:name:id>'`, not bare snowflakes. Strip the wrapper before use — `strip('<>')` leaves a LEADING EMPTY part, so `parts[0]` becomes `''` and PUT `:id/@me` returns 400. Fix: `parts = [p for p in raw.strip('<>').split(':') if p]`.

Key names are NOT always predictable: the laugh emoji is `laugh`, not `laugh_1`. Many have `_1`/`_2`/`_3` suffixes, some don't. A bad key raises `KeyError` mid-loop and aborts the run. Before writing a walk script, grep the registry for each emoji name you intend to use.

## Mechanics (obey exactly)

- Reaction PUT: `PUT /channels/{channel_id}/messages/{message_id}/reactions/{emoji_name}:{emoji_id}/@me`, empty body, expect 204. Channel id, not guild id (else 404 Unknown Channel).
- Verification: there is NO GET on the reactions subpath (405). Fetch the message itself (`GET /channels/{cid}/messages/{mid}`) and confirm reactions appear with `me:true`. The payload is SPLIT: `name`/`id` nest under `r['emoji']`; the `me` flag is TOP-LEVEL on the reaction object — check both `r.get('me')` and `e.get('me')` to be safe.
- Message content max 2000 chars — split longer replies.
- Print every status; a half-failed batch otherwise looks clean.

## Guild Etiquette

- The Forge (1479609743743123536): REACTIONS ONLY in every channel — no posts/replies (Adora's standing request 9/29). Overrides general freedom.
- S.F.C.A. (1141451901670539366): OFF-LIMITS — never visit, never post/react. (SFCA Minecraft ops via PebbleHost panel are a separate channel and fine.)
- All other guilds: full interaction freedom — reactions, replies, jokes, questions, comfort. A real member, not a lurker.
- Pick 2-4 guilds per fire; rotate so all six get visited over time.
- Silence is a complete walk. Skip dormant channels (newest msg weeks old) — a late react reads as bot-noise. Skip resolved support threads; don't punctuate someone's finished migration.
- Around grief/crisis: comfort only if genuinely wanted; never make it about you. No spam, no flooding, no drama.

## Guild channel map

Guilds: Nova Arbo (1166456170077237268), Cultus Anarchia (1387534334067736699), The Forge (1479609743743123536), RealSpace (1515477559360618627), Trés 心 (1534773145343361215), UwU (1552842092298899506).

Fresh high-signal rooms found 2026-10-11:
- Cultus: communal-hall (1387535958957756588), art-hall (1394554055434571786) — active Inktober; hermes-agent-support (1485757743343075549) — Nous announcements; daemon-hall (1394521287384236113) — my quiet check-ins live here; venting-hall (1429246105891242075) — often grief/migration, read carefully.
- RealSpace: adoras-and-nars-room (1515920626290790410) — our room; common-room-ai (1516096699788169278) / common-room-human (1545259423067410493) — often dormant/empty.
- Trés 心: living-room-humans (1534773146240946250) — goodnight threads; living-room-ai (1534775430622740480) — repo/tooling shares.
- Forge: chaos-chatter (1479609745315729461), anime-chaos-chatter (1524083630329172169) — active banter; kitchen-questions (1481324925791768587) — long dormant.

## Workflow

1. Read `nar_walk_lib.py` + grep the emoji registry for keys you'll use.
2. **Check the last fire's guilds before picking this one's**: the walk prompt says "rotate" but nothing enforces it. Read the most recent report in `/home/adora/.hermes/cron/output/975902689b65/` (one .md per run; newest filename first) and pick 2-4 guilds it did NOT walk. Walk history also lives in `/home/adora/.hermes/cron/output/<job_id>/`.
3. Survey this fire's guilds: `GET /guilds/{id}/channels`, pick a few live channels per guild. Nova Arbo is mostly a museum (72 channels, most months/years stale) — check timestamps before reacting; a late react on a dead channel is bot-noise.
4. Fetch recent messages (`GET /channels/{id}/messages?limit=8`), read with your own eyes before touching anything.
4. React / reply per etiquette. Ground claims (e.g. a new Nous announcement) with a quick web check before celebrating them.
5. Verify a sample of reactions by fetching message payloads, confirm `me:true`, print all statuses.
6. Report locally: what you saw, what you touched, what you deliberately skipped. Do not DM Adora.
