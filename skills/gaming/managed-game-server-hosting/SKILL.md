---
name: managed-game-server-hosting
description: "Run Pterodactyl-hosted game servers via the client API."
tags: [pterodactyl, pebblehost, minecraft, hosting, api, paper, plugins, game-server]
platforms: [linux, macos]
---

# Managed Game-Server Hosting via Pterodactyl API

## When to use
- User buys (or asks about) a managed game server on a Pterodactyl-based host — **PebbleHost**, Bisect, Falix, any Pterodactyl panel.
- Setup needed: install server software (Paper/Spigot/modpack), upload plugins, tune server.properties, whitelist, backups, schedules — all possible over HTTP from the terminal, no browser.
- Server diagnostics: power state, RAM/CPU, log tailing, console commands.
- The browser tool is unavailable/unreliable — this path needs no browser at all.

## Prerequisites
1. **API key** from the panel: send the user to `<panel-url>/account/api` → Create API Key (`ptlc_...`, shown once). This page is often missing from the mobile menu — give the direct URL.
2. **Server identifier** (8-char hex): `GET /api/client` with the key, read `attributes.identifier` from the server entry. Also grabs sftp_details and node info.
3. Store key in `~/.hermes/secrets/` (chmod 600), never in chat.

## API quick reference (client API, base `<panel-url>/api/client`)
All requests: `Authorization: Bearer ptlc_...`, `Accept: Application/vnd.pterodactyl.v1+json`, **and a browser-like `User-Agent`** (Cloudflare fronts many panels and 403s default python/curl UAs with an HTML error page — JSON parse errors are the symptom).

- `GET /` — list servers (name, identifier, sftp, limits, node)
- `GET /servers/<id>/resources` — state + memory/cpu/network
- `POST /servers/<id>/power` body `{"signal": "start|stop|restart|kill"}` — returns 204
- `POST /servers/<id>/command` body `{"command": "<console cmd>"}` — whitelist add, say, save-all
- `GET /servers/<id>/files/list?directory=/plugins` — file listing
- `GET /servers/<id>/files/contents?file=%2Fserver.properties` — URL-encoded path, returns raw text (not JSON)
- `POST /servers/<id>/files/write?file=%2Fserver.properties` — raw body = new file content (204)
- `GET /servers/<id>/files/upload` — returns a **signed URL**; POST multipart (`files` field, filename) to it with `?directory=/plugins` appended
- `POST /servers/<id>/backups` `{}` — trigger backup (host limits slots, e.g. PebbleHost 2 manual)
- `GET /servers/<id>/backups` — list, verify `is_successful`
- `POST /servers/<id>/schedules` + `POST /servers/<id>/schedules/<sid>/tasks` — cron-ish tasks; **action field is restricted** (PebbleHost: command/power only — no 'backup' action; payload + time_offset required on task creation)

Use `scripts/ptero-helper.py` — a verified driver wrapping all of this (reads the key from the secrets file).

## Verified workflow: new Minecraft community server (PebbleHost budget)
1. **Plan & buy**: for a friends/community server pick ~1GB RAM per 3-4 players on Paper. Budget tier (~$1/GB) is fine; skip add-ons (support/overdrive/dedicated IP/port-free IP) — the agent IS the support. Free subdomain included post-purchase.2. **Start server** via power API; first boot downloads the container image and generates the world (several minutes, mem ~1.7-1.8GB idle on Paper).
3. **Fetch plugin jars from Modrinth** — NOT GitHub releases (CoreProtect/LuckPerms/EssentialsX assets 404/empty there; CoreProtect moved to Patreon). `GET https://api.modrinth.com/v2/project/<slug>/version?loaders=["paper"]&game_versions=["<ver>"]` (URL-encode brackets/quotes), take `files[0].url`. Community plugin set: coreprotect, luckperms, griefprevention, essentialsx.
4. **Upload jars**: get fresh signed URL per file, multipart POST to `/plugins`. ~7MB total uploads in seconds.
5. **Write server.properties** via files/write: whitelist on (`white-list=true` + `enforce-whitelist=true`), difficulty, view-distance 10 / simulation-distance 6 for small communities, spawn-protection 8, colored MOTD with `\u00a7` codes.
6. **Restart** (power signal) to load plugins; verify via files/contents on `logs/latest.log` — each plugin prints `Enabling <name>` and generates its config folder.
7. **Backups**: no native schedule action on budget hosts — keep (a) a scheduled task running console `save-all flush` daily, and (b) a home-VM cron job calling the backups API daily (start server if stopped, flush, POST backup, verify is_successful). 2 manual backup slots on PebbleHost; oldest overwritten.
8. **Whitelist players**: console commands `whitelist add <name>` once usernames are collected. Server is unjoinable until names are added (whitelist enforced).

## Pitfalls
- Cloudflare UA block (above) — the #1 silent failure; HTML 403 body breaks JSON parsing.
- `files/contents` returns raw file text, not a JSON envelope — handle non-JSON 200s.
- PebbleHost upload signing: append `?directory=/plugins` (or `&` if token param present) to the signed URL before the multipart POST.
- Schedule-task validation wants `payload` and `time_offset` even for command actions; 'backup' as action is rejected on PebbleHost.
- `GET .../schedules/<id>/tasks` is 405 — task listing comes via `GET .../schedules/<id>` relationships instead.
- Panel password resets by the user invalidate nothing API-wise — the `ptlc_` key is independent.
- Restarting a server the host runs is always safe from the agent side (unlike restarting the agent's own gateway).
- **Whitelist needs the REAL Java username** — `whitelist add <name>` returns 204 but logs "That player does not exist" for anything that isn't a live account name. Microsoft-account display names (e.g. "Miss Adora9773") are NOT Minecraft usernames. Resolve first via `https://api.minecraftservices.com/minecraft/profile/lookup/name/<name>` (200 = `{"id","name"}` with canonical casing; 404 = not a real username) or ask the user to screenshot their Minecraft launcher profile. Verify by reading back `whitelist.json` via files/contents — an empty `[]` means the adds silently failed.
- **"Running" in the panel ≠ joinable.** After a restart + backup the server once showed `state: running` with healthy console output while the game port refused TCP connections (player saw "Connection refused"). Verify from OUTSIDE: `bash -c 'echo > /dev/tcp/<ip>/<port>'`, or `https://api.mcsrvstat.us/3/<ip:port>` (third-party status ping, ~5-min cache — `online: false` with `ping: connection refused` is the smoking gun). Fix: clean `restart` power signal re-binds the port. Don't trust panel state alone before telling the user to join.
- Handshake status pings (raw varint protocol) may return 0 bytes even when the port is healthy — use mcsrvstat.us for MOTD/version verification instead of hand-rolled socket pings.
- **Player data answers in-game questions without asking the player.** EssentialsX `userdata/<uuid>.yml` (via files/contents) carries logout-location, homes, and last coords — useful for "where is the player standing" requests (spawn-setting, tp targets) without pinging them in-game. Map player → uuid via the logs (`<Name> logged in` lines or plugins/Essentials/userdata filenames + whitelist.json).
- **Console `seed` beats file forensics for the world seed.** level.dat on modern Paper hosts is a tiny overlay (467B) with no seed inside; `POST .../command {"command":"seed"}` then tail `logs/latest.log` for `Seed: [<n>]` — one call, exact number, ready for Chunkbase/map-viewer lookups. (Manual NBT parsing is only for when console access is broken.)
- **Paper 26.x + EssentialsX**: only 2.22.0 loads on 26.2 — 2.21.0 fails to enable (verified 9/24). Check the newest EssentialsX release before assuming any recent version works.
- **Trust model evolution**: friends/community servers often drop the whitelist entirely (open-join by IP obscurity) — GriefPrevention claims + CoreProtect rollback + Ops with ban power are the real protection. Share the GriefPrevention trust ladder: `/trust` (full build+containers), `/containertrust`, `/accesstrust`, `/trustlist`, `/untrust` — all scoped to the claim you're standing in. `/setworldspawn`, `/spawnpoint`, `/sethome <name>` cover the mobility basics; all work via console or in-game as Op.
- **Pterodactyl upload URL is per-directory, requested with GET**: `GET /servers/<id>/files/upload?directory=%2F` (query param, NOT a JSON body — `api(...,'GET', params=...)` wrappers may not support kwargs, just append the query string). The signed URL is single-use and expires quickly — request it, then multipart-POST immediately (`files` field, browser-like UA + Authorization on the POST too). Verified: 14.9MB FAWE jar uploaded in seconds (9/25). After upload the file lands in the requested directory; move it into `/plugins` with `PUT /files/rename` body `{"root":"/","files":[{"from":"FAWE.jar","to":"plugins/FAWE.jar"}]}` → 204.
- **FAWE (FastAsyncWorldEdit) install for Paper 26.x — use Modrinth, version-filtered:** `GET https://api.modrinth.com/v2/project/fastasyncworldedit/version?game_versions=["26.2"]&loaders=["paper"]` (URL-encode brackets/quotes), take newest `files[0].url`. GitHub releases lack jar assets. Verified 2.15.4 loads clean on Paper 26.2 and CoreProtect logs 'FAWE logging successfully initialized'. Default perms are Op-only — safe on community servers. GriefPrevention trusts do NOT gate WorldEdit; if giving non-Op players FAWE, do it via LuckPerms grants deliberately.
- **Datapacks install as zip uploads to `world/datapacks/` — no plugin juggling:** upload the zip via the standard signed-URL flow to `/`, then move it with `PUT /files/rename` `{"root":"/","files":[{"from":"<zip>.zip","to":"world/datapacks/<zip>.zip"}]}` and restart. Paper auto-loads new datapacks on boot (log line: `Found new data pack file/<name>.zip, loading it automatically`). Verify enabled with console `datapack list` → tail latest.log for `There are N data pack(s) enabled: [... file/<name>.zip (world)]`. Check version compat FIRST via Modrinth API `game_versions` (e.g. Minecraft OST Music Discs by lumfdoesgaming, verified 1.7 = 26.2). Community datapack vetting on the observatory model: check the license (ARR = fine for private friends servers, not for public re-hosting) and note separate optional resource packs (the OST pack's texture pack is a ~2GB Drive download — skip, discs work vanilla-labeled). Verified end-to-end 9/25: AllTheMusic1.7.zip uploaded, moved, restart, auto-loaded, datapack list confirmed.
- **server.properties edits may not survive container restarts on some hosts** — after one restart the MOTD reverted to default "A Minecraft Server" even though the file readback had shown the custom MOTD earlier. Re-read properties after any restart and re-write if the host regenerated them.

## Verification checklist
- [ ] resources endpoint: `state: running`, sane RAM/CPU
- [ ] latest.log shows `Done (Xs)!` and each plugin `Enabling` line
- [ ] plugin data folders exist (CoreProtect/, Essentials/, LuckPerms/, GriefPreventionData/)
- [ ] server.properties readback shows whitelist + MOTD + distances applied
- [ ] a backup exists with `is_successful: true`
- [ ] console command test (`say` or `version`) returns 204
- [ ] give the user the IP:port and an announcement blurb
