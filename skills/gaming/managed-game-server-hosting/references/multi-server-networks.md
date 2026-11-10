# Multi-server networks: proxy + backends (PebbleHost / Pterodactyl)

Condensed from PebbleHost's BungeeCord guide and the Sub-Servers feature. Use with the `managed-game-server-hosting` skill.

## Sub-Servers (split one plan)

- Panel: left nav → Sub Servers. Shows "used X of Y" slots; split RAM/CPU with sliders.
- Choose type: **proxy** (BungeeCord/Velocity), **minecraft**, or **bots**. MC sub-servers need ≥2 CPU threads and a minimum RAM (2GB on standard plans; 1GB on extreme plans).
- Plan must have spare RAM/CPU. If the primary server is near capacity (SFCA ~5GB/6GB), splitting starves it — buy a separate plan or upgrade first.
- After splitting, the primary server is no longer splittable until resources are freed.
- Blue bars = reserved (unusable) resources; only the white portion is assignable.

## Proxy setup (BungeeCord) — PebbleHost one-click

Requirements: 3 services minimum — one BungeeCord proxy (1GB is enough), one hub/lobby, one or more backend gamemodes. Dedicated IP goes on the proxy, not the backends.

1. On the proxy server: panel → "Jars and Preinstalls" → choose BungeeCord. Start; wait for "Startup Listening on /0.0.0.0:{PORT}". Stop.
2. Edit `config.yml` on the proxy:
   - `ip_forward: true`
   - `listeners.host: 0.0.0.0` (include port; 25565 if dedicated IP)
   - Under `servers`: copy the default `lobby` entry per backend; set each `address` to `IP:PORT` (include port).
   - Set `motd` under `listeners`.
   - `priorities`: set default server to lobby name; `force_default_server: true` to force lobby entry.
   - To restrict a backend: enable whitelist on that backend server.
3. On every backend: `server.properties` → `online-mode=false`; `spigot.yml` → `bungeecord: true` under settings. Restart each backend.
4. Restart proxy last. Verify with `/server` in-game.
5. **UUID-spoofing protection:** BungeeCord allows join-as-anyone. Follow PebbleHost's "protect against UUID spoofing" guide (BungeeGuard plugin or IP-forward trust). Mandatory before opening to players.

## Proxy setup (Velocity) — modern alternative

- Download Velocity jar; run once to generate `velocity.toml` + `forwarding.secret`.
- Backends: Paper proxy config → `proxy-protocol`/`velocity` forwarding mode, paste the secret.
- Velocity modern forwarding is the recommended mode for Paper 26.x.
- Do NOT chain proxies (Velocity behind BungeeCord unsupported).

## In-game portals

- **Advanced Portals** plugin: creates physical portals that switch servers via BungeeCord plugin messaging. Install on backends; configure destination server names matching the proxy's `servers` block.
- Alternatives: ServerSelector, AnimatedMenu (GUI menus).
- Portal destination names must exactly match proxy server keys.

## Patreon-gated access on MC 26.2

No modern plugin supports Paper 26.2 for Patreon whitelist (Minecraft Authentication stops at 1.19.2; MCLink is Java 8 / 1.7.10-era).

**Option 1 — Custom automation (recommended):**
- Patreon webhook (member pledge create/update/delete) → handler verifies tier via Patreon API → Pterodactyl console command `whitelist add <name>` (or `whitelist remove`).
- Players submit their Minecraft Java username via a form or Discord command; resolve canonical name via `api.minecraftservices.com/minecraft/profile/lookup/name/<name>` before whitelisting.
- Host the webhook handler on the home VM (same machine that runs the backup cron) or a small service; reuse the existing `ptero-helper.py` plumbing (console command endpoint).
- On tier downgrade/cancellation → `whitelist remove`.
- Store Patreon token in `~/.hermes/secrets/` (chmod 600), never in chat.

**Option 2 — Discord-gated (fallback):** only Patreon-tier Discord members see the server IP/channel; keep whitelist off; rely on obscurity + GriefPrevention + Op ban power. Zero build cost, weaker.

**Option 3 — Permission-plugin gate:** whitelist off; LuckPerms + Skript (or a tiny plugin) kicks non-patrons on join. Middle ground.

MCPatron (Patreon creator service) exists but is small/semi-abandoned; manages whitelist via `whitelist.json` download — third-party dependency.

## Verification (network)
- [ ] Proxy starts and logs "Startup Listening on /0.0.0.0:{PORT}"
- [ ] Each backend starts with `online-mode=false` and forwarding enabled
- [ ] `/server` lists all backends; switching works in-game
- [ ] Advanced Portals (or menu) teleports between servers
- [ ] UUID-spoofing protection active (test join-as-other-name is rejected)
- [ ] Backend ports not directly joinable without whitelist (for gated backend)
- [ ] MOTD/properties readback after restart; re-apply if regenerated
- [ ] Backups configured per backend (each server has its own backup slot budget)
