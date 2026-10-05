---
name: hosted-game-servers
description: "Administer panel-hosted game servers via Pterodactyl API. Backup 204-success, config-write JSON envelope, live FAWE reload, WorldEdit grant flow."
tags: [gaming, hosting, pterodactyl, minecraft, pebblehost, server-setup]
platforms: [linux]
---

# Hosted Game Server Panel Administration

## When to use
- User bought or wants a game server on a Pterodactyl-based host (PebbleHost, BisectHosting, etc.) and needs it built/configured
- Managing a hosted server: power, files, plugins, whitelist, backups, version upgrades
- Choosing a hosting provider/plan for a community game server
- Panel reports a state that doesn't match reality (says running, port closed)

This skill complements `minecraft-modpack-server` (self-hosted modded servers) — use that one for local/VM installs, this one for panel-hosted. Note: `minecraft-modpack-server`'s Java table predates the 2026 versioning change — this skill's `minecraft-versions-2026.md` reference is the current authority on versions and Java requirements.

## High-level flow
1. **Provider choice:** For friends/community servers (6-15 players, vanilla+plugins): PebbleHost Budget 6GB (~$6/mo) is the value pick; subuser panel access is the community feature to want. DatHost (hourly billing) for zero-commitment trials. Skip hosts' 'support/setup' add-ons when the agent can configure everything itself.
2. **Get API access:** user creates a `ptlc_` client key at `panel.<host>/account/api` (direct URL — mobile menus hide it). Store in `~/.hermes/secrets/`, never in chat.
3. **Drive the panel over HTTPS** — no browser needed. See `references/pterodactyl-client-api.md` for the full endpoint cookbook (auth, power, files, uploads, console, backups, startup variables).
4. **Version right:** 2026 Minecraft uses year-based versioning (26.x) and **requires Java 25**. See `references/minecraft-versions-2026.md`.
5. **Plugins via Modrinth API**, whitelist with real usernames verified against Mojang, automated backups from the agent's own cron (panel schedule actions are limited). See `references/plugin-install-recipe.md` for the end-to-end Modrinth→panel install recipe (worked example: TorchHeadLight, 2026-09-25).
6. **Verify externally:** panel 'running' state ≠ port actually open; check with TCP connect or `api.mcsrvstat.us`.

## References
- `references/pterodactyl-client-api.md` — full endpoint cookbook: auth, power, file read/write, uploads, console commands, backups, startup variables, and request quirks (User-Agent requirement, URL-encoded file paths, PUT vs POST)
- `references/minecraft-versions-2026.md` — the 26.x versioning scheme, Java 25 requirement, Paper download API, world-migration notes, plugin compatibility checks, username vs display-name pitfall
- `references/fawe-coreprotect-troubleshooting.md` — FAWE `CoreProtectLogger` noise during WorldEdit use: diagnosis chain (rotated .log.gz logs), root cause (`extent.debug: true` default), config fix + why NOT to disable CoreProtect's `worldedit: true`
- `references/rail-speed-plugins.md` — minecart/powered-rail speed plugin landscape on Paper 26.2: no native gamerule (probed live), CartSpeed vs hsrails vs dead ends, ~4x physics ceiling, staged-not-installed status

## Datapack install (distinct from plugins — zip goes to /world/datapacks)
Datapacks are NOT plugins: download the zip, upload to panel root, then rename/move it into `world/datapacks/` (Pterodactyl rename API handles dir-creation). Server auto-loads new datapack files **on next boot** — verify via console `datapack list`, expect `[file/<name>.zip (world)]` among enabled. Verified live 2026-09-25: 'All The Music 1.7' OST-discs datapack (917+ music discs, Modrinth `minecraft-ost-music-discs`, 1.2MB zip) loaded automatically on restart with zero config; its optional ~2GB resource pack is a separate Google-Drive download (skippable). Check Modrinth `game_versions` includes the server version AND the zip's `pack.mcmeta` `min_format` fits before uploading.

## Verified plugin pool (2026-09-25, SFCA/Paper 26.2)
- **FAWE (FastAsyncWorldEdit)** (`fastasyncworldedit`) — terraform/world-edit; Paper 2.15.4 build for 26.2, 14.9MB. Boot-verified: `[FastAsyncWorldEdit] Enabling` + `CoreProtect logging successfully initialized` (WE edits become rollbackable). Commands `//`-prefixed (`//wand`, `//set`, `//copy`, `//undo`), Op-only by default.
- **TorchHeadLight 1.1.0** (`torchheadlight`, 13KB) — hold a torch, get dynamic light around you; server-side light data, works for everyone with zero client mods. Lists 26.1.x but runs fine on 26.2 (boot-verified 9/25). Enables with default `height=2.0`.
- **CartSpeed 1.0** (`cartspeed`, 11KB) — minecart speed multipliers: `/cartspeed global <x>`, `/cartspeed nearest <x>`, `/cartspeed reload`; Op-only. 26.2-listed. **Boot-verified 2026-09-26** (loaded during FAWE restart; global multiplier set to 1.5 from console, log line `Global minecart speed multiplier set to 1.5`). Author warns multipliers much above ~2x glitch (Minecraft physics hard ceiling ~4x: more adds momentum, not top speed). See `references/rail-speed-plugins.md` for the full option landscape.

## Common in-game ops (verified live 2026-09-24, SFCA/PebbleHost)
All via POST `/servers/{id}/command` with JSON `{"command": "..."}`; read effect from `/logs/latest.log` contents.
- **Whitelist**: `whitelist add <Name>` / `remove` / `list` / `off` — verify adds in latest.log after a few seconds; after `whitelist off`, confirm with log line `Whitelist is now turned off`
- **Ops**: `op <Name>` — verify in `ops.json` (expect `level: 4`)
- **Seed**: send `seed` command, then grep latest.log for `Seed: [...]` — don't try to parse NBT from level.dat (on 26.x server layouts the root level.dat is a small overlay without WorldGenSettings; NBT parsing is a dead end)
- **Spawn**: player runs `/setworldspawn` (world spawn, everyone) vs `/spawnpoint` (personal respawn); agent-side spawn writes aren't needed — the player command is precise
- **GriefPrevention trust ladder**: `/trust` (full build), `/containertrust` (chests/doors only), `/accesstrust` (doors/buttons only), `/trustlist`, `/untrust` — applies to the claim the player is standing in
- **EssentialsX multi-homes**: `/sethome <name>` + `/home <name>` for fast travel between build sites
- Username verification: Mojang lookup `https://api.minecraftservices.com/minecraft/profile/lookup/name/<Name>` returns `{id, name}` — do this for EVERY name before whitelisting (catches typos like `krob050`→`Krob`)

## Pitfalls (summary — details in references)
- Panel may claim 'running' while the game port refuses connections — restart to re-bind; always verify from outside
- The container can regenerate `server.properties` on restart: custom MOTD lost, and version upgrades can silently reset `white-list=false` — re-check security-relevant props after any change
- Budget plans cap manual backups (Pebble: 2) and slot deletion can silently fail — plan around the cap
- Microsoft display name ≠ Java username; verify via Mojang's lookup API before whitelisting
- Pterodactyl file **download** endpoint uses `file_path=` param (not `file=`; that belongs to the contents-read endpoint) — 422 'The file path field is required' means you used the wrong param name
- Download response returns `attributes.url` (a signed URL) — fetch that with a browser User-Agent to get the bytes
- If a whitelisted name doesn't exist on Mojang, check near-variants (`Krob` vs `krob050`) — real users often type a number their actual handle doesn't have
- `/startup` returns `{object: list, data: [...]}` directly (egg_variable entries, each `attributes.env_variable` / `attributes.server_value`) — it has NO `attributes` wrapper; code written for `/` and `/servers/{id}` shapes throws KeyError there
- Modrinth search `facets` param is a JSON array-of-arrays (e.g. `[["categories:bukkit"],["project_type:plugin"]]`) URL-encoded into the query — a bare `categories:plugin` bracket string returns HTTP 400
- Agent-script actions on the panel (plugin install with server restart, backups) may sit pending approval in foreground sessions — stage everything, present the plan (plugin, version, restart caveat) and wait for explicit user go rather than retrying the blocked command
- A plugin may not list the newest MC version (e.g. supports 26.1.x, server runs 26.2) — plugins usually survive a point release; install, then judge from latest.log enable lines, not from the version list alone
- FAWE noise mentioning `net.coreprotect.worldedit.CoreProtectLogger` on `//set` = FAWE's default `extent.debug: true` complaining about CoreProtect's hook extent — edits and logging are fine; set `extent.debug: false` in FAWE config.yml, restart. Do NOT disable CoreProtect's `worldedit: true` to silence it (kills WE rollback logging). See `references/fawe-coreprotect-troubleshooting.md`
- Old console sessions rotate to `/logs/YYYY-MM-DD-N.log.gz`: fetch via the download endpoint (`file_path=` param, signed URL, browser UA) and `gzip.decompress` in Python — latest.log only holds the current boot; in-game plugin warnings live in the rotated log for when they happened
- Whitelist flow when Mojang 404s every case/spelling variant: stop guessing, ask the user to copy the exact username (title-screen or pause menu shows it) — a corrected name then verifies instantly (worked: 'Likeabucketof' dead → 'RustyToasterOven' real)
- **Staged ≠ loaded:** a jar uploaded to /plugins is completely inert until the next server boot. When the user says 'don't restart yet' (mid-build day — they did, 9/26), stage the upload, verify it landed in the dir listing, and let the next natural restart pick it up; never bounce the server without an explicit OK, and say what the restart costs (~20s blip, boots online players)
- Native capability probe: test for a vanilla/Paper gamerule by sending `gamerule <name>` via console, sleeping ~5s, and reading latest.log — `Unknown or incomplete command` means the rule doesn't exist on that build (e.g. NO minecart-speed gamerule exists on Paper 26.2 despite hsrails' README mentioning `minecartMaxSpeed` — that's for the optional Improved Minecarts experiment only)
- Modrinth search may return nothing for a multi-word query that plainly has hits ('powered rail speed' → 0): retry with a single broader keyword ('rail', 'minecart speed') — multi-word AND-matching is strict
- Panel file-write: PebbleHost rejects raw-text bodies with 403 — use the JSON envelope
  `{"raw": "<full file text>"}` (POST to `/files/write?file=<url-encoded path>`). Read-back after
  every write regardless of method.
- FAWE config changes don't need a restart: `fawe reload` via console applies live (`Configuration reloaded!` in latest.log). Reserve restarts for plugin jar changes. Verified live 9/29:
  navigation-wand `max-distance` 100 → 1000 (compass `/jumpto`/`/thru` reach) applied with zero
  downtime, players uninterrupted.

## Granting a player WorldEdit access (verified 2026-09-29, SFCA)
When a user says 'make it so <friend> can use WorldEdit', check before installing anything — the answer is often already 'yes':
1. **Plugin presence:** list `/plugins` — FAWE (FastAsyncWorldEdit) being installed means WorldEdit is available; commands are `//`-prefixed, NOT `/` (the single most common first-time failure — tell the player about double slashes proactively).
2. **Permission path:** ops bypass FAWE permission checks by default (`no-op-permissions: false` in `worldedit-config.yml` is the NORMAL model — it means standard WE permission plugin rules apply, and ops have them). Verify with `/servers/{id}/files/contents?file=%2Fops.json` — expect `level: 4`. If the player isn't op'd, prefer granting a LuckPerms group with `worldedit.*` nodes over op for trust-tier separation; only op when the user already chose op (e.g. they ran `/op <Name>` in game — confirm via latest.log before assuming).
3. **Config sanity:** scan `worldedit-config.yml` for restrictive limits (max-radius, max-blocks-changed, disallowed-blocks, use-inventory.enable) — defaults are permissive; no restart needed if untouched.
4. **Safety net:** with CoreProtect installed + `worldedit: true` in CoreProtect config, every FAWE edit is rollbackable — worth telling the user (lowers the 'letting a friend loose with //set' anxiety).
5. **Claim conflicts:** WorldEdit edits inside a GriefPrevention claim the player isn't trusted on are denied. If edits fail inside claims, the fix is `/trust <Name>` by the claim owner, not plugin config.
6. **Identifying who the friend is in-game:** don't ask the user which MC account — find it. Grep `logs/latest.log` for the user's own commands (`/op <Name>`, `/gamemode creative <Name>`, `/tp <Name> ...`) and chat/social lines to correlate names; verify against Mojang lookup before touching ops/whitelist. (Worked: 'Marisa' → OctoRis via `/op OctoRis` log line + online activity.)
7. **Report live evidence, not theory:** pull join times, gamemode changes, advancement/sign activity from latest.log so the user sees you actually checked ('she's in creative, online now, 2/20 players').

Logged a real instance of this? 2026-09-29: Marisa (OctoRis) — FAWE already present, op'd level 4 in-game by Adora, zero config changes needed. Avoided an unnecessary plugin reinstall + restart.

## Compass/navigation-wand distance (verified 2026-09-29, SFCA)
If a player reports the navigation wand (compass `/jumpto`, `/thru`) falls short:
1. Read `plugins/FastAsyncWorldEdit/worldedit-config.yml`, find `navigation-wand: max-distance` (default 100).
2. Patch the one value (100 → 1000 requested; no FAWE hard ceiling, pick a sane multiple, ask user if they want more).
3. Write back via the panel `raw` JSON envelope, read back to verify.
4. `fawe reload` via console — live, no restart, players uninterrupted. Confirm `Configuration reloaded!` in latest.log.
Full flow and config notes in `references/pterodactyl-client-api.md` § FAWE config quick-reference.

## Insurance-blocked pharmacy vaccines (non-gaming, observed 2026-10-04)
Not a server task — logged here only because the session surfaced it mid-flow. When a user's
vaccine appointment is refused by a pharmacy for insurance reasons: it's network membership
(venue-specific), not coverage existence. The fix paths: use a pharmacy that has ALREADY billed
the user's plan successfully before (that one is in-network by definition), the county health
department (often free regardless of insurance), or the PCP's office (billed differently).
Recommend the user check their plan's app for in-network pharmacy lists; never send them to
another random pharmacy to 'try their luck' — that's a full energy-day spend per rejection for
a chronically ill user.

## Backup cron reliability (verified 2026-10-03, SFCA)
When a scheduled backup cron reports failure, diagnose before re-running:
1. **HTTP 204 = success for backup creation.** Pterodactyl returns 204 No Content on POST /backups; a script that treats empty-body 2xx as failure exits falsely. Treat 204 as success.
2. **Backups are async (~2-4 min).** If a retry hits "action in progress", the FIRST POST actually landed — re-list backups (GET /servers/{id}/backups) and verify the new entry (name/size/is_successful) instead of firing a third POST.
3. **Backup failures can be credential, not panel:** an auth provider whose refresh token was rejected (auth.json `last_auth_error.code: invalid_grant`, credential pool empty) silently blocks the preflight before any panel call. Fix is agent-side re-login (`hermes auth login <provider>`), NOT panel retries. Check the auth provider's error fields before blaming the server.

