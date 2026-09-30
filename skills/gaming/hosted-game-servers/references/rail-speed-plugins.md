# Rail / minecart speed plugins on Paper 26.x

Researched 2026-09-26 for SFCA (Paper 26.2, PebbleHost). Question: change powered-rail speeds.

## No native gamerule (verified live)
Probed via console on Paper 26.2 build 129 (2026-09-26): `minecartMaxSpeed`, `maxMinecartSpeed`, `minecartSpeedLimit`, `railSpeed` — ALL returned `Unknown or incomplete command`. The `minecartMaxSpeed` gamerule mentioned in some plugin READMEs belongs to the optional 'Improved Minecarts' experiment, not stock Paper 26.2. Don't trust a README's gamerule list — probe the console first (send `gamerule <name>`, read latest.log ~5s later).

## Chosen: CartSpeed 1.0 (Modrinth `cartspeed`)
- Bukkit/Paper/Spigot, officially lists 26.2. 11KB jar.
- `/cartspeed global <multiplier>` — all carts, real time; `/cartspeed nearest <x>` — the cart closest to you; `/cartspeed reload`. Permission `cartspeed.admin`, Op-only by default.
- Adjusts per-entity or global speed multipliers in config; deleting a cart's UUID from config.yml resets an overspeeded cart.
- Author warning: high values glitch from Minecraft physics; delete config.yml to recover.
- Status: STAGED in /plugins 2026-09-26, not yet boot-verified (user deferred restart).

## Alternative worth knowing: hsrails (ergor/hsrails)
- Different design: powered rail placed on a **boost block** (redstone block by default) = high-speed rail (default 4x ≈ 32 m/s); powered rail on any other block = normal. Enables mixed fast/normal networks, plus a hard-brake block (soul sand, 8x decel).
- Config: `speedMultiplier` (1–8), `boostBlock`, `hardBrakeMultiplier`, `hardBrakeBlock`; `/hsrails <1-8>` temporary override.
- **Physics ceiling: ~4x.** Higher multipliers add momentum/coast time, not top speed.
- Composes with `minecartMaxSpeed` gamerule if the Improved Minecarts experiment is on.
- Downside: last release v1.5.0 2025-06 (Folia support), no published jar builds for 26.x — would need compiling from source before it's usable on 26.2.

## Dead ends / adjacent
- **BetaMinecart** — removes the speed cap entirely (beta-preview behavior), but only lists ≤1.21.1.
- **RailDest** (`raildest`) — automatic rail junctions, supports 26.2 (not speed, but pairs well with a network).
- **Simple Trains** — fast-travel train stations, only ≤1.21.11.
- Enhanced Rails — April-fools-domain listing; up to 10x claimed, unverified quality — skip.

## Search note
Modrinth multi-word queries AND-match strictly: 'powered rail speed' → 0 hits, 'minecart speed' → the two relevant plugins. Use single keywords and facets `[["categories:bukkit"],["project_type:plugin"]]`.
