# Minecraft Versions 2026 + Paper on a Panel

## The 26.x versioning scheme
- The 1.x line ended at **1.21.11** (Dec 2025). From 2026: `YY.drop[.hotfix]` — 26.1 (Mar), 26.2 'Chaos Cubed' (Jun), 26.3 (Sep snapshots), ~3-4 drops/year.
- **There is no 1.26.** Searching for it finds nothing.

## Java requirements
- 26.1 and later: **Java 25** (hard requirement, all server software).
- 1.17–1.21.11: Java 21.
- Launchers ship their own Java so players don't notice; servers must be pointed at the right one.

## Paper (current server jar of choice)
- Version + support status API: `https://fill.papermc.io/v3/projects/paper/versions` → `versions[].version.support.status` (SUPPORTED vs UNSUPPORTED) and `java.version.minimum`.
- Build download: `https://fill.papermc.io/v3/projects/paper/versions/26.2/builds` → newest entry, `channel: STABLE`, `downloads['server:default'].{url,name,checksums.sha256,size}` (~60MB jar).
- On a panel: upload jar to `/`, `PUT startup/variable` JARFILE=jar name, LOADER_JAVAVERSION=25, restart.

## World migration (1.21.x → 26.x)
- 26.1 reorganized world storage (world/dimensions/..., world/players/). Paper runs this migration automatically on first boot of a 26.x jar — the log prints a loud `WorldFolderMigration ALERT` offering a pre-migration backup window. TAKE A BACKUP FIRST; the migration is one-way.
- Post-migration: re-verify server.properties — the migration/upgrade regenerated it and reset `white-list` to false and MOTD to default in one observed case.

## Plugin sourcing — Modrinth API (reliable), not GitHub releases
```
GET https://api.modrinth.com/v2/project/<slug>/version?loaders=%5B%22paper%22%5D            # newest first
GET https://api.modrinth.com/v2/project/<slug>/version?loaders=...&game_versions=%5B%2226.2%22%5D
```
- GitHub latest-release assets are often empty (CoreProtect posts Patreon links), and some repos 404 outright. Modrinth is the dependable path.
- The modrinth `game_versions` list in a version can be a long legacy list — check the server's exact version is covered before installing. (EssentialsX 2.21.0 → crash on 26.2; 2.22.0 → works but logs a benign 'unsupported server version' ERROR.)
- Community staples: EssentialsX, LuckPerms, CoreProtect, GriefPrevention (+ DiscordSRV for a Discord chat bridge, needs bot token + MySQL).

## Usernames: display name ≠ Java username
- Microsoft profile page shows a display name ('Miss Adora9773'); the actual Java username was `missadora`.
- Authoritative check: `GET https://api.minecraftservices.com/minecraft/profile/lookup/name/<name>` → `{id, name}` or 404. (api.mojang.com randomly 403s — WEB-7591; use the minecraftservices host.)

## Recommended defaults (friends/community server, 6-15 players, 6GB)
- Paper latest supported (26.x), Java 25, difficulty normal, view-distance 10, simulation-distance 6, spawn-protection 8, white-list=true, enforce-secure-profile=false (avoids chat-report friction), enable-command-block=true.
- JVM: Xms4G/Xmx6G G1GC flag set.
- MOTD color codes are `\u00a7`-escaped in properties files (`\u00a7a` green, `\u00a7b` aqua, `\u00a76` gold, `\u00a78` dark gray).
