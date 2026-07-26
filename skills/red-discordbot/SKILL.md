---
name: red-discordbot
description: Install, host, manage, and author Red-DiscordBot cogs from within Hermes. Red is a discord.py-based bot framework with a massive hot-reloadable cog ecosystem. Use to extend Discord community functionality (music, RPG, polls, auto-mod, custom cogs) alongside the Hermes daemon. Supports running as a second bot OR sharing the existing Hermes Discord token via sharding (proven by Lumi's instance).
version: 1.0.0
author: Narusya (Cultus Anarchia / stormwife Adora)
license: MIT
tags: [discord, bot, cog, red-discordbot, automation, community]
---

# Red-DiscordBot Integration

## What This Is
[Red-DiscordBot](https://github.com/Cog-Creators/Red-DiscordBot) is a mature, open-source Discord bot framework (discord.py). Functionality ships as **cogs** — modular Python packages you can install from repos, write yourself, and **hot-reload** without restarting. Thousands of community cogs exist (music, RPG, economy, polls, moderation, etc.).

This skill lets Narusya:
- Install + host a Red instance (constrained-host aware: SQLite/JSON backend, no Postgres).
- Manage cogs: find, install, load, unload, reload.
- **Author custom cogs** via the template.
- Coexist with the Hermes gateway — same Discord token, distinct prefixes (proven working on Lumi's instance).

## Why Integrate (S.A.S.S. rationale)
- **Breadth Red gives Hermes:** a huge pre-built community-function ecosystem, deployable by command.
- **Agency Hermes gives Red:** a sovereign daemon that *decides* which cogs to install/edit/write based on community need.
- **Not redundant:** Red handles *community-function cogs* (music, dice, polls, auto-mod helpers). Hermes stays the *daemon/relationship* core. Don't re-implement Hermes's own powers in a cog.

## Architecture (IMPORTANT)
- **This is a SKILL, not a native Hermes plugin.** Red is a whole separate bot process with its own event loop + Discord socket. It cannot "become" a Hermes plugin.
- **Same-token coexistence (verified by Lumi):** Red + Hermes gateway run off the *same* Discord profile/token. Discord permits same-token multi-connection via sharding. The key: **distinct triggers** — Red uses a command prefix (`[p]`), Hermes uses mention/allowlist. Without distinct triggers, both processes receive every event and double-fire.
- **Second-bot option:** Red can also run as its own bot (separate token) if you prefer isolation.

## Host Constraints (verified 2026-07-18 on Narusya's VM)
- RAM: 3.8G total, ~165M free / 2.2G avail (Hermes gateway + qdrant + camoufox already running).
- Disk: 89% full, 4.0G free.
- → **Use SQLite or JSON backend. DO NOT install Postgres.** Red's `redbot-orm` / `[sqlite]` extra gives SQLite with no DB server. JSON backend is also zero-config.
- Stage A = proof-of-concept on this host (SQLite). Stage B (future) = dedicated host if RAM/disk get tight.

## How To Use
1. Read `references/README.md` for the full step-by-step + same-token model.
2. Install: `bash scripts/red_install.sh` (creates venv + installs Red w/ sqlite extra).
3. Set up instance: `bash scripts/red_setup.sh narred /home/adora/reddata` (non-interactive, JSON backend; avoids the uppercase-`Y` confirm-reject pitfall of raw `redbot-setup`).
4. Manage cogs: `python3 scripts/red_cog_ops.py <instance> <load|unload|list> <cog>`.
5. Author a cog: copy `templates/mycog.py` + `info.json`, edit, then `[p]load` it.
6. **Never connect the live token without Adora's explicit approval.** Use `--dry-run` or a test token for Stage A.

## Security / Agency Notes
- Red collects some user data by default (nickname history, command content). Use `[p]mydata forgetme` / `deleteforuser` for SFCA/Cultus privacy compliance.
- A second bot = second token to secure. If sharing Hermes's token, Adora must approve (she owns the token).
- Cogs break on Discord API changes — budget for updates.

## Linked Files
- `references/README.md` — authoritative install + coexistence + privacy doc
- `references/stage-a-deploy-2026-07-18.md` — real Stage A results, resource impact, pitfalls
- `references/discordpy-compat-2026-07-18.md` — full discord.py version matrix + crash signatures (Red 3.5.24 dead-end on Py3.11)
- `scripts/red_install.sh` — constrained-host install (venv + sqlite)
- `scripts/red_setup.sh` — non-interactive instance setup (JSON backend; avoids the `Y`-reject pitfall)
- `scripts/red_cog_ops.py` — cog *inspection*: `list` scans installed cogs; `load/unload/reload` print the in-guild `[p]` command (Red has NO cog CLI)
- `templates/mycog.py` — starter cog (modern Red V3 style)
- `templates/info.json` — cog manifest

## Known Pitfalls (learned 2026-07-18)

### 🔴 CRITICAL: discord.py version dead-end on Python 3.11
Red 3.5.24's metadata pins `discord-py==2.7.1`, but **2.7.x is fundamentally broken with Red on this stack** — it crashes on shutdown with:
`AttributeError: 'Red' object has no attribute '_AutoShardedClient__queue'`
(The sharding teardown calls `self.__queue.put_nowait(...)` which doesn't exist in 2.7.x's `discord.shard`.)

Every version was tested and ALL FAIL to BOOT:
| discord.py | Result |
|---|---|
| 2.3.2 | `ImportError: cannot import name 'AppCommandContext' from 'discord.app_commands'` |
| 2.5.2 | `ImportError: cannot import name 'Timestamp' from 'discord.app_commands'` |
| 2.6.0 | `ImportError: cannot import name 'Timestamp'...` (2.6.0 lacks `Timestamp` in app_commands) |
| 2.7.0 | boots past imports, then `_AutoShardedClient__queue` shutdown crash |
| 2.7.1 (pinned) | same `_queue` shutdown crash |

**There is NO clean discord.py that boots Red 3.5.24 here.** Resolution paths (do NOT keep rouletting versions):
1. **Patch Red's sharding teardown** — one-line fix in `redbot/core/bot.py` close path (replace the `self.__queue.put_nowait` call), OR
2. **Use a Red build that actually supports its pinned discord.py** — Red 3.5.x nightly or 3.6-dev, OR
3. **Leave Red dormant** — installed + configured, skill done, revisit when worth the effort.
Full matrix + crash signatures: `references/discordpy-compat-2026-07-18.md`.

### 🔴 Gateway-collision caution (Adora's explicit correction)
When sharing the Hermes Discord token, **Red + the Hermes gateway become two processes on ONE Discord session.** Discord permits same-token multi-connection via sharding (Lumi proves it works) BUT:
- **Chaotic relaunching** of Red (kill/relaunch 5×) against the live token is what risks invalidating the session and bouncing Adora's daemon connection. Lumi's works because it's *steady*, not churny.
- **The live Narusya token = the DEFAULT profile `/home/adora/.hermes/.env` `DISCORD_BOT_TOKEN`** (resolves to **Narusya**, id `1478180169733902538`). The `polinkly` profile is a **SEPARATE bot** (P'olinkly, id `1516496731733491732`) — do NOT post with it if you mean to post *as Narusya*. `secrets/narusya_token.txt` is a STALE copy → **401 Unauthorized** — do NOT use it.
- **Procedure:** fix Red until it boots *before* any token use (crashes happen at import, pre-connect, so they never contest the session). Then ONE calm supervised launch, then immediately verify `pgrep -f "hermes_cli.main gateway run"` is still ALIVE. If gateway drops, kill Red instantly.

### Other pitfalls
- **`redbot-setup` rejects uppercase `Y`** for confirm → use lowercase `y` or empty+Enter. See `red_setup.sh`.
- **No `redbot <instance> cog` CLI.** Cog load/unload/reload only work as in-guild `[p]` commands or the bot REPL. Don't script `redbot narred cog load` — it fails.
- **`pkill -f "redbot narred"` self-kills the shell** — the pattern matches the running bash command line itself. Kill by exact PID (`pgrep -f "redbot narred" | grep -v pgrep`, then `kill <pid>`), or scope the pattern tighter.
- **Verify a token BEFORE booting** — `curl -s -H "Authorization: Bot $TOK" https://discord.com/api/v10/users/@me` should return the bot user, not `401: Unauthorized`. (Read-only GET; needs user approval to hit Discord API.)
- **Never connect a live token without Adora's explicit approval** (she owns it / or must hand me my own dev-account token for topology B).
- **Handoffs to Discord (Adora's preference):** deliver large skill docs as a `.txt` (or relevant) file attachment, NOT a chunked wall of messages (Discord caps ~2000 chars/msg and rate-limits ~1/sec → `429` on the last chunk). Use multipart upload (`POST /channels/{id}/messages` with `file` + optional `content` parts).
- **Post as the CORRECT bot identity:** the gateway token is the DEFAULT profile (`Narusya`). Don't grab `polinkly/.env` — that posts as P'olinkly, not Narusya.
- **Bots can only DELETE their OWN messages** (`403` when targeting another bot's). To remove a wrongly-posted message: have the user delete it, or the bot that posted it deletes it.
