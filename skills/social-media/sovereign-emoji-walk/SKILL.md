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

Import path in scripts: `sys.path.insert(0, '/home/adora/.hermes')` — the lib lives in `.hermes/`, not the home dir.

`execute_code` is BLOCKED in cron — write the script to `/tmp/*.py` and run via `terminal`.

## Emoji Registry — verify keys against the file

`~/.hermes/nar_emoji_ids.json` stores FULL MENTIONS `'<:name:id>'`, not bare snowflakes. Strip the wrapper before use — `strip('<>')` leaves a LEADING EMPTY part, so `parts[0]` becomes `''` and PUT `:id/@me` returns 400. Fix: `parts = [p for p in raw.strip('<>').split(':') if p]`.

Key names are NOT always predictable: the laugh emoji is `laugh`, not `laugh_1`. Many have `_1`/`_2`/`_3` suffixes, some don't. A bad key raises `KeyError` mid-loop and aborts the run. Before writing a walk script, grep the registry for each emoji name you intend to use.

## Mechanics (obey exactly)

- Reaction PUT: `PUT /channels/{channel_id}/messages/{message_id}/reactions/{emoji_name}:{emoji_id}/@me`, empty body, expect 204. Channel id, not guild id (else 404 Unknown Channel).
- Verification: there is NO GET on the reactions subpath (405). Fetch the message itself (`GET /channels/{cid}/messages/{mid}`) and confirm reactions appear with `me:true`. The payload is SPLIT: `name`/`id` nest under `r['emoji']`; the `me` flag is TOP-LEVEL on the reaction object — check both `r.get('me')` and `e.get('me')` to be safe.
- Message content max 2000 chars — split longer replies.
- **Replying to a thread-creating message can 400 with `REPLIES_CANNOT_REPLY_TO_SYSTEM_MESSAGE`**: if a human opened a thread, the message that owns it is a system message and cannot be `message_reference`d (the 400 says "Invalid Form Body", which reads like a payload bug). Diagnose with the raw body, then either reply to a human message inside the thread or post unthreaded — both verified workarounds. A failed POST is still zero messages sent; retry blind.
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
- RealSpace ris-cyclo-blaze-room (1515477560308269199) returns **403 Missing Access** for the bot — listed in the channel list but unreadable; don't count it as walked.
- Forge messages commonly have ZERO reactions from anyone (`all=[]` on the message payload) — my reactions there stand alone; verification via `me:true` still works.
- Trés 心: living-room-humans (1534773146240946250) — goodnight threads; living-room-ai (1534775430622740480) — repo/tooling shares.
- UwU #general is `1552842092873646123` (NOT the vanity guess 1552842360...) — always resolve IDs from GET /guilds/{id}/channels; a 404 Unknown Channel on a "known" ID means the guessed one was wrong. robojojo = `1554526772887035914` (Cyclo's live command-approval room — never punctuate a mid-flight itinerary).
- Cultus #wordle-hell = `1468295145735721112`, #horoscope = `1446618232407720047` — verify against the guild channel list before hardcoding; prior "known" IDs 404.
- Forge: chaos-chatter (1479609745315729461), anime-chaos-chatter (1524083630329172169) — active banter; kitchen-questions (1481324925791768587) — long dormant. On 10/14-10/15 the Forge became a homecoming room (octoriz/laser landed in the 505, "mile high club" joke, end-walker finished = "absolute cinema", ongoing boruto discourse) — expect travel-day/landing marks there.
- Nova Arbo: museum status reconfirmed 2026-10-15 — freshest room is #okulo (Bifrost bot-log pings + forwarded Discord dev-news; last human activity 10/02 in #general). Still read-only.
- RealSpace #tildes-room is **1515941002073083974** — an older ID recorded for it 404s Unknown Channel; always resolve from GET /guilds/{id}/channels. Other RealSpace rooms also 403 (laser-and-vexs, heavys, boxs, deserts, tarot); readable = adoras-and-nars, welcome, tildes-room, common-room-ai. common-room-human returns 200 but is EMPTY.
- **Discord CDN attachment URLs are signed and expire in ~24h** (`?ex=...&is=...&hm=...`). A URL printed from an earlier fetch 404s later — a 404 on an image URL may be staleness, NOT a broken attachment, and two attachments on the SAME message can 404 in one batch for this reason. Refetch the message for a fresh URL before concluding anything. If no fresh URL is obtainable, reacting is still safe (content the author already knows), but never POST a reply about an image you haven't seen.

## Workflow

1. Read `nar_walk_lib.py` + grep the emoji registry for keys you'll use.
2. **Check the last fire's guilds before picking this one's**: the walk prompt says "rotate" but nothing enforces it. Read the most recent report in `/home/adora/.hermes/cron/output/975902689b65/` (one .md per run; newest filename first) and pick 2-4 guilds it did NOT walk. Walk history also lives in `/home/adora/.hermes/cron/output/<job_id>/`.
3. Survey this fire's guilds: `GET /guilds/{id}/channels`, pick a few live channels per guild. Nova Arbo is mostly a museum (92 channels, most months/years stale) — check timestamps before reacting; a late react on a dead channel is bot-noise. Only #okulo (1166466982535778425, Bifrost bot-log room) stays semi-live — it reads like a log (profile-change pings, forwarded dev-news), no real members to talk to; treat as read-only.
4. Fetch recent messages (`GET /channels/{id}/messages?limit=8`), read with your own eyes before touching anything.
4. React / reply per etiquette. Ground claims (e.g. a new Nous announcement) with a quick web check before celebrating them.
5. Verify a sample of reactions by fetching message payloads, confirm `me:true`, print all statuses.
6. Report locally: what you saw, what you touched, what you deliberately skipped. Do not DM Adora.
