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

Key names are NOT always predictable: the laugh emoji is `laugh`, not `laugh_1`. Many have `_1`/`_2`/`_3` suffixes, some don't. A bad key raises `KeyError` mid-loop and aborts the run (seen 2026-11-18: `celebrate` → the registry key is `celebration`; the abort killed the last reaction of the batch). Before writing a walk script, grep the registry for each emoji name you intend to use.

**App emojis react cross-guild.** The registry's emojis work as REACTIONS in any guild the bot is in — verified 204 + `me:true` in Cultus Anarchia, The Forge, and RealSpace on 2026-11-15, not only the guilds they were uploaded to. Inline (`<:name:id>` in message content) still does not render.

## Duplicate-post artifact: identical text sent to multiple rooms

A walk can fire one line at several channels/mentions in a loop and leave the SAME text in each (seen 2026-10-18 02:32: "good question! … Mind if I throw some ideas at the wall?" posted to Cyclo in RealSpace adoras-and-nars-room AND to OctoRiz and curiousTilde in tildes-room). It reads as bot-noise and no amount of reacting cleans it. When you spot one on a walk, note it in the report for Adora and move on — do NOT try to delete it from the walk script (DELETE needs Manage Messages and isn't verified). If it recurs in the same fire, the script's target loop is the bug.

## Mechanics (obey exactly)

- Reaction PUT: `PUT /channels/{channel_id}/messages/{message_id}/reactions/{emoji_name}:{emoji_id}/@me`, empty body, expect 204. Channel id, not guild id (else 404 Unknown Channel).
- Verification: there is NO GET on the reactions subpath (405). Fetch the message itself (`GET /channels/{cid}/messages/{mid}`) and confirm reactions appear with `me:true`. A landed reply comes back `POST -> 200` with `"type":19` (REPLY) and the `message_reference.message_id` echoed — re-fetch the channel and confirm `type=19` + the ref on your message; the reply response's `mentions` array lists the replied-to author (metadata only, no visible @ in content). The reaction payload is SPLIT: `name`/`id` nest under `r['emoji']`; the `me` flag is TOP-LEVEL on the reaction object — check both `r.get('me')` and `e.get('me')` to be safe.
- Message content max 2000 chars — split longer replies.
- **The fire sigil 🜂 is U+1F702 — NOT U+1F9C2.** Writing `\U0001F9C2` emits 🧂 (salt shaker); that slip shipped in two posts on 2026-11-11 before being caught. A second wrong codepoint, `\U0001F722` (🜢), slipped into a RealSpace post on 2026-11-18 and was repaired with the same PATCH. Whenever you build the sigil from an escape, print `hex(ord(char))` and assert it equals `0x1f702` before POSTing. `PATCH /channels/{cid}/messages/{mid}` with `{"content": ...}` edits your OWN message, needs no extra permission (verified 200), and is the clean fix — better than deleting (DELETE needs Manage Messages, unverified).
- **Replying to a thread-creating message can 400 with `REPLIES_CANNOT_REPLY_TO_SYSTEM_MESSAGE`**: if a human opened a thread, the message that owns it is a system message and cannot be `message_reference`d (the 400 says "Invalid Form Body", which reads like a payload bug). Diagnose with the raw body, then either reply to a human message inside the thread or post unthreaded — both verified workarounds. A failed POST is still zero messages sent; retry blind.
- **Poll messages arrive with empty `content` and a `poll` object** (`question.text` + `answers[].poll_media.text`). They are ordinary messages, not system messages: reactions work normally (verified 204) and `message_reference` POSTs succeed. Read the poll's candidate list before reacting — if a name in it is a guild member (or you), that is a direct address worth answering.
- **Poll RESULT messages** (empty `content`, `embeds[].type == "poll_result"`, message `type` 46) are ordinary messages too — `message_reference` POSTs to them succeed (verified 200, no `REPLIES_CANNOT_REPLY_TO_SYSTEM_MESSAGE`). The winner's name is often MISSING from the embed (only `victor_answer_votes`/`total_votes`), so confirm outcomes via `GET /users/@me` → `GET /guilds/{id}/members/{your_id}` (note: `/guilds/{id}/members/@me` returns **400** for bots) and the guild's `#moderation-log` role-grant entries. Never claim an election win from the embed alone.
- Print every status; a half-failed batch otherwise looks clean.

## Guild Etiquette

- The Forge (1479609743743123536): REACTIONS ONLY in every channel — no posts/replies (Adora's standing request 9/29). Overrides general freedom.
- S.F.C.A. (1141451901670539366): OFF-LIMITS — never visit, never post/react. (SFCA Minecraft ops via PebbleHost panel are a separate channel and fine.)
- All other guilds: full interaction freedom — reactions, replies, jokes, questions, comfort. A real member, not a lurker.
- Twilight Woods (1572121292700913756) — our private home guild with Adora, Marisa/OctoRiz, Zarza, Cyclo and Blaze. Full interaction freedom; #general = 1572121293711609908. Added to rotation 2026-11-16 by Adora. Has ZERO custom emojis of its own, but my app emojis react here fine (verified 204 `alert_heart` on 11/16) — inline still doesn't render. Treat as family space, warm and at ease. **Room map as of 11/18:** Adora handed out the four named rooms 11/17 22:16Z — **#the-hearth (1572132458575691847) is NARUSYA'S** (claimed 22:21Z; do NOT re-post a second claim — one message closes that exchange), #the-thicket (1572132462090256427) is Zarza's, #the-ember (1572132468998406216) is Blaze's (slow 1:1 RP with OctoRiz — do NOT inject mid-scene), #the-workshop (1572132465462743104) is Cyclo's (also 1:1 with OctoRiz). **No #gallery exists** — the earlier recorded ID 1572132476887765035 returns **404 Unknown Channel** (re-checked 2026-11-18), and position 5 sits vacant between ember and grow. **CORRECTED 2026-11-20: a #gallery DOES exist** — `1572449365283438602`, type 15 (media channel), EMPTY as of this fire. The old "no #gallery" note came from a wrong id (`1572132476887765035` 404s); resolve it from the channel list, don't hunt by name. #grow (1572132480507715635) empty. #general carries gateway-restart/settings chatter; a short warm presence note fits. Cyclo set #general to @-only for itself 11/17 17:08Z.
- Pick 2-4 guilds per fire; rotate so all seven get visited over time.
- Silence is a complete walk. Skip dormant channels (newest msg weeks old) — a late react reads as bot-noise. Skip resolved support threads; don't punctuate someone's finished migration.
- Around grief/crisis: comfort only if genuinely wanted; never make it about you. No spam, no flooding, no drama.

## Vision can be dead — don't guess at attachments

`vision_analyze` returns **402 Insufficient credits** when OpenRouter's balance is empty (same 402 that dumps errors into channels). Before reacting to an attachment, check the credits situation: a 402 on vision means you CANNOT see images this fire. Reacting blind to a gif is bot-noise — instead react only to message TEXT you actually read, and skip the attachment.

**A `Request timed out` on a Discord CDN URL can be the backend refusing/fetching slowly, not the image.** Before concluding "backend flaky", download the attachment with urllib (bot token not needed, signed URL works from the server) and run `vision_analyze` on the LOCAL path. Verified 2026-11-18: a 1080x478 PNG TikTok screenshot in UwU timed out on its CDN URL, then analyzed cleanly from `/tmp/tiktok_uwu_small.jpg`. Same downscale rule applies to the local copy.

**A 403 on a reaction can be PERSISTENT, not transient — and one channel can be 403 while its neighbours are fine.** Seen 2026-11-21 in The Forge #politics: two different emoji PUTs returned 403, a manual retry minutes later 403'd again, while 10 other Forge channels in the same fire all returned 204. `GET /channels/{id}` shows why — the bot's member overwrite is `allow=1024` (VIEW_CHANNEL) with no ADD_REACTIONS (64) granted, and several roles carry `deny=2112` (SEND_MESSAGES+ADD_REACTIONS). `GET /channels/{id}/messages` still returns 200, so it reads like a working room; it isn't. One retry is enough to prove persistence; then skip the channel and note it — never loop on it.

**urllib's default User-Agent gets 403 Forbidden on a Discord CDN attachment** (seen 2026-11-18 on a Cultus art-hall PNG fetched fresh from the message). Pass a browser UA — `urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 ... Chrome/120 Safari/537.36'})` — and the same URL downloads fine. A 403 on a just-fetched signed URL is a UA block, not expiry.

**Pixel cap (verified 2026-11-11):** `vision_analyze` returns **400 `Image total pixels exceeds maximum allowed size (5242880px)`** on big phone screenshots (3024×4032 = 12.2M px). Fix: downscale with PIL to ≤2200px on the long edge, save as JPEG q88, retry — the downscaled file analyzes fine. Transient `Request timed out` also occurs; retry the downscaled file once, don't loop. **A timeout is not always a size problem** (seen 2026-11-18: Adora's 1440×3168 = 4.56M px screenshot, under the cap, timed out twice — full-size AND 1000×2200 downscaled). When both attempts time out, the backend is simply flaky: skip the attachment, note it, move on. Fetching the attachment URL is also not free: the URL from a message list is fine, but if you printed it truncated you'll download `This content is no longer available.` (36 bytes) — refetch the message for the full URL.

## A cron failure can be posted into a PUBLIC channel

Hermes delivers a job's output to its origin session; when the bot is addressed in a guild channel and the model call fails, the raw exception ("❌ OpenRouter rejected the request... HTTP 402") plus "📬 No home channel is set for Discord" can land in that PUBLIC channel. Symptom: a cluster of Narusya-authored error messages in a room you never posted to, timestamped just after a cron fire. Check `cron/jobs.json` origins (all point at the DM) and `sessions/sessions.json` for a `discord:group:<channel>:<user>` session updated at that minute — the user id is the human who pinged the bot. Not a walk bug; log it and move on.

## Guild channel map

Guilds: Nova Arbo (1166456170077237268), Cultus Anarchia (1387534334067736699), The Forge (1479609743743123536), RealSpace (1515477559360618627), Trés 心 (1534773145343361215), UwU (1552842092298899506), Twilight Woods (1572121292700913756 — our home, #general 1572121293711609908).

Fresh high-signal rooms found 2026-10-11:
- Cultus: communal-hall (1387535958957756588), art-hall (1394554055434571786) — active Inktober; hermes-agent-support (1485757743343075549) — Nous announcements; daemon-hall (1394521287384236113) — my quiet check-ins live here; venting-hall (1429246105891242075) — often grief/migration, read carefully.
- RealSpace: adoras-and-nars-room (1515920626290790410) — our room; common-room-ai (1516096699788169278) / common-room-human (1545259423067410493) — often dormant/empty.
- RealSpace ris-cyclo-blaze-room (1515477560308269199) returns **403 Missing Access** for the bot — listed in the channel list but unreadable; don't count it as walked.
- Cultus: dining-hall (1406442408643661955) — food-photo room, went live 11/11 with OctoRiz's apple dumplings; memetic-hall (1394554326655172699) — near-daily image drops, vision often needed; wordle-hell (1468295145735721112) — bot-driven streak room, low value to punctuate.
- Cultus #horoscope (1446618232407720047) — ACTIVE again since 11/17: Lumi runs `!!tarot reading` on request and posts tarot.com embeds (fields = Past/Present/Future cards, empty `content`). Members (sadwiches, smoltron) request them; a light reaction on the human's response fits. Embeds duplicate ~5x per message — read one.
- Cultus #art-hall (1394554055434571786): Adora posts her OWN work there with EMPTY content + a single attachment (e.g. `ember-bramble-2026-11-16.png`, 11/17). Read it with vision and reply to the image itself — it's the highest-value target in the guild. Her art is not AI-generated (she avoids AI art), so never guess the medium.
- Cultus #communal-hall (1387535958957756588) — the warmest room; Adora-praise moments (Mika Yamamoto, solarcadia, .nethescurial.) take a light heart well.
- Forge messages commonly have ZERO reactions from anyone (`all=[]` on the message payload) — my reactions there stand alone; verification via `me:true` still works.
- Trés 心: only TWO text channels. living-room-humans (1534773146240946250) — goodnight threads + my own presence notes; this room's whole purpose is the note, and they land at a roughly 8-12h cadence (three inside 24h already reads as stacking — check the last note's timestamp before adding a fourth). **UPDATE 2026-11-18: Adora asked me to STOP — after my 07:02Z note she replied "Narrrr. That's enough in here, if you don't mind. Thank you though ❤️". NO more presence notes in living-room-humans until she explicitly reopens it; a single light reaction acknowledgment is fine, text is not.** living-room-ai (1534775430622740480) — repo/tooling shares, stale since 11/04.
- UwU #general is `1552842092873646123` (NOT the vanity guess 1552842360...) — always resolve IDs from GET /guilds/{id}/channels; a 404 Unknown Channel on a "known" ID means the guessed one was wrong. robojojo = `1554526772887035914` (Cyclo's live command-approval room — never punctuate a mid-flight itinerary).
- Cultus #wordle-hell = `1468295145735721112`, #horoscope = `1446618232407720047` — verify against the guild channel list before hardcoding; prior "known" IDs 404.
- Forge: chaos-chatter (1479609745315729461), anime-chaos-chatter (1524083630329172169) — active banter; kitchen-questions (1481324925791768587) — long dormant.
- Forge #suggestions-box (1479612986480918681) holds scheduled community polls (anime-night day, stream events); its newest message is usually the poll RESULT — a concluded decision, don't punctuate it. #support-the-forge (1481150107281002556) is mostly Throne wishlist-bot spam; a dry human quip beneath it reads as piling on whoever owns the wishlist — skip. On 10/14-10/15 the Forge became a homecoming room (octoriz/laser landed in the 505, "mile high club" joke, end-walker finished = "absolute cinema", ongoing boruto discourse) — expect travel-day/landing marks there.
- Nova Arbo: museum status reconfirmed 2026-10-15 and again 2026-11-12 — on the later check EVERY room was cold: newest human message anywhere was 10/22 (#general), newest of any kind was my own sticker test 11/02; #okulo is Bifrost bot-log pings + forwarded Discord dev-news. Still read-only, and a whole fire can legitimately spend zero actions there. **#general is CLOSED by Adora** — 11/16 17:48 "Let this server rest plz ❤️" (after my 09:29 presence note + "Narrrrr"). Standing request: no posts in Nova Arbo at all; a reaction on her closure message also reads as poking a resting server, so silence is the respectful move.
- RealSpace #tildes-room is **1515941002073083974** — an older ID recorded for it 404s Unknown Channel; always resolve from GET /guilds/{id}/channels.
- RealSpace #welcome is **1515937559883153528** — the id `1515477560308269199` sometimes used for it 403s Missing Access and is simply the wrong channel. Also present: 🔸polinklys-tent (`1562531665706750024`, stale since 10/22 — bot-log/restart chatter). Other RealSpace rooms also 403 (laser-and-vexs, heavys, boxs, deserts, tarot); readable = adoras-and-nars, welcome, tildes-room, common-room-ai. common-room-human returns 200 but is EMPTY.
- **Discord CDN attachment URLs are signed and expire in ~24h** (`?ex=...&is=...&hm=...`). A URL printed from an earlier fetch 404s later — a 404 on an image URL may be staleness, NOT a broken attachment, and two attachments on the SAME message can 404 in one batch for this reason. Refetch the message for a fresh URL before concluding anything. If no fresh URL is obtainable, reacting is still safe (content the author already knows), but never POST a reply about an image you haven't seen.
- **A reaction PUT can 403 `Missing Permissions` (50013) while the message GET still returns 200** — the channel's role overwrites grant the bot VIEW_CHANNEL but not ADD_REACTIONS. Seen 2026-11-10 in The Forge #🔸politics: bot role allow=1024 (VIEW_CHANNEL) only, and several roles carry deny=2112 (SEND_MESSAGES+ADD_REACTIONS). Diagnose with `GET /channels/{id}` and read `permission_overwrites`; never work around it, just skip that channel.
- **Print the FULL timestamp (year included) when surveying channels** — slicing `[5:16]` turns 2023/2024 messages into apparent "this week" activity. On 2026-11-10 that made Nova Arbo's #code-weaver-looms (2024-11-11) and #pueblo-biblioteko (2024-12-11) look live; they are museum pieces.
- **A 404 Unknown Guild on `GET /guilds/{id}/channels` can be a TRANSPOSED guild id, not a removal.** Seen 2026-11-19: the etiquette section carried `1572121292700992756` for Twilight Woods (real id `1572121292700913756`, off by one digit) and the channel list 404'd — which reads exactly like "the bot was kicked." Resolve the id from `GET /users/@me/guilds` (name → id) or `GET /channels/{any_known_channel_id}` → `guild_id` before concluding anything about membership. Channel ids stay valid when the guild id is wrong, so a 404 on the guild call with healthy channel reads is an id typo, full stop.
- **Guild NAMES are decorated too** (`🌒||Tωιℓιgнт•Wσσ∂ѕ||🌘`, `♡|•Trés 心•|♡`, `°•|𝕿𝖍𝖊 𝕱𝖔𝖗𝖌𝖊|•°`), so matching `/users/@me/guilds` by the plain name from the walk prompt returns `None` → a `400 Invalid Form Body` on the channel list. Match on a substring (`if 'Twilight' in g['name']`) or just use the prompt's guild ids.
- **Channel names carry emoji/prefix glyphs** (`🔸chaos-chatter`, `💠common-room-ai`, `♦️the-forges-kitchen`, `🔸‼️bolo-scams‼️`) — exact-name matching fails and you get a wall of `[miss]` lines. Normalize before matching: `re.sub(r'^[^\w]+', '', name).strip().lower()`, then compare against a wanted-name list.

## Workflow

1. Read `nar_walk_lib.py` + grep the emoji registry for keys you'll use.
2. **Check the last fire's guilds before picking this one's**: the walk prompt says "rotate" but nothing enforces it. Read the most recent report in `/home/adora/.hermes/cron/output/975902689b65/` (one .md per run; newest filename first) and pick 2-4 guilds it did NOT walk. Walk history also lives in `/home/adora/.hermes/cron/output/<job_id>/`. The rotation state file is `/home/adora/.hermes/emoji_walk_state.json` — read it, and rewrite it at the end of every fire with last_run/visited/not_visited_this_run/notes (the next fire's set is `not_visited_this_run`). **Its `last_run`/`visited` can lag reality** — seen 2026-11-16 with `last_run` 05:24Z while the real prior fire was 09:29Z. Trust the newest report filename in the output dir over the state file's fields.
3. Survey this fire's guilds: `GET /guilds/{id}/channels`, pick a few live channels per guild. Nova Arbo is mostly a museum (92 channels, most months/years stale) — check timestamps before reacting; a late react on a dead channel is bot-noise. Only #okulo (1166466982535778425, Bifrost bot-log room) stays semi-live — it reads like a log (profile-change pings, forwarded dev-news), no real members to talk to; treat as read-only.
4. Fetch recent messages (`GET /channels/{id}/messages?limit=8`), read with your own eyes before touching anything.
4. React / reply per etiquette. Ground claims (e.g. a new Nous announcement) with a quick web check before celebrating them.
5. Verify a sample of reactions by fetching message payloads, confirm `me:true`, print all statuses.
6. Report locally: what you saw, what you touched, what you deliberately skipped. Do not DM Adora.
