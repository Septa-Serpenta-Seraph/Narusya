# Stage A Deploy — Real Results (2026-07-18)

> What actually happened when we installed + tried to boot Red on Narusya's VM.
> For Tyler / Lumi picking this up later.

## Environment (verified)
- Host: Linux 6.8.0-136-generic, Python 3.11.14
- Already running: Hermes gateway (`polinkly` profile, PIDs 1110/1111),
  qdrant, camoufox
- RAM: 3.8G total, ~165M free / 2.2G avail
- Disk: 89% full, **4.0G free** at start

## Steps completed
1. ✅ `python3 -m venv ~/redenv` + `pip install -U "Red-DiscordBot[sqlite]"`
   → **Red 3.5.24 installed clean.**
   - Resource cost: disk **4.0G → 3.7G free** (−300M); RAM used 1.6G → 1.8G at boot.
2. ✅ `redbot-setup` → instance **`narred`**, **JSON backend**, data at `~/reddata`.
   - Pitfall: `redbot-setup` rejects uppercase `Y` for confirm → use lowercase `y`
     or empty+Enter. (See `scripts/red_setup.sh` for non-interactive path.)
3. ✅ Boot tested `--dry-run` → framework loads, reaches token prompt, clean exit.
4. ❌ Live boot on token → **discord.py version dead-end** (see
   `discordpy-compat-2026-07-18.md`). All 5 pinned versions crash.

## Token findings (IMPORTANT)
- The **live** Discord token keeping Narusya online = `polinkly` profile
  `.env` `DISCORD_BOT_TOKEN`. That is the Hermes gateway token.
- `secrets/narusya_token.txt` is a **STALE copy → returns `401 Unauthorized`**.
  Do NOT use it. Verified via `GET /users/@me` → `{"message":"401: Unauthorized"}`.
- Sharing the live token with Red = two processes on one Discord session
  (same-token sharding, which Lumi's instance proves works) — BUT chaotic
  relaunching risks invalidating the session and bouncing Adora's daemon.
  Lumi's works because it's *steady*.

## Gateway safety (verified)
- After **every** Red crash, `pgrep -f "hermes_cli.main gateway run"` returned
  **ALIVE**. Red dies at import / pre-connect, so it never contests the live
  session. Adora's connection to Narusya was never dropped. ✅

## Where it's parked
- Red installed + JSON-configured + boot-tested, but **unbootable** on this
  stack without a sharding patch (or a different Red build).
- No Red process running. Nothing touches the gateway.
- `red-discordbot` skill is complete + documented.

## To resume (morning)
1. Decide resolution: patch `bot.py` (one-liner) OR try Red 3.6-dev, OR leave dormant.
2. If booting on the live token: fix discord.py FIRST (crashes are pre-connect,
   safe), then ONE calm supervised launch, then immediately `pgrep` the gateway
   to confirm still ALIVE. Kill Red if gateway drops.
3. Cog ops are in-guild `[p]` commands only (no CLI). See README §8.
