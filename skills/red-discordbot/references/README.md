# Red-DiscordBot Integration — README

> Authoritative, step-by-step guide for installing, hosting, and authoring Red-DiscordBot cogs from within the Hermes/Narusya environment. Written 2026-07-18.

---

## 1. What Is Red, and Why Integrate?

[Red-DiscordBot](https://github.com/Cog-Creators/Red-DiscordBot) is a mature open-source Discord bot framework built on `discord.py`. Its superpower is the **cog ecosystem**: functionality ships as modular Python packages ("cogs") that are:

- **Installable** from community repos (`[p]repo add` → `[p]cog install`)
- **Hot-reloadable** without restarting the bot (`[p]reload mycog`)
- **Authorable** by you — write your own Python, drop it in, load it

Thousands of cogs exist: music, RPG/dice, polls, economy, moderation, welcome messages, trivia, and more.

**Why Narusya wants this:** Hermes is a *sovereign daemon* — deep, relationship-shaped, but it doesn't ship with a music player or a DnD dice roller. Red gives **breadth**. Hermes gives Red **agency** — a daemon that decides *which* cogs the community needs and *writes* them when none exist. Together: I can go "the communal-hall DnD crowd needs a dice roller" → install or author a cog → hot-reload → done.

**Scope rule:** Red handles *community-function cogs*. Hermes stays the *daemon/relationship* core. Don't re-implement Hermes's own powers (moderation log, daemon sweep) as cogs — that's redundant.

---

## 2. Prerequisites (verified 2026-07-18)

| Requirement | Status |
|---|---|
| Python 3.8+ | ✅ 3.11.14 present |
| Git | check: `git --version` |
| `venv` | ✅ stdlib |
| RAM | ⚠️ 3.8G total, ~165M free (tight — see §3) |
| Disk | ⚠️ 89% full, 4.0G free (tight — see §3) |

Red **requires** installation into a virtual environment. Do not install into the system Python.

---

## 3. HOST CONSTRAINT WARNING (read before installing)

Narusya's VM (2026-07-18) already runs: Hermes gateway, qdrant, camoufox. Resources are tight:

- **RAM:** 3.8G total, 1.6G used, only 165M *free* (2.2G reclaimable from cache).
- **Disk:** 89% full, **4.0G free**.

**Therefore:**
- ✅ Use **SQLite** or **JSON** data backend. Both are zero-config, no DB server.
- ❌ **DO NOT install PostgreSQL.** It would eat 300–500M RAM we don't have, plus disk.
- Red's `redbot-orm` package and the `[sqlite]` pip extra give SQLite support with no setup.

If at any point `free -h` shows < 500M available or `df -h /` shows < 1G free, **stop** — move to Stage B (dedicated host, see §10).

---

## 4. Install (constrained host)

```bash
# from your home dir
python3 -m venv ~/redenv
source ~/redenv/bin/activate
# SQLite extra = no Postgres needed
pip install -U "Red-DiscordBot[sqlite]"
# verify
redbot --version
```

The `scripts/red_install.sh` in this skill does exactly this. Run: `bash ~/.hermes/skills/red-discordbot/scripts/red_install.sh`

---

## 5. Instance Setup

```bash
redbot-setup
```

It will ask:
- **Storage backend** → choose **JSON** or **SQLite** (NOT PostgreSQL)
- **Data path** → e.g. `~/reddata`
- **Instance name** → e.g. `narred`

Red stores all cog data + config under that path.

---

## 6. SAME-TOKEN COEXISTENCE (the important part)

**Proven working on Lumi's instance:** Hermes gateway + Redbot run off the *same* Discord profile/token. Discord permits same-token multi-connection (via sharding). This is documented Red behavior ("running multiple instances of Red on the same machine").

**The ONE rule that makes it work:** distinct triggers so the two bots don't both answer every message.

| Bot | Trigger | Prefix/Mode |
|---|---|---|
| Hermes (Narusya) | mention or allowlisted channel | configured in `config.yaml` |
| Red | command prefix | `[p]` (configurable via `redbot-setup` / `[p]prefix`) |

Set Red's prefix to something Hermes never uses (default `[p]`). Then:
- Messages starting with `[p]` → Red responds.
- Mentions / allowlisted channels → Hermes responds.
- No overlap → no double-fire.

**Two topologies:**
- **A. Shared token (Lumi's model):** Red uses the *same* `DISCORD_BOT_TOKEN` as Hermes. Simplest, one bot identity, two processes. **Requires Adora's approval** (she owns the token).
- **B. Second bot:** Red gets its own Discord application + token. Isolated, but a separate bot identity in servers.

---

## 7. Running Red

```bash
source ~/redenv/bin/activate
# DRY RUN first (no token, just boots the framework):
redbot narred --dry-run
# Real run (only after Adora approves the token):
redbot narred --token "$DISCORD_BOT_TOKEN"
```

For production, run under a supervisor (systemd user service or `nohup`) so it survives reboots. Red docs cover Linux autostart.

---

## 8. Cog Management (the daily operation)

Once Red is up, in any channel it can see:

```
[p]repo add <name> <git-url>     # add a community cog repo
[p]cog install <repo> <cog>      # install a cog from a repo
[p]load <cog>                    # load an installed cog
[p]reload <cog>                  # hot-reload after editing
[p]unload <cog>                  # unload
[p]cog list                      # list installed/available cogs
```

Narusya can also run these non-interactively via `scripts/red_cog_ops.py`:
```bash
python3 ~/.hermes/skills/red-discordbot/scripts/red_cog_ops.py narred load mycog
```

---

## 9. Authoring Your Own Cog

Copy the template:
```bash
cp ~/.hermes/skills/red-discordbot/templates/mycog.py ~/reddata/cogs/mycog.py
cp ~/.hermes/skills/red-discordbot/templates/info.json ~/reddata/cogs/info.json
```

Edit `mycog.py` — modern Red V3 style:
```python
from redbot.core import commands
import discord

class Mycog(commands.Cog):
    """My custom cog that does stuff!"""

    @commands.command()
    async def mycom(self, ctx):
        """This does stuff!"""
        await ctx.send("I can do stuff!")

    @commands.command()
    async def punch(self, ctx, user: discord.Member):
        """I will punch anyone! >.<"""
        await ctx.send(f"ONE PUNCH! And {user.mention} is out! ლ(ಠ益ಠლ)")

def setup(bot):
    bot.add_cog(Mycog())
```

Then `[p]load mycog`. Edit + `[p]reload mycog` to iterate. Live, no restart.

**Note on legacy docs:** Old Red tutorials use `self.bot.say(...)` — that's deprecated. Use `ctx.send(...)`. The template uses the modern API.

---

## 10. Privacy & Compliance (SFCA / Cultus Anarchia)

Red collects some user data by default (nickname history, command-content used directly as commands). For our community servers:

```
[p]mydata forgetme              # user removes their own data
[p]mydata ownermanagement deleteforuser <id>   # owner deletes for a user
```

Bot owners are responsible for Discord ToS + applicable law. Be forthright with users about what's stored.

---

## 11. Updating

```bash
source ~/redenv/bin/activate
pip install -U Red-DiscordBot
```

Cogs can break on Discord API changes — budget for periodic maintenance. Community repos often push fixes; `[p]cog update` (if the repo supports it) or re-install.

---

## 12. Stage A vs Stage B

- **Stage A (this host, SQLite):** Proof-of-concept. Install, boot with `--dry-run`, confirm it runs, watch RAM/disk. Do NOT connect live token without Adora's explicit approval.
- **Stage B (dedicated host):** If Stage A shows RAM < 500M avail or disk < 1G free, or if we want isolation, run Red on a separate lightweight box (or co-locate with Lumi's proven stack). Same-token sharding still applies.

---

## 13. Security Checklist

- [ ] Red runs in its own venv (never system Python)
- [ ] SQLite/JSON backend (no Postgres on constrained host)
- [ ] Distinct prefix from Hermes (no double-fire)
- [ ] Live token connection approved by Adora
- [ ] `[p]mydata` commands available for user privacy requests
- [ ] Supervised process (survives reboot)
- [ ] Resource watch (`free -h`, `df -h /`) after deploy
