# Session reference: PebbleHost SFCA build, 2026-09-24 (all verified live)

## Context
Friends/community server ("SFCA", 6-12 players): Java, Paper, plugins. Purchased PebbleHost 6GB Budget ($6/mo, NA node NA1664), IP 144.217.117.180:25589, server ID 187ab089.

## Decisions that worked
- **Skipped all add-ons** at checkout: Advanced Minecraft Support $10/mo (their team sets up 10 plugins — that's the agent's job), Priority Discord Support $5/mo, Overdrive $7.50/mo (unneeded for small Paper community), port-free IP $5/mo (free subdomain included instead), Advanced DDoS (L3/4 included free). Total: $6.00.
- **Browser automation was broken this session** (harness CDP misconfig, needs gateway restart) — the API path bypassed it entirely and was faster.
- **Plugin sourcing**: Modrinth API gave every jar (CoreProtect-CE-24.1, EssentialsX-2.21.0, GriefPrevention 16.18.5, LuckPerms-Bukkit-5.5.71 — all support 1.21.4; verify with the game_versions filter, don't trust the unfiltered newest). GitHub releases API returned empty asset lists / 404 for all four repos.
- **server.properties delta from default** (friends server): difficulty normal, white-list=true + enforce-whitelist=true, enforce-secure-profile=false, spawn-protection 8 (not 16), view-distance 10, simulation-distance 6, enable-command-block=true, MOTD green/aqua/gold.
- **Backups**: POST /backups worked (258MB world, is_successful true, ~2min). Scheduled 'backup' action rejected (422 invalid); console `pebblehost:backup` = unknown command. Kept a `save-all flush` scheduled task at 4:00 + home-VM cron (Hermes cronjob) hitting the backups API at 4:05 daily, reporting to Discord home channel.
- **Plugin load proof**: after restart, `plugins/` listing shows generated data folders (CoreProtect/, Essentials/, LuckPerms/, GriefPreventionData/) and latest.log shows each `Enabling` line + `Done (21.312s)!`.

## Gotchas encountered
- Cloudflare HTML 403 on default python UA — fix with browser-like User-Agent header.
- `files/contents` 200 response body is the raw file, not JSON (initial JSONDecodeError).
- Upload signed URL needs `?directory=/plugins` appended (fresh URL per file).
- Schedule task POST requires payload + time_offset fields even for command actions.
- `GET schedules/<id>/tasks` → 405; use `GET schedules/<id>` and read relationships.
- User couldn't find the API-keys page in mobile panel UI — direct link `<panel>/account/api` solved it. The `ptlc_` key is separate from panel login password and survives password resets.

## First-join debugging (same evening, verified)
- User's Microsoft display name was "Miss Adora9773" but the real Java username is `missadora` — console `whitelist add` 204'd and logged "That player does not exist" for the display-name variants (tried 3 casings). `https://api.minecraftservices.com/minecraft/profile/lookup/name/MissAdora9773` → 404, `/missadora` → 200 `{"id":"e571636c...","name":"missadora"}` — that's the authoritative check. Reading back whitelist.json confirmed only the correct name landed.
- **Port-wedge incident**: after the 18:00 restart + backup trigger, panel reported running, console `list` worked, but TCP connect to 144.217.117.180:25589 was refused (user got "Connection refused: getsockopt"). mcsrvstat.us confirmed `online: false, ping: connection refused`. A clean `restart` power signal re-bound the port; mcsrvstat then reported online, 1.21.4, 20 slots. Lesson: external port check before inviting the user to join.
- Post-restart the MOTD showed default "A Minecraft Server" in status pings despite an earlier successful properties readback with the custom MOTD — suspect container regeneration; re-check properties after restarts.

## 9/26 addendum (day 3-4, verified)
- **Datapack install (All The Music 1.7 = entire Minecraft OST as lootable discs, by lumfdoesgaming on Modrinth, ARR license):** zip upload via signed URL to `/`, `PUT files/rename` into `world/datapacks/`, restart → `Found new data pack file/AllTheMusic1.7.zip, loading it automatically`, verified via console `datapack list` → `4 data pack(s) enabled: [... file/AllTheMusic1.7.zip (world)]`. Check Modrinth `game_versions` field for exact-version compat before downloading; optional resource pack was a separate ~2GB Google Drive file — skipped, discs work with vanilla textures.
- **CartSpeed 1.0 installed for the railway ( Tyler's request):** staged jar in /plugins WITHOUT restart (Tyler explicitly asked no restarts during peak hours — honor co-admin timing constraints), then restarted when he green-lit. Console `cartspeed global 1.5` → logged `Global minecart speed multiplier set to 1.5`. Author caveat: >2x causes physics glitches; ceiling ~4x. Modrinth API version-filtered download worked; gamerule probes (minecartMaxSpeed etc.) all failed on Paper 26.2 — no native knob, plugin required.
- **Co-admin workflow (Tyler = second Op):** he DMs feature requests and bug reports directly (torch plugin → TorchHeadLight, WorldEdit error reports, rail-speed research, whitelist adds with polite 'pwease'). Relay group decisions as made by consensus. Belt-and-suspenders whitelist adds are harmless when server is open-join. Full plugin stack after day 3: CoreProtect-CE, EssentialsX 2.22, FAWE 2.15.4, GriefPrevention, LuckPerms, TorchHeadLight, CartSpeed.
- Known issue logged (not fixed): FAWE + CoreProtect throws `Net.coreprotect.worldedit.coreprotectlogger` errors during heavy WorldEdit use — logged noise, rollback still works, low priority.

## Handoff state
Whitelist ON but empty — awaiting player usernames to `whitelist add <name>` each. DiscordSRV chat bridge deferred to v2 (needs bot token). Announcement blurb + IP drafted in session.

## 9/25 addendum (day 2, verified)
- Whitelist turned OFF at Adora's request (open-join by IP obscurity) — `whitelist off` console cmd; protection now = GriefPrevention claims + CoreProtect rollback + Op ban power. kitty/thewindwhistler also whitelist-added anyway (belt-and-suspenders, harmless).
- FAWE 2.15.4 (Paper build, Modrinth API `game_versions=["26.2"]`) uploaded (14.9MB, multipart to signed URL from `GET files/upload?directory=/` then `PUT files/rename` into plugins/), restart → clean enable, CoreProtect handshake logged.
- World seed pulled via console `seed` → `Seed: [5787697784011462183]`; world spawn set via `/setworldspawn` (her position read from EssentialsX userdata yml); desert site scouted at -1, 64, -8687.
- Community dynamics: users self-organize in a Discord channel (baeski's blood fountain w/ donation mechanic, FREE Potato Hut, free building-materials chest by fountain, subway entrance + nether portal chamber). The agent's job is infrastructure; the community builds the culture within hours.
- The Pterodactyl `files/upload` endpoint is requested with GET and returns a signed URL that accepts the multipart POST — but note the Hermes `ptero.py` helper's `api()` does NOT take a `params` kwarg; append query strings directly to the path. The final move into /plugins is `PUT files/rename` (no files/upload-to-directory support).
