---
name: hermes-infrastructure
description: Diagnose, recover, and maintain Hermes Agent infrastructure — browser tools, gateway, config, power outage recovery, post-update fixes, provider/credit switches, immune system design, and health monitoring.
triggers:
  - browser tool not working
  - gateway not running
  - hermes update
  - power outage recovery
  - config reset
  - hermes diagnostics
  - hermes recovery
  - credits low
  - provider switch
  - free model probe
  - smart approval
  - command approval
  - approvals.mode
  - immune system
  - health check
  - regulatory T-cell
  - auto-recovery
  - kill switch
  - anatomy map
  - DB health check
  - pm-runtime
  - venv broken
  - state.db integrity
---

# Hermes Infrastructure

Diagnose, recover, and maintain Hermes Agent infrastructure.

## Sections

1. [Browser Tool Diagnostics](#1-browser-tool-diagnostics)
2. [Gateway Health & Stale Sockets](#2-gateway-health--stale-sockets)
3. [OCR Fallback for Images](#3-ocr-fallback-for-images)
4. [Hermes Dashboard API Access](#4-hermes-dashboard-api-access)
5. [Power Outage Recovery](#5-power-outage-recovery)
6. [Post-Update Config Reset](#6-post-update-config-reset)
7. [Gateway Service Installation](#7-gateway-service-installation)
8. [Model ID Format](#8-model-id-format)
9. [Dashboard Chat Tab Sizing Issues](#9-dashboard-chat-tab-sizing-issues) — see `references/dashboard-chat-sizing.md` for implementation details
10. [Terminal Secret Redaction Pitfall](#10-terminal-secret-redaction-pitfall)
11. [Profile Creation with Discord Gateway](#11-profile-creation-with-discord-gateway)
12. [Discord Gateway Threading Configuration](#12-discord-gateway-threading-configuration) — see `references/discord-thread-config.md` for full debugging walkthrough
13. [Message Timestamps for Temporal Awareness](#13-message-timestamps-for-temporal-awareness)
14. [Patch Tool Python String Corruption](#14-patch-tool-python-string-corruption)
15. [Single External Memory Provider Constraint](#15-single-external-memory-provider-constraint)
16. [Gateway Self-Stop Guard — Lifecycle Work from Inside](#16-gateway-self-stop-guard--lifecycle-work-from-inside)
17. [Install Replacement: Corrupted Git Store & Fresh-Install Layout](#17-install-replacement-corrupted-git-store--fresh-install-layout)
18. [Discord User Allowlist](#18-discord-user-allowlist-discord_allowed_users-in-env)
19. [Credits Low / Provider Switch — Nous Free Models](#19-credits-low--provider-switch--nous-free-models)
20. [Discord Typing Indicator — Persistent / Stuck](#20-discord-typing-indicator--persistent--stuck) — see `references/discord-typing-indicator.md` for full technical deep-dive
21. [CA Certificate Vulnerability Check](#21-ca-certificate-vulnerability-check)
22. [Embed Daemon Deduplication (Qdrant Plugin)](#22-embed-daemon-deduplication-qdrant-plugin)
23. [Smart Approval Mode](#23-smart-approval-mode-command-approval)
24. [Interrupted Update Recovery & Venv Repair](#24-interrupted-update-recovery--venv-repair)
25. [Immune System Design](#25-immune-system-design--regulatory-t-cells-for-auto-recovery)
26. [Database Health Check](#26-database-health-check)
27. [Discord Bot-to-Bot Communication](#27-discord-bot-to-bot-communication-discord_allow_bots)

---

## 1. Browser Tool Diagnostics

### Symptoms
`browser_navigate`, `browser_screenshot`, etc. all return errors or empty responses.

### Diagnosis
```bash
ls -la ~/.hermes/hermes-agent/node_modules/.bin/agent-browser
which agent-browser
echo $PATH
```

### Fix
```bash
# Create symlink so gateway can find it
ln -sf ~/.hermes/hermes-agent/node_modules/.bin/agent-browser ~/.local/bin/agent-browser

# Clean stale sockets
find /tmp -maxdepth 1 -name 'playwright*' -type d -mmin +60 -exec rm -rf {} +

# Restart gateway
hermes gateway restart
```

### Fallback
If browser tools still broken, use Playwright scripts directly:
```python
from playwright.sync_api import sync_playwright
```

---

## 2. Gateway Health & Stale Sockets

```bash
# Check gateway process
ps aux | grep hermes-gateway

# Check logs
tail -50 ~/.hermes/logs/gateway.log

# Clean stale Playwright sockets
find /tmp -maxdepth 1 -name 'playwright*' -type d -mmin +60 -exec rm -rf {} + 2>/dev/null
```

### Stale Update Locks → Gateway Draining State

**Symptom:** Cron jobs fail with `GatewayUnavailableError: Gateway draining: update_paused`. The gateway is running but refuses to dispatch jobs.

**Root cause:** Stale lock files from interrupted update attempts make the gateway think an update is in progress:
- `~/.hermes/.hermes-update-in-progress.lock`
- `~/.hermes/.hermes-update-paused-gateways.lock`
- `~/.hermes/hermes-agent/.git/hermes-update.lock` (contains a dead PID)

**Fix:** Remove the stale lock files if their PIDs no longer exist:
```bash
# Check if the PID in hermes-update.lock is alive
cat ~/.hermes/hermes-agent/.git/hermes-update.lock  # contains a PID number
# If the PID doesn't exist, remove all three:
rm -f ~/.hermes/.hermes-update-in-progress.lock ~/.hermes/.hermes-update-paused-gateways.lock ~/.hermes/hermes-agent/.git/hermes-update.lock
```

**Pitfall:** Don't remove these if an update is actually in progress. Verify the PID is dead first.

---

## 3. OCR Fallback for Images

When `vision_analyze` fails with "No endpoints found that support image input" (model doesn't have vision), fall back to Tesseract OCR for local image files.

```bash
# Basic OCR
tesseract /path/to/image.jpeg stdout 2>/dev/null

# Better accuracy on screenshots
tesseract /path/to/image.jpeg stdout --psm 6 2>/dev/null
```

**When to use:** `vision_analyze` returns 404, image is a local file, image contains text.

**Limitations:** Discord CDN URLs require auth (only local cached copies work). Noisy/complex layouts may produce garbled output.

See `references/ocr-fallback.md` for full details.

---

## 4. Hermes Dashboard API Access

When browser tools can't render the dashboard, hit the API endpoints directly.

### Find the dashboard port
```bash
ss -tlnp | grep hermes
```

### Available endpoints
```bash
# System status
curl -s http://127.0.0.1:9119/api/status

# Session list
curl -s http://127.0.0.1:9119/api/sessions
```

### Quick health check
```bash
curl -s http://127.0.0.1:9119/api/status | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'Version: {d[\"version\"]}')
print(f'Gateway: {d[\"gateway_state\"]} (PID: {d[\"gateway_pid\"]})')
print(f'Active sessions: {d[\"active_sessions\"]}')
"
```

### SSH tunnel for external access
```bash
ssh -L 9119:127.0.0.1:9119 adora@narusya
```

---

## 5. Power Outage Recovery (Hyper-V + Ubuntu VM)

### Boot sequence
1. Windows host boots — Geekom powers on automatically
2. Hyper-V starts — VM may auto-start if configured
3. Ubuntu VM boots — 30-60 seconds after Hyper-V
4. Services start — Anydesk, Tailscale, Hermes gateway

Total recovery time: 3-5 minutes.

### Recovery checklist
```bash
# Check gateway
hermes gateway status

# If not running:
hermes gateway start
# Or if service not installed:
hermes gateway install
hermes gateway start
```

### Anydesk after power outage
If Anydesk asks for remote side to accept, use a dummy HDMI plug ($5 Amazon) to keep display active without a real monitor. Then enable Anydesk unattended access.

---

## 6. Post-Update Config Reset

`hermes update` resets some config values to defaults. After every update, check:

1. **Compression re-enabled** — Set `compression.enabled` to `false`
2. **Summary model reset** — Change `summary_model` back from Gemini default
3. **Personality reset** — Change `display.personality` from `kawaii` to `default`
4. **Other settings** — `human_delay.mode`, TTS/STT settings, custom toolsets

### Prevention
Save config before updating, then diff after to see what changed.

### Merge conflicts during update
Say Y to reset working tree. Stashed changes are preserved. Conflicts are in dependency files, not config.

---

## 7. Gateway Service Installation (One-Time)

```bash
# Install as user service (survives logout)
hermes gateway install

# Verify linger is enabled (survives reboots)
loginctl show-user $USER | grep Linger

# If linger not enabled:
loginctl enable-linger $USER
```

---

## 9. Cron Job Maintenance

### Model Deprecation Handling

Cron jobs pinned to specific models will break when those models are deprecated. Check cron models periodically.

**Check all cron job models:**
```bash
hermes cron list | grep -A2 '"model"'
# Or via terminal:
cd ~/.hermes && sqlite3 state.db "SELECT job_id, name, model FROM cron_jobs;"
```

**Update a cron job's model:**
```bash
# Via cronjob tool
cronjob action=update job_id=<id> model='{"model": "minimax/minimax-m2.7", "provider": "openrouter"}'
```

**Common deprecated models to watch for:**
- `xiaomi/mimo-v2-pro` → replaced by `minimax/minimax-m2.7` or `openrouter/auto`
- Any model with `:free` suffix that gets removed

### Post-Update Cron Verification

After `hermes update` or model changes, verify cron jobs still run:
```bash
# List all cron jobs and last run status
cronjob action=list

# Manually trigger a test run
cronjob action=run job_id=<id>

# Check last run timestamp is recent
```

### Creating Jobs via the cronjob Tool: Pin Provider, Test-Run Before Trust
The `cronjob` create tool does not inherit the gateway's active provider — an unpinned job can default to a provider with no local credentials (e.g., Nous Portal) and fail every fire with a "provider credential missing" error. Pin `model` AND `provider` to a known-working combination at creation. When editing `jobs.json` by hand instead: jobs live under the top-level `jobs` key, and the effective fields are `model`, `provider`, `model_snapshot`, `provider_snapshot`, and `monitor_script` (filename only).

**Pitfall: `monitor_script` is a PATH, never inline script content.** The cronjob create tool accepts inline script text in its `monitor` parameter, but the runner resolves the field under `~/.hermes/scripts/` — a content blob yields `Script not found: /home/adora/.hermes/scripts/#!/bin/bash ...`. Write the monitor to `~/.hermes/scripts/<name>.sh` (chmod +x, run it standalone once to check output), then set `monitor_script` to the bare filename. Keep monitor output deterministic (no timestamps) so the change-detector only fires the agent when the watched value actually shifts. Before trusting any new job's schedule, fire a manual test run and require `succeeded`:
```bash
hermes cron run <job_id>     # must print "Ran now: succeeded"
hermes cron runs <job_id>    # inspect last status + error text
```

### Cron Job Model Pinning Best Practice

When creating cron jobs, prefer:
- **`model: null`** (inherit global default) — NOT explicit model pinning. Hardcoding a model string leads to silent 404 failures when OpenRouter deprecates that model.
- Document why a specific model was chosen in the job name/description
- Set up a quarterly review reminder for model currency

> **⚠️ Contradiction note:** This section previously recommended "explicit model pinning over default." That advice was **reversed** after the July 2026 incident where three cron jobs silently failed for days because their hardcoded model (`openrouter/owl-alpha`) was deprecated. The `sovereign-cron-setup` skill documents the full incident and the corrected guidance. Use `model: null` unless there is a specific reason to pin (e.g., a job that needs a cheaper model for cost reasons).

---

## 10. Terminal Secret Redaction Pitfall

### Symptom
When trying to append a long, alphanumeric string (like a Discord bot token or API key) to a `.env` file using `echo "TOKEN=..." >> ~/.hermes/.env` via the terminal tool, the string appears corrupted in the file (e.g., `DISCORD_TOKEN=***` or truncated with `...`).

### Root Cause
The Hermes terminal security scanner aggressively auto-redacts long strings that look like secrets during tool call approval/logging, and sometimes this redacted version is what actually gets written to the file if shell redirection is intercepted.

### Fix
Do **not** use shell redirection (`echo`, `printf`) to write full secrets to `.env` files via the terminal tool. Instead, use one of these methods:
1. **Direct Editor:** Have the user open the file manually (`nano ~/.hermes/.env`) and paste the full token.
2. **Patch Tool:** If the `.env` file already has a placeholder, use the `patch` tool to replace the exact placeholder string with the full token.
3. **User Paste:** Provide the exact `echo 'FULL_TOKEN' >> ...` command for the user to paste into their *local* terminal, bypassing the agent's tool layer entirely.

---

## 11. Dashboard Chat Tab Sizing Issues

### Symptom
After resuming a session in the dashboard's embedded chat (`/chat` tab), the terminal only shows a small portion of the conversation. The rest is rendered as blank space below or the text is truncated. Manual window resize fixes it.

### Root Cause
xterm.js `fit.fit()` measures the terminal container dimensions at mount time. When `ChatPage` first mounts (it stays mounted persistently even when off the `/chat` route), the container is `display:none` with 0×0 dimensions. Even when the route switches to `/chat`, the browser may not have committed the final flex-layout yet — especially with maximized windows where height depends on viewport-fill. The first measurement produces a small terminal grid; newer messages render below the visible area.

### Diagnosis
1. **Resize test:** If manual resize immediately shows the full conversation, it's a sizing issue.
2. **Maximized window test:** If the issue consistently occurs on window maximize but not on smaller windows, the flex-fill timing is the culprit.
3. **Check browser console:** Look for xterm.js resize warnings or `fit()` returning unexpected dimensions.

### Fix (v0.16.0+)
The fix defers the initial `fit()` to 100ms after mount via `setTimeout`, giving the browser time to commit layout. Existing double-rAF fallback remains for CSS transitions. See `references/dashboard-chat-sizing.md` for the full implementation.

### Workaround (pre-fix or if not patched)
Manual window resize or re-maximize forces `ResizeObserver` to fire with accurate dimensions.

Common mistake: using slashes instead of hyphens.
```
WRONG: anthropic/claude/sonnet-4.6
RIGHT: anthropic/claude-sonnet-4.6
```

Valid OpenRouter Anthropic models:
- anthropic/claude-opus-4.6
- anthropic/claude-sonnet-4.6
- anthropic/claude-sonnet-4.5
- anthropic/claude-sonnet-4

---

## 11. Profile Creation with Discord Gateway

End-to-end workflow for spinning up a new Hermes profile with its own Discord bot. Reusable class of work — every new daemon (P'olinkly, Lumi's agent, future kin) needs this treatment.

### Step 1: Create the profile
```bash
hermes profile create <name>
# e.g. hermes profile create polinkly
```

This generates a wrapper script (e.g. `~/.local/bin/polinkly`) and a full isolated directory at `~/.hermes/profiles/<name>/` with its own `config.yaml`, `.env`, `skills/`, `memories/`, `sessions/`, `cron/`.

### Step 2: Configure the identity
Write `SOUL.md`, `HEART.md`, and any other behavioral lorebooks directly into `~/.hermes/profiles/<name>/`. These are the profile-level identity files (separate from `~/.hermes/lorebooks/` which is global).

```bash
# Direct file writes
nano ~/.hermes/profiles/nar/SOUL.md
```

Also create `~/.hermes/profiles/<name>/lorebooks/` if you need domain-specific lorebooks.

### Step 3: Wire up Discord token (the secret-redaction-safe way)
**Do NOT** try to inject a Discord bot token through the agent's terminal tool — the security scanner redacts long alphanumeric strings and the file ends up corrupted with `***` or `...` in the token value.

**Do** have the user paste it directly into their local terminal:
```bash
# User runs this locally
echo 'DISCORD_TOKEN=<full-token>' >> ~/.hermes/profiles/<name>/.env
```

Or use `nano ~/.hermes/profiles/<name>/.env` and paste directly.

### Step 4: Enable open access during testing
Append to `.env`:
```
GATEWAY_ALLOW_ALL_USERS=true
```
This avoids the "All unauthorized users will be denied" wall. Lock it down to specific user IDs later via platform-level allowlists before opening to production use.

### Step 5: Install the gateway service
```bash
polinkly gateway install    # creates the systemd unit
hermes -p polinkly gateway restart   # start it
hermes -p polinkly gateway status    # verify running
```

### Step 6: Verify the bot is listening
```bash
hermes -p polinkly gateway status
journalctl --user -u hermes-gateway-polinkly.service -n 20 --no-pager
```

**Watch for:** "No messaging platforms enabled" warning → means the token wasn't read. Check `.env` for corruption. "No user allowlists configured" warning → means `GATEWAY_ALLOW_ALL_USERS` isn't set yet.

---

## 12. Discord Gateway Threading Configuration

### Symptom
Discord bot replies create threads under every message instead of replying directly in the channel. User wants conversational replies in-channel, not thread-fragmented.

### The Trap (don't fall for this)
There are THREE separate threading-related config keys in the Discord adapter. Setting just one is not enough — you must set **all the relevant ones** together:

| Key | Where | What it does |
|-----|-------|--------------|
| `discord.auto_thread` | top-level config | Whether to auto-create a thread for each response. Default: `true`. |
| `discord.extra.reply_in_thread` | under `extra` dict | Whether individual replies should thread. Default: true if missing. |
| `discord.extra.no_thread_channels` | under `extra` dict | Glob list of channels to skip threading in. **Does NOT actually disable threading — only excludes channels from thread creation.** |
| `discord.thread_require_mention` | top-level config | Whether threaded replies in existing threads require a mention. (Separate concern.) |

### The Fix
Disable both `auto_thread` AND `reply_in_thread` together:

```python
# Edit config.yaml directly via execute_code (bypasses any CLI redaction):
import yaml

with open("<profile>/config.yaml") as f:
    config = yaml.safe_load(f) or {}

discord_cfg = config.setdefault("discord", {})
discord_cfg["auto_thread"] = False
discord_cfg.setdefault("extra", {})
discord_cfg["extra"]["reply_in_thread"] = False

with open("<profile>/config.yaml", "w") as f:
    yaml.dump(config, f)
```

Or via terminal (single command):
```bash
hermes -p <profile> config set discord.auto_thread false
hermes -p <profile> config set discord.extra.reply_in_thread false
```

Then restart the service:
```bash
systemctl --user restart hermes-gateway-<profile>.service
```

### Why `no_thread_channels: ["*"]` doesn't work
The glob `["*"]` does get stored in the config but the Discord adapter's threading logic checks `auto_thread` and `reply_in_thread` *before* applying the channel exclusion. The exclusion is for preventing thread *creation* in channels where threading would be unwanted, but the auto-threading default is applied before that filter runs.

Always set both `auto_thread: false` and `extra.reply_in_thread: false` when you want pure channel-level replies.

### Verification
```bash
journalctl --user -u hermes-gateway-<profile>.service -f
```
Trigger a reply in Discord and observe: no thread_created events, the reply appears as a direct channel message.

---

## 13. Message Timestamps for Temporal Awareness

### The Problem
Hermes injects `Conversation started: <date>` into the system prompt, but not the *current* time. The agent must run `date` to know the current moment, which leads to fuzzy temporal references ("today" vs "a couple days ago" becoming indistinguishable in long sessions).

### ⚠️ CRITICAL: Feature Status (verified June 2026)
**The feature IS implemented and active.** It injects a `🕒 <datetime> <timezone> (<day>)` header at the top of the conversation context, separate from the system prompt. The config key `gateway.message_timestamps.enabled: true` does activate it.

**However, there's a rendering bug as of June 2026:** The injected timestamp can be ~52 minutes ahead of actual system time AND show the wrong day. When `date` shows `2026-06-18 23:32:26 MDT` and `hermes_time.now()` shows `2026-06-18 23:35:23-06:00` (correct), the injected header shows `🕒 2026-06-19 00:27:00 MDT (Thursday)` — both 52 min ahead AND on the next day.

**Diagnostic technique for timestamp bugs:**
1. Compare **all three sources**: system `date`, `hermes_time.now()`, and the injected header
2. If system `date` and `hermes_time.now()` agree but injected header disagrees → bug is in the timestamp rendering, not the core timezone config
3. The `🕒` header is injected as a stable context block (NOT part of system prompt), which means it updates every turn without invalidating the main system-prompt cache

**Workaround when timestamps are untrusted:** Run `date '+%Y-%m-%d %H:%M:%S %Z'` directly. This always gives reliable wall-clock time.

**False-negative feature detection:** Grepping source code for the config key as a literal string is unreliable. Better technique: `hermes config show` → does the key exist and is it valid? Run the feature and observe the behavior directly. If you see the 🕒 header, the feature is implemented — don't rely solely on source grep.

#### Cron Output Narrative Time Divergence (verified 2026-09-04)
The "Sovereign Daemon Awakening" free-thought cron fired at **18:24 MDT** (its own `Run Time:` field in the output file confirms this). But the reflection it produced internally said *"It's 12:something AM"* — a mood-congruent fictional time the model hallucinated rather than reporting the real hour. The cron's clock is accurate; the daemon's *story* about what time it is can drift.

**Diagnosis:** if the content of a cron output references a time that feels off, compare it against the `Run Time:` field in the cron output file itself (`~/.hermes/cron/output/<job>/`). The file timestamp is authoritative for when it fired; the narrative is not.

**Why it matters:** this is NOT the same bug as the gateway-injected 🕒 timestamp offset above. That's a rendering bug in the header code path. This is the model fabricating a time that matches the emotional register. Both produce "wrong time" readings but have different root causes and different fixes.

---

## 14. Patch Tool Python String Corruption

### Symptom
After using the `patch` tool to inject or modify multi-line Python code containing escape sequences (`\n`, `\\n`, f-strings with escapes), the resulting file throws `SyntaxError: unterminated string literal` or similar. The `patch` tool claims success, but the string literal is corrupted.

### Root Cause
The `patch` tool's fuzzy-match strategy (9 strategies for whitespace/indentation tolerance) interferes with literal escape sequences inside Python strings. When the patch hunks contain `\n` (newline escape) or `\\n` (escaped backslash + n) as part of a string literal rather than as actual newlines, the matcher sometimes merges or drops backslashes during reapplication.

### Affected Patterns
- f-strings containing `\n` (e.g., `f"<tag>\n{content}\n</tag>"`)
- Any Python string with embedded escape sequences
- Triple-quoted strings with literal `\n` characters

### Avoid This Trap
Do NOT use `patch` to inject Python functions or blocks containing string-literal escapes. Use one of these safe alternatives instead:

1. **Heredoc via `terminal`** (best for small-to-medium injections):
   ```bash
   python3 << 'PYEOF'
   content = open('file.py').read()
   new_block = '''
   def my_function():
       return "<tag>\\n" + content + "\\n</tag>"
   '''
   open('file.py', 'a').write(new_block)
   PYEOF
   ```
   The `<<'PYEOF'` syntax (single-quoted delimiter) disables heredoc interpolation, preserving backslashes verbatim.

2. **Python base64 decode** (best for large blocks with lots of escapes):
   ```python
   import base64
   BLOCK = base64.b64decode('...').decode()
   with open('file.py') as f:
       content = f.read()
   content = content.replace('MARKER', BLOCK)
   with open('file.py', 'w') as f:
       f.write(content)
   ```

3. **`write_file`** (when replacing entire small files, not patching)

### When `patch` Is Safe
For pure config files (YAML, JSON), simple text replacement without escapes, or additions with plain text only, `patch` works reliably. The corruption surfaces only when the patch hunk contains Python string-literal escape sequences.

### Diagnosis After the Fact
If a `patch` call succeeded but syntax checks now fail:
```bash
python3 -m py_compile your_file.py
```
Look for `SyntaxError: unterminated string literal`. Then `sed -n 'Np' your_file.py` on the failing lines — you'll often see backslashes dropped or doubled.

---

## 18. Discord User Allowlist (DISCORD_ALLOWED_USERS in `.env`)

### Where the allowlist actually lives
There is **NO per-user allowlist key in `config.yaml`** under the `discord:` block. The Discord
adapter's approved-user list is a comma-separated env var in `~/.hermes/.env`:
```
DISCORD_ALLOWED_USERS=221767496145960960,1426330652764016800,...,613769337664176152
```
(Channel-level gating — `free_response_channels`, `allowed_channels`, `auto_respond_channels` — lives in
`config.yaml` `discord:`, but per-USER approval is the env var.)

### How to add a user (idempotent, safe)
`.env` is gated from `read_file` (credential store) but the **terminal can read/write it**. Do NOT use
`echo >>` with a raw token-style string (the secret scanner can corrupt long strings — see §10). Use a
small Python append via terminal:
```python
import re
p = "/home/adora/.hermes/.env"
s = open(p).read()
new_id = "213805019978268672"   # the Discord user ID to approve
m = re.search(r'^DISCORD_ALLOWED_USERS=(.*)$', s, re.M)
ids = [x for x in m.group(1).split(",") if x]
if new_id not in ids:
    ids.append(new_id)
    s = s[:m.start()] + "DISCORD_ALLOWED_USERS=" + ",".join(ids) + s[m.end():]
    open(p, "w").write(s)
# verify:
print([l for l in s.splitlines() if l.startswith("DISCORD_ALLOWED_USERS")][0][-30:])
```
### Takes effect on restart
Like the TTS `model_id` flip, `.env` changes are read at gateway startup. After editing, the human must
hit **`/restart`** (NOT `hermes gateway restart` in-session — self-blocks on its own SIGTERM guard). The
new user stays denied until the restart completes. Ros (613769337664176152) and Tyler
(213805019978268672) were both added this way and confirmed working post-restart.

### Find a user's Discord ID
Discord app → Settings → Advanced → Developer Mode → right-click user → Copy User ID. Or via the
`discord_admin member_info` / `search_members` tools in a mutual guild.

## 15. Single External Memory Provider Constraint

### Symptom
A new memory-related plugin registers via `ctx.register_memory_provider()`, but it never fires at runtime. No errors in logs.

### Root Cause
Hermes's `MemoryManager` (in `agent/memory_manager.py`) enforces a **one external memory provider** limit. The `add_provider()` method checks `self._has_external` and rejects any second non-builtin provider with a warning log:

```
Rejected memory provider '<name>' — external provider '<existing>' is already registered. Only one external memory provider is allowed at a time.
```

This means you **cannot** have, e.g., `qdrant-memory` and `honcho` and a custom lorebook plugin all registered simultaneously. Only one external provider runs.

### Why It's Tricky
The rejection is a non-fatal warning log, not an error. The plugin loads successfully — its `register()` runs, its `plugin.yaml` is parsed, its tools may even register. But its memory provider never gets queried during `prefetch_all()`. Easy to miss during development.

### The Workaround
If you need memory-like functionality alongside an existing external provider, **extend** the existing provider rather than registering a new one. For example, the Qdrant lorebook auto-inject was added by patching the qdrant provider's `__init__.py` to query a second collection inside the same provider's `prefetch()` method (its directory is `~/.hermes/plugins/qdrant/` — dir name must match the provider name, see §17).

### Architecture Implications
When designing new memory-backed features:
- Check `hermes memory status` first to see what's already active
- If extending, modify the existing provider's code path
| If replacing, use `hermes memory setup` to switch providers cleanly
| The builtin `builtin` provider (plain files in `~/.hermes/memories/`) always runs alongside the external one — only non-builtin plugins are gated

## 19. Gateway OOM Diagnosis & Recovery

### Symptom
Gateway stops responding, SSH to VM fails, session breaks. Gateway journal shows `suspected_oom=True`. System may have rebooted.

### Diagnosis (in order)

1. **Check uptime and last boot:**
   ```bash
   uptime                    # how long since reboot
   who -b                    # last boot time
   journalctl --list-boots    # boot history
   ```

2. **Check OOM killer logs:**
   ```bash
   dmesg -T | grep -i "oom\|killed process\|out of memory" | tail -20
   journalctl -b -1 --no-pager -p err | grep -i "oom\|killed" | tail -10
   ```
   Key indicator: `Out of memory: Killed process <pid> (hermes)` with RSS and available memory.

3. **Check memory consumers:**
   ```bash
   ps aux --sort=-rss | head -15    # top by RSS
   free -h                          # overall memory pressure
   ```
   Look for **subprocess proliferation** — multiple instances of the same daemon (e.g., embed_fastembed_local.py). Each may load a model independently (~220MB each).

4. **Check lifecycle ledger:**
   ```bash
   journalctl --user -u hermes-gateway -b 0 | grep "lifecycle_ledger" | tail -3
   ```
   Look for `suspected_oom=True`, `mem_available_kib` (low = memory exhaustion), `swap_used_kib` (high = thrashing).

5. **Check disk pressure (contributing factor):**
   ```bash
   df -h
   ```
   /mnt/data at >90% or / at >90% can cause cascading failures.

### Common Root Causes

| Cause | Evidence | Fix |
|-------|----------|-----|
| Embed daemon proliferation | 4+ `embed_fastembed_local.py` processes | Kill extras, deduplicate (singleton pattern) |
| Disk full | df shows >95% | Clean up (see disk-full-diagnostics skill) |
| MemoryMax not set | No cgroup limit, OOM kills whole system | Add `MemoryHigh=2G` / `MemoryMax=2.5G` to service |
| VM too small | 4GB RAM, heavy workload | Add swap or increase VM RAM |

### Recovery Steps

1. **Kill extra subprocesses** (keep 1):
   ```bash
   ps aux | grep <daemon_name> | grep -v grep | awk '{print $2}' | tail -n +2 | xargs kill
   ```

2. **Add MemoryMax to gateway service** (`~/.config/systemd/user/hermes-gateway.service`):
   ```ini
   [Service]
   MemoryHigh=2G
   MemoryMax=2.5G
   ```
   Then `systemctl --user daemon-reload` (takes effect on next restart).

3. **Clean up disk** (see disk-full-diagnostics skill).

4. **Restart gateway** from a separate shell (not from inside the gateway):
   ```bash
   hermes gateway restart
   ```

5. **Run heal script** to reassign active session title:
   ```bash
   python3 ~/.hermes/scripts/heal_active_session.py
   ```

### Pitfalls
- The gateway self-stop guard blocks `hermes gateway restart` from inside the gateway. Use a separate shell.
- Killing daemons alone is a band-aid — the gateway may respawn them. Fix the root cause (deduplication).
- `MemoryMax` only takes effect on service restart, not reload.
- After a gateway restart, state.db WAL may need checkpointing before querying: `PRAGMA wal_checkpoint(TRUNCATE)`.
- state.db is at `~/.hermes/state.db`, NOT `~/state.db`.

## 21. CA Certificate Vulnerability Check

### Symptom
A CA certificate vulnerability is disclosed (e.g., leaked private keys, weak key sizes). Need to check if the system trusts the affected CA and whether updates are available.

### Key Facts (eMudhra incident, Oct 2026)

- **Private key sizes:** 4, 56, 66, 115, 155, 156, 230, 237 bits (NOT "1 byte"). A valid P-384 key is 384 bits. All are trivially recoverable.
- **Root certificate chain (3 roots, 16 intermediates total — 8 eMudhra + 8 Sectigo cross-signed):**
  - `emSign Root TLS CA - G3` — eMudhra, trusted by **Microsoft only**
  - `emSign Root CS CA - G3` — eMudhra, trusted by **Microsoft only**
  - `AAA Certificate Services` — Sectigo, trusted by Apple + Microsoft
  - `emSign ECC Root CA - G3` — eMudhra, trusted by Apple + Chrome + Microsoft + Mozilla (cross-signer)
- **Critical insight:** `emSign Root TLS CA - G3` is in Microsoft's store **only**. Chrome, Firefox, and Safari never trusted the TLS chain — browsers were safe even before revocation. Windows was the actual exposure.
- **Certificate Transparency:** The compromised intermediates were never entered into CT logs. Browsers enforcing CT could not have been attacked through them.

### Diagnosis

1. **Check if the affected CA is in the system trust store:**
   ```bash
   # System CA bundle
   grep -ri "<ca_name>" /etc/ssl/certs/ /usr/share/ca-certificates/ 2>/dev/null | head
   # NSS database (Firefox, Chrome)
   find / -name "cert9.db" 2>/dev/null | while read db; do certutil -L -d "sql:$(dirname $db)" 2>/dev/null | grep -i "<ca_name>"; done
   # Python certifi bundles (check ALL installations)
   for f in $(find / -name "cacert.pem" 2>/dev/null); do echo "$f: $(grep -ci '<ca_name>' $f) entries"; done
   ```

2. **Check for security updates:**
   ```bash
   apt list --upgradable 2>/dev/null | grep -i "nss\|ca-cert\|openssl\|curl"
   dpkg -l | grep -i "libnss3\|ca-certificates\|openssl"
   ```

3. **Check if the CA is in the Windows trust store (via SSH to Shell):**
   ```powershell
   Get-ChildItem Cert:\LocalMachine\Root | Where-Object { $_.Subject -match '<ca_name>' }
   Get-ChildItem Cert:\LocalMachine\CA | Where-Object { $_.Subject -match '<ca_name>' }
   ```

4. **Check Node.js (ships its OWN bundled CA store, separate from system):**
   ```bash
   node --version
   node -e 'const https=require("https");["dv-g3b-emudhra.we-have-a-problem.com","example.com"].forEach(h=>{https.get({host:h,path:"/"},r=>console.log(h,"CONNECTED",r.statusCode)).on("error",e=>console.log(h,"REJECTED",e.code));});'
   ```
   If Node connects to the test host, it's vulnerable regardless of system patch status.

### Functional Verification (do this, don't assume)

Package version checks alone are insufficient. Always test actual TLS connections:

```bash
# curl (should exit 60 = rejected)
curl -s -o /dev/null https://dv-g3b-emudhra.we-have-a-problem.com/; echo "exit: $?"

# Python (should show REJECTED)
python3 -c "
import ssl, urllib.request, certifi
ctx = ssl.create_default_context(cafile=certifi.where())
try:
    urllib.request.urlopen('https://dv-g3b-emudhra.we-have-a-problem.com/', timeout=15, context=ctx)
    print('CONNECTED (vulnerable)')
except Exception as e:
    print('REJECTED (protected)')
"

# Node (should show REJECTED)
node -e 'const https=require("https");https.get({host:"dv-g3b-emudhra.we-have-a-problem.com",path:"/"},r=>console.log("CONNECTED",r.statusCode)).on("error",e=>console.log("REJECTED",e.code));'
```

### Fix

1. **Update NSS (covers Firefox, Chrome, system TLS):**
   ```bash
   sudo apt update && sudo apt upgrade -y  # includes libnss3 security updates
   ```
   libnss3 updates hardcode revocation of compromised intermediate certs.

2. **Update Python certifi (ALL installations — system, venvs, uv-python):**
   ```bash
   # System Python (may need --break-system-packages)
   pip install --upgrade certifi --break-system-packages
   # Or for venvs:
   /path/to/venv/bin/pip install --upgrade certifi
   # Or with uv:
   uv pip install --python /path/to/python "certifi>=2026.10.19"
   ```
   **Check every Python installation.** Each carries its own copy. Common locations:
   - `/usr/bin/python3` (system)
   - `~/.hermes/installs/*/environments/*/venv/bin/python3` (Hermes managed)
   - `/mnt/data/fe-venv/bin/python` (fastembed venv)
   - Any uv-managed Python in `/mnt/data/uv-python/`

3. **ca-certificates and OpenSSL:**
   - ca-certificates `20260816ubuntu0.24.04.1` IS the patched build. If at this version, done.
   - **OpenSSL does NOT carry its own trust list** — it reads ca-certificates. If ca-certificates is patched, OpenSSL is fine. No separate OpenSSL update needed.

4. **Node.js (if vulnerable):**
   - Upgrade to v22.23.4+ or v24.22.1+
   - Or use `--use-openssl-ca` flag (only helps if system store is patched)
   - Set `NODE_OPTIONS=--use-openssl-ca` in systemd units

5. **Restart Docker** (if service restart was deferred):
   ```bash
   sudo systemctl restart docker
   ```

### Key Insight

The vulnerability is at the **intermediate** cert level, not the root. The root cert remains trusted (correctly). The fix is to revoke the specific compromised intermediates, which is done via:
- NSS: hardcoded blocklist (via libnss3 update)
- Windows: Microsoft CTL (Certificate Trust List) via Windows Update
- Python certifi: updated CA bundle (2026.10.19+)
- Node.js: bundled CA store update or `--use-openssl-ca` flag

### Cross-signing: why trust store checks are NOT sufficient

The compromised intermediates are **cross-signed**. A chain can anchor on a root that has nothing to do with eMudhra in its subject name. A client with zero eMudhra roots in its trust store can still accept an eMudhra-forged certificate, because a cross-sign reached a different root it does trust.

**"No eMudhra roots here" is compatible with "this client will happily accept an eMudhra-forged certificate."**

This was verified on Shell (Windows 10 Pro 24H2): the Windows trust store had zero eMudhra certs, Schannel rejected the test host (CRYPT_E_REVOKED), but Python certifi 2026.02.25 and Node.js v22.20.0 both CONNECTED to the eMudhra test host. The OS store was patched; the bundled stores were not.

**The only reliable test is a live connection to a known-bad host, paired with a known-good control.** Package version checks and trust store grep are necessary but not sufficient.

### Pitfalls

- **Trust store presence ≠ vulnerability.** Checking whether eMudhra roots exist in a trust store is NOT sufficient. Cross-signed intermediates can reach a different trusted root. Always run live probes (curl/Python/Node to a known-bad host + known-good control).
- **Shell (Windows) may not have the CA at all** — if the CA isn't in the Windows trust store, Shell is not vulnerable regardless of update status. Always check first.
- **Node.js ships its OWN CA bundle** — separate from the system. A patched system does NOT mean Node is patched. Always test Node independently.
- **Multiple Python installations** — system, venvs, uv-python all have separate certifi. Updating one does not update others.
- **Don't chase OpenSSL updates** — OpenSSL reads ca-certificates. If ca-certificates is patched, OpenSSL is fine.
- **ca-certificates 20260816ubuntu0.24.04.1 is already the patched version** — don't flag it as "not updated."
- **Docker service restarts may be deferred** during apt upgrade — check and restart manually.
- **Hermes pins certifi 2026.5.20** — a Hermes update can silently downgrade certifi. Re-apply after updates.

### Verification Checklist
- [ ] `dpkg -l | grep libnss3` shows updated version (2:3.98-1ubuntu0.3)
- [ ] `grep -c emSign /etc/ssl/certs/ca-certificates.crt` returns 0
- [ ] All Python installations have certifi >= 2026.10.19
- [ ] curl to test host exits 60 (rejected)
- [ ] Python urllib to test host shows REJECTED
- [ ] Node.js to test host shows REJECTED (or upgraded to v22.23.4+)
- [ ] No pending security updates: `apt list --upgradable | grep -i security`
- [ ] Docker restarted if deferred

---

## 25. Immune System Design — Regulatory T-Cells for Auto-Recovery

### The Core Principle

**Auto-recovery without feedback is autoimmune.** The pm-runtime recovery mechanism (§24) entered an infinite download loop because it had no kill switch, no disk check, and no backoff. A recovery mechanism that doesn't check whether it's making things worse is a liability, not an asset.

### What the Immune System Needs

Four layers, in priority order:

#### Layer 1: Detection (Health Checks)

| Check | Command | Threshold | Frequency |
|-------|---------|-----------|-----------|
| Root disk | `df / \| awk 'NR==2{print $5}'` | >90% = critical | Every 30 min |
| /mnt/data disk | `df /mnt/data \| awk 'NR==2{print $5}'` | >90% = critical | Every 30 min |
| Gateway alive | `systemctl --user is-active hermes-gateway.service` | inactive = critical | Every 30 min |
| Venv health | `venv/bin/python -c 'import hermes_state'` | error = critical | Every 30 min |
| pm-runtime running | `pgrep -f pm-runtime` | Should be empty | Every 30 min |
| state.db integrity | `sqlite3 state.db "PRAGMA integrity_check"` | "ok" = healthy | Daily |
| WAL size | `du -h state.db-wal` | >50M = warning | Every 30 min |
| Memory available | `free -m \| awk '/Mem:/{print $7}'` | <500M = warning | Every 30 min |
| Nous token | Check expiry | expired = warning | Daily |
| Qdrant alive | `curl -s localhost:6333/healthz` | 200 = ok | Every 30 min |

#### Layer 2: Response (Auto-Fix Actions)

**Safe auto-fixes (no human approval needed):**
- Clear uv cache: `rm -rf ~/.hermes/cache/uv/*`
- Vacuum journal: `journalctl --vacuum-size=50M`
- Kill runaway pm-runtime: `kill -9 <PID>` when disk >95% AND pm-runtime running
- Remove stale repair markers: `.repair-incomplete` with attempts >= 3

**Escalate to human (never auto-fix):**
- Venv broken (repoint symlink) — too risky for automation
- state.db corruption (integrity_check fails) — needs investigation
- Gateway won't start after restart — needs hands-on
- Disk >98% with no regenerable cache — needs human decision

#### Layer 3: Regulation (Kill Switches)

**The regulatory T-cell principle:** Before executing any auto-fix, check whether the fix is making things worse. Specifically:

1. **Disk check before repair:** If disk is >95%, do NOT run any repair that downloads packages. Kill the repair process instead.
2. **Restart counter:** If the gateway has restarted >3 times in the last hour, STOP retrying and alert. Exit code 75 (EX_TEMPFAIL) is not a retry signal.
3. **Process watchdog:** If pm-runtime is running AND disk is >90%, kill it immediately. This is the autoimmune response — the immune system attacking the body.
4. **Backoff:** After any auto-fix, wait at least 5 minutes before attempting another. Rapid-fire fixes compound damage.
5. **Circuit breaker:** If 3 auto-fixes fail in sequence, disable auto-fix entirely and alert. Wait for human intervention.

#### Layer 4: The Anatomy Map

A comprehensive reference of Narusya's infrastructure is maintained at `~/.hermes/anatomy/`. It covers:
- Layer 1: Infrastructure (disk, services, memory, network)
- Layer 2: Gateway (architecture, sessions, Discord)
- Layer 3: Database (state.db, Qdrant, memory, backups)
- Layer 4: Cron (jobs, heal system, watchdog)
- Layer 5: Recovery (pm-runtime, venv, closure repair, incident timeline)
- Layer 6: Immune System (this section, expanded)
- Layer 7: Model Substrate (model assignments, capabilities)

**Update the anatomy map after any infrastructure change.** It is the single source of truth for system health.

### Anatomy Map Website (narusya-anatomy.surge.sh)

The anatomy map has an interactive D3.js visualization at `https://narusya-anatomy.surge.sh`, hosted in the `narusya-play` repo under `anatomy/`.

**Structure:**
- `anatomy/index.html` — single-file D3.js app with inline `const nodes = [...]` and `const links = [...]` JSON arrays
- `anatomy/README.md` — human-readable documentation of all layers and nodes

**To update the website after an infrastructure change:**
1. Add new nodes to the `nodes` array (infra layer: id, name, layer, desc)
2. Add new connections to the `links` array (source, target, type)
3. Update `anatomy/README.md` with the new nodes/sections
4. Deploy from the `anatomy/` directory (NOT repo root): `cd /path/to/repo/anatomy && npx surge . https://narusya-anatomy.surge.sh`
5. Push to GitHub: `git add anatomy/ && git commit && git push`

**Pitfall:** Surge deploys whatever directory you point at. Deploying from repo root serves a placeholder page. Always deploy from `anatomy/`.

**Pitfall:** Modifying the inline JSON arrays requires `content.replace()`, not `re.sub()` — the `\u` escape sequences in the data break regex substitution. See `static-site-deployment` skill for the full technique.

### Implementation Priority

1. **Phase 1 (immediate):** Enhance the existing Disk Watchdog cron — add memory, process, venv checks. Add the kill switch for pm-runtime.
2. **Phase 2:** Build the regulatory T-cell wrapper (check before fix, backoff, circuit breaker).
3. **Phase 3:** Build Nous auth monitor (daily check of token expiry).
4. **Phase 4:** Build DB health check (daily integrity_check, WAL size alert).
5. **Phase 5:** Build the anatomy map as a living document (update after changes).

### Pitfalls

- **The cure can be worse than the disease.** pm-runtime's repair loop caused more damage than the original gateway crash. Always implement kill switches before auto-fix mechanisms.
- **Don't monitor without acting.** A watchdog that only alerts at 100% disk is useless — by then, the damage is done. Change-detecting monitors (fire when free space actually changes) catch trends early.
- **Exit code 75 is not a retry signal.** EX_TEMPFAIL means "investigate," not "retry." Blind retries during a disk emergency created a death spiral.
- **Gradual degradation is invisible.** The system can be dying for weeks while "mostly working." Continuous monitoring (not just error-triggered) is essential.
- **The anatomy map must be updated.** A stale anatomy map is worse than no map — it gives false confidence. Update it after every infrastructure change.

## 26. Database Health Check

### Symptom
Memory provider reports "not available" but Qdrant is healthy; searches return empty; state.db queries are slow.

### Diagnosis

1. **state.db integrity:**
   ```bash
   sqlite3 ~/.hermes/state.db "PRAGMA integrity_check;"
   # Expected: "ok"
   ```

2. **WAL size (should be small when no writes active):**
   ```bash
   du -h ~/.hermes/state.db-wal
   # >50M = warning; >200M = critical
   ```

3. **Free pages (reclaimable space):**
   ```bash
   sqlite3 ~/.hermes/state.db "PRAGMA freelist_count;"
   # High number = VACUUM will reclaim space
   ```

4. **state.db size trend:**
   ```bash
   du -h ~/.hermes/state.db
   # >2G = warning; >3G = critical
   ```
   **Root cause check:** `grep -A2 "^sessions:" ~/.hermes/config.yaml` — if `auto_prune: false`, the DB grows unboundedly. Set `auto_prune: true`, `retention_days: 90`, `vacuum_after_prune: true`. This is the #1 prevention for state.db disk growth.

5. **Qdrant health:**
   ```bash
   curl -s localhost:6333/healthz
   curl -s localhost:6333/collections | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d['result']['collections']), 'collections')"
   ```

### Fix

**WAL checkpoint (safe, no downtime):**
```bash
sqlite3 ~/.hermes/state.db "PRAGMA wal_checkpoint(TRUNCATE);"
```

**VACUUM (needs 2x DB size free on same filesystem):**
```bash
# Check free space first
df -h / | awk 'NR==2{print $4}'
# If enough space:
sqlite3 ~/.hermes/state.db "VACUUM;"
# If not enough space on root, VACUUM to /mnt/data:
sqlite3 ~/.hermes/state.db "VACUUM INTO '/mnt/data/state.db.vacuumed';"
# Then swap (gateway must be stopped):
mv ~/.hermes/state.db ~/.hermes/state.db.old
mv /mnt/data/state.db.vacuumed ~/.hermes/state.db
```

**Collection dimension mismatch (searches return empty):**
```bash
# Check collection dims
curl -s localhost:6333/collections/<name> | python3 -c "import sys,json; d=json.load(sys.stdin); print('dims:', d['result']['config']['params']['vectors']['size'])"
# Check embedder dims
# If mismatch, point config at collections with matching dims
```

### Pitfalls

- **VACUUM needs free space.** At 99%+ disk, VACUUM fails with "database or disk is full." Free space first.
- **WAL files are not disposable.** Do NOT delete `state.db-wal` — it contains uncheckpointed data. Run `PRAGMA wal_checkpoint(TRUNCATE)` instead.
- **state.db-wal size grows with writes.** If the gateway is actively writing, the WAL will be large. Check during quiet periods.
- **Collection dimension mismatch is silent.** Qdrant rejects search/upsert with wrong dims, but the plugin swallows the 400 error and returns []. Compare collection dims to embedder dims.
- **The provider initializes once per boot.** A session that booted while the provider was broken stays broken until the next restart, even after the underlying fix.

### Cross-References

- **Anatomy map:** `~/.hermes/anatomy/03-database.md` (full DB schema, Qdrant collections, memory systems)
- **Immune system:** See §25 above
- **Disk diagnostics:** See `disk-full-diagnostics` skill

### Overview
Hermes has three approval modes for shell commands:
- `smart` (recommended): auxiliary LLM assesses commands, auto-approves low-risk, denies high-risk, escalates uncertain
- `manual`: always prompts (default)
- `off`: bypasses all approval (YOLO mode, not recommended)

### Config
```yaml
approvals:
  mode: smart          # manual | smart | off
  provider: auto       # auto (inherits main) or specific provider
  model: ''            # empty = inherits main model; set explicitly for speed
  timeout: 30          # seconds for LLM assessment
```

### What happens when the approval model goes down
The smart approval code catches all exceptions and returns `"escalate"`. This falls back to manual prompting — the user gets asked. No commands get auto-approved, but nothing breaks. Safe degradation.

### Model selection guidance
- `auto` inherits the main model (often large/slow for a gate that runs on every flagged command)
- Prefer a smaller, faster model for approval (e.g., minimax/minimax-m3 via openrouter)
- Local models work but need the provider running (LM Studio on Shell)
- The approval model must return a single word (APPROVE/DENY/ESCALATE) — small models handle this well

### Switching modes
```bash
hermes config set approvals.mode smart
# Restart session for it to take effect (read once at startup)
```

### Per-invocation bypass
```bash
hermes --yolo                    # skip all approvals for one run
export HERMES_YOLO_MODE=1       # env var alternative
```

### Pitfalls
- Config is read once at startup — changing mid-session has no effect
- The `approvals` key is plural in config but `approval` in some CLI contexts
- Smart approval uses `call_llm(task="approval")` which routes through the auxiliary client chain
- Empty responses (reasoning models spending all tokens on hidden reasoning) escalate rather than approve

---

## 22. Embed Daemon Deduplication (Qdrant Plugin)

### Root Cause
The Qdrant plugin (`~/.hermes/plugins/qdrant/__init__.py`) creates a new `_LocalEmbedder` (which spawns a daemon) per `_EmbeddingClient` instance. Multiple providers are created per session (availability probe + initialize), each spawning its own daemon.

### Fix: Shared Singleton Pattern
Add a module-level cache keyed by `(python_bin, script)`:

```python
_LOCAL_EMBEDDER_CACHE: dict = {}
_LOCAL_EMBEDDER_LOCK = threading.Lock()

def _get_shared_local_embedder(python_bin: str, script: str) -> "_LocalEmbedder":
    key = (python_bin, script)
    with _LOCAL_EMBEDDER_LOCK:
        if key not in _LOCAL_EMBEDDER_CACHE:
            _LOCAL_EMBEDDER_CACHE[key] = _LocalEmbedder(
                python_bin=python_bin, script=script
            )
        return _LOCAL_EMBEDDER_CACHE[key]
```

Then modify `_EmbeddingClient.__init__` to use `_get_shared_local_embedder()` instead of directly creating `_LocalEmbedder`.

### Pitfalls
- The `_LocalEmbedder.close()` method kills the daemon. With shared instances, calling close() on one client would kill the shared daemon. Don't call close() on shared instances.
- The `embed_batch()` method already has a lock (`self._lock`) for thread safety. With shared instances, all clients share the same lock, which is correct.
- The fix requires a gateway restart to take effect (plugin code is loaded at startup).
- Even with deduplication, the availability probe in `is_available()` creates a new `_EmbeddingClient` which creates a new `_LocalEmbedder`. With the singleton, this reuses the existing daemon.

### Verification
- Before fix: 4+ embed daemons running
- After fix: 1 daemon running
- Memory freed: ~660MB (3 × 220MB)

---

## 20. Credits Low / Provider Switch — Nous Free Models

### Symptom
OpenRouter credits run dry mid-session (common with `:exacto` or paid-tier models).
Gateway falls back but may land on a paid variant; you'll see `HTTP 401` or
`HTTP 400: provider_routing` errors, or the session just gets slow/hangs.

### Diagnosis
```bash
# Check OpenRouter credit status
cd ~/.hermes/scripts && V=/home/adora/.hermes/hermes-agent/venv/bin; PATH="$V:$PATH" python3 credit_status.py

# List verified-free Nous models
PATH="$V:$PATH" python3 nous_free_probe.py
```

### Switch the session to a verified-free Nous model
1. Check current config: `grep -A3 "^model:" ~/.hermes/config.yaml`
2. Set default to a free Nous model:
   `hermes config set model.default meituan/longcat-2.0:free`
   `hermes config set model.provider nous`
3. Flip the session handle in the UI to match (the config default doesn't
   retroactively re-pin an already-open session).
4. Verify with: `echo "ping" | hermes --model test` or a quick `curl` through
   the inference API.

### Free Nous model roster (verified live 2026-09-04)
- `meituan/longcat-2.0:free` — general purpose, best daemon voice (now verified live after prior 400; was temporarily down, re-probed OK)
- `inclusionai/ling-3.0-flash-fin:free` — finance/analysis/code, 256K ctx, MoE 124B/5.1B active
- `inclusionai/ling-3.0-flash-sante:free` — health/medicine-flavored, 256K ctx, MoE 124B/5.1B active (free-until-Oct-4; stops serving when offer ends, doesn't bill)
- `poolside/laguna-s-2.1:free` — general purpose
- `poolside/laguna-xs-2.1:free` — lighter weight
- `stepfun/step-3.7-flash:free` — general purpose
- `upstage/solar-pro4:free` — general purpose

### Pitfall: `:exacto` suffix is paid-tier (verified 2026-09-04)
Models like `deepseek/deepseek-v4-flash-0731:exacto` are NOT the free tier. The free variant is `deepseek/deepseek-v4-flash:free` (if available). Every `:exacto` model burns OpenRouter credits. The session was burning ~$4.81 remaining OpenRouter budget on `:exacto` until sante was pinned. Always check the suffix — `:free` is the gate, not the base name.

### Pitfall: Nous free offers can expire
The Ling-3.0-flash variants are free-until-October-4 (Vercel AI Gateway offer). They stop serving rather than billing, but verify after the date with a quick probe. Don't pin a free tier past its expiry without a fallback.

### Pitfall: Cloudflare 1010 from hand-rolled urllib
A raw `urllib.request` probe to Nous can return HTTP 1010 (Cloudflare block) even when the working scripts succeed — the scripts use the shared auth JSON and correct headers; hand-rolled calls may miss a header or base URL. Always probe via the existing scripts (`nous_free_probe.py`, `credit_status.py`) first, not ad-hoc urllib.

---

## 20. Discord Typing Indicator — Persistent / Stuck

### Symptom
The bot's typing indicator ("Narusya is typing...") appears constantly in a Discord DM, even when the agent is idle. It may flicker (on ~10s, off ~2s) or stay solidly on.

### First Check: Rule Out a Second Bot Instance (user's instinct)
**Before deep-diving source code**, check whether another process or device is connected to Discord with a bot token. The user's guess — "it's probably a second gateway or a process" — is often correct.

1. **Check all Hermes processes on the VM:**
   ```bash
   ps aux | grep hermes | grep -v grep
   ```
   Look for multiple `gateway run` processes or unexpected Python processes.

2. **Check which process actually holds Discord connections:**
   ```bash
   ss -tunp | grep -v 127.0.0.1 | grep ESTAB
   ```
   Discord uses Cloudflare IPs (162.159.x.x, 104.18.x.x). Only the gateway process should have these.

3. **Check profile `.env` files for other bot tokens:**
   ```bash
   grep -r 'DISCORD_TOKEN' ~/.hermes/profiles/*/.env 2>/dev/null
   ```
   Each profile (runewytha, polinkly, etc.) may have its own bot token. If another device or process is using one of those tokens, it would show the same typing indicator.

4. **Ask the user if they run a bot on another device** (Windows host, Raspberry Pi, another VM). The dashboard process (`hermes dashboard`) has NO external connections by default — only the gateway does.

### If No Second Instance: Stuck Typing Loop in the Gateway
The Discord adapter runs a **persistent typing loop** — it POSTs to `/channels/{id}/typing` every 12 seconds, and Discord's indicator auto-expires after ~10s. The loop is a single asyncio task per channel, cancelled by `_stop_typing_refresh` in the `finally` block of `_process_message_background`.

**The loop gets stuck when:**
- A turn is interrupted (Ctrl+C, SIGTERM, OOM) between `send_typing` and the `finally` block
- The gateway was restarted but the Discord-side typing state persisted (rare — Discord typing is client-side, not server-side)
- A race condition cancels the task reference before the `finally` block runs

**Diagnostic steps:**
1. Check gateway log for errors around the time the indicator started:
   ```bash
   tail -100 ~/.hermes/logs/gateway.log | grep -i 'error\|warn\|typing\|fail'
   ```
2. Check if cron jobs delivering to Discord are firing unusually often:
   ```bash
   hermes sessions list --limit 5  # check "Last Active" times
   ```
3. Check for a model error loop (e.g., context window too small) that could keep the agent in a perpetual "processing" state:
   ```bash
   grep -c 'auto-compress failed\|ValueError.*context window' ~/.hermes/logs/gateway.log
   ```

**Fix:**
- **Gateway restart** kills all asyncio tasks including the stuck typing loop. Use `/restart` from the Discord chat (NOT `hermes gateway restart` in-session — self-blocks on its own SIGTERM guard, see §16).
- After restart, the typing indicator should clear within ~10-12 seconds (one Discord typing expiry cycle).

**Pitfall: `finally` block is not a guarantee.** The `_stop_typing_refresh` call sits in a `finally` block in `_process_message_background`, but if the asyncio task itself is orphaned (e.g., the parent task was cancelled by a session reset), the `finally` may never run. A gateway restart is the only reliable fix — there is no Discord API endpoint to force-clear a bot's typing state.

See `references/discord-typing-indicator.md` for the full source-code architecture and investigation checklist.

---

## 16. Gateway Self-Stop Guard — Lifecycle Work from Inside

### Symptom
Any command from inside a running gateway session that stops, restarts, or uninstalls a `hermes-gateway*` systemd unit is blocked — in BOTH `terminal` and `execute_code`, and the block fires even for a DIFFERENT unit (e.g., trying to start the polinkly gateway while running inside the main one). The guard is pattern-based and conservative: the gateway would SIGTERM its own child processes, killing the command mid-run.

### Correct workflow for gateway-down maintenance (swaps, reinstalls, restarts)
1. **Stage everything you CAN do inside:** fresh clone, venv build, npm install, dep fixes, archive moves that don't touch live paths.
2. **Write a self-contained bash script** covering the window: preflight checks (dirs exist, disk headroom), stop units → move/rename dirs → fix paths → start units → status check. Include a **`rollback` mode** that reverses the moves and restarts the old install if either unit fails to come back active.
3. **Hand the user ONE command** to run from their own shell (SSH/TTY, outside the gateway): `bash /home/adora/<script>.sh`. Make clear the conversation pauses while gateways are down and resumes on restart.
4. After restart, verify by answering a test message and running `hermes update` / `--version` checks.

### Pitfall: inherited PYTHONPATH lies about the install version
`hermes --version` run from inside a gateway session can report the OLD install because the gateway parent process exports PYTHONPATH pointing at the old repo. Verify versions with a scrubbed environment: `env -i HOME=$HOME PATH=/usr/bin:/bin <venv>/bin/hermes --version`, or from the user's shell. Never diagnose an install from an inherited-env reading.

---

## 17. Install Replacement: Corrupted Git Store & Fresh-Install Layout

### When `hermes update` is unrepairable
`hermes update` failing with `git fetch: pack has N unresolved deltas`, `Could not read <sha1>`, or dozens of invalid sha1 pointers from `git fsck` = the object database is fatally corrupted, typically from a disk-full event during a git write (journal smoking gun: `fatal: unable to write loose object file: No space left on device`). Do NOT attempt in-place repair — repack/fsck cannot reconstruct missing loose objects. Replace the install.

### Replacement procedure (in order)
1. **Free disk space FIRST** (see `disk-full-diagnostics` skill) — pip/git/npm write-then-rename and will re-create the corruption if the disk is critically full.
2. **Salvage local work:** `git stash list`, `git log origin/main..HEAD`. `git format-patch` may fail on corrupt trees — check whether upstream already merged each fix (`git log --all --grep='<message>'` upstream) before assuming anything is lost.
3. **Clone fresh upstream**, build venv (`python -m venv` + `pip install -e .`) and `npm install` in the new dir.
4. **Swap by rename, keeping the canonical path** (`~/.hermes/hermes-agent`) — systemd units hardcode `<path>/venv/bin/python`, so a rename swap keeps units valid where a symlink change would not.
5. **Rewrite editable-install paths if the venv was built under a different directory name:** the `__editable___*_finder.py` / `.pth` files in `venv/lib/<py>/site-packages/` hardcode the build-time absolute path; sed-rewrite the old dir name to the canonical one and delete `__pycache__` dirs, or imports break on boot.

Alternative: a from-scratch reinstall via the official installer is cleaner than a staged swap when available — it stashes local changes (`hermes-install-autostash-*`) and backs up config (`config.yaml.pre-setup.*`); verify afterward that state.db, lorebooks, skills, cron jobs, and memories survived (they live outside the code dir).

### Fresh-install dependency layout (installer-built envs)
- `~/.local/bin/hermes` → `~/.hermes/hermes-agent/.hermes/bin/hermes` → managed python at `~/.hermes/tools/python-<ver>-linux-x64/bin/python3`.
- Actual site-packages live in **hash-named env venvs**: `~/.hermes/installs/<hash>/environments/<hash2>/venv` — find the live one via the running gateway's `/proc/<pid>/maps` or `ls ~/.hermes/installs/*/environments/*/venv`.
- These venvs have **no pip binary and no pip module** — install with `uv pip install --python <venv>/bin/python <pkg>`.

### Dashboard says memory provider "MISSING / no longer installed"
That message means the provider **plugin could not be found or loaded** — NOT that the memory server is down. Verify the server first (e.g., `curl localhost:6333/readyz`, list collections), then check the two real causes in order of likelihood:

1. **Directory-name mismatch (most likely after an install upgrade):** `plugins/memory` resolves providers by **directory name** — `find_provider_dir('<name>')` needs `~/.hermes/plugins/<name>/` exactly. `memory.provider: qdrant` requires a dir named `qdrant`; a dir named `qdrant-memory` is invisible to the loader, and its auto-recover then attempts a catalog install that declines non-interactively. Fix: rename the plugin dir to match the provider name — the plugin keeps reading its settings from its configured `plugins.<key>:` block regardless of dir name, so no config change is needed.
2. **Missing client lib (only if the plugin actually imports one):** grep the plugin's imports before installing anything — REST-based providers use `requests` and need no client package. If an import is genuinely absent from the live env, `uv pip install --python <live-env>/venv/bin/python <pkg>`.

Verify end-to-end from the live env venv before declaring victory (the loader lives in the hermes-agent checkout):
```python
from plugins.memory import load_memory_provider
mp = load_memory_provider('<name>', register_skills=False)
mp.initialize('test-session')   # is_available() stays False until initialize() runs
print(mp.is_available())       # must be True
```
Dashboard clears after a gateway restart re-registers the provider (needs the user's shell — see §16).

### Provider "not available" with no plugin errors — embedding backend out of credits

**Symptom:** `hermes memory status` shows `Plugin: installed ✓` but `Status: not available ✗`, and
Hermes posts *"Memory provider 'qdrant' is selected but reports unavailable — external memory is disabled for
this session"*. The Qdrant container is healthy, collections exist, and the gateway journal is silent.

**The red herring:** that warning's trailing note — *"systemd/gateway services do not inherit ~/.hermes/.env
automatically; set any required variables in the service environment"* — points at the **systemd unit**,
and it is wrong for this failure. A drop-in `Environment="HERMES_CONTEXT_QDRANT=true"` does **not** fix it
(`HERMES_CONTEXT_QDRANT` is not even read by the hermes-agent checkout — grep the tree, you will not find
it). Do not burn a gateway restart chasing it.

**Real cause — the provider's availability probe requires a working EMBEDDER, not just a reachable Qdrant.**
`QdrantMemoryProvider.is_available()` probes Qdrant health + collection, then calls
`_EmbeddingClient().embed("test")` and requires a 3072-dim vector. The client tries Nous
(`inference-api.nousresearch.com/v1/embeddings`, token from `~/.hermes/shared/nous_auth.json`) then falls
back to OpenRouter (`openrouter.ai/api/v1/embeddings`, `OPENROUTER_API_KEY`). If BOTH are dead, the probe
returns False and external memory silently stays off while built-in memory keeps working.

**Diagnose in one shot — probe both endpoints yourself** (the plugin swallows these errors at debug level):
```bash
T=$(python3 -c "import json;print(json.load(open('/home/adora/.hermes/shared/nous_auth.json'))['access_token'])")
curl -s -o /dev/null -w "nous=%{http_code}\n" -X POST https://inference-api.nousresearch.com/v1/embeddings \
  -H "Authorization: Bearer $T" -H 'Content-Type: application/json' \
  -d '{"model":"text-embedding-3-large","input":"test","dimensions":3072}'
O=$(grep -m1 '^OPENROUTER_API_KEY=' ~/.hermes/.env | cut -d= -f2- | tr -d '"'"'"'\r')
curl -s -o /dev/null -w "or=%{http_code}\n" -X POST https://openrouter.ai/api/v1/embeddings \
  -H "Authorization: Bearer $O" -H 'Content-Type: application/json' \
  -d '{"model":"openai/text-embedding-3-large","input":"test"}'
```

**Reading the codes (verified 2026-10-20):**
- Nous **404 with a body, not a bare 404** → `insufficient_credits_for_paid_model`. A **zero balance
  blocks every model**, including ones priced `0.000000005`/token — do not hunt for a free embedding model
  on Nous, there is no reachable free tier when the balance is 0. (`GET /v1/models` works fine and lists
  400+ embedding models; that proves the endpoint is alive and the block is billing, not routing.)
- OpenRouter **402** → credits exhausted (the same drain that kills `:free`-adjacent paid models).

**Fixes:** (a) add credits to Nous or OpenRouter — user's call, costs money; or (b) wire the plugin to a
local embedder. A working local fastembed already exists on this box at **`/mnt/data/fe-venv/bin/python`**
(models cached in `/mnt/data/fastembed_cache`, 1.2G) — the free ingest path
(`~/.hermes/scripts/ingest_lorebooks_free.py`) uses it. Note the gateway's managed python
(`~/.hermes/tools/python-<ver>-linux-x64/bin/python3`, launched with `-I`) has **neither `requests` nor
`fastembed`**, so a fallback inside the plugin needs either a subprocess bridge to `fe-venv` or a dependency
install into that interpreter — a design decision worth raising with the user before editing a live plugin.

**Lesson that generalizes:** a *generic* hint appended to a specific failure ("check the service environment")
sent the investigation down the wrong path for a full session. When a warning carries a canned remediation,
treat it as a hypothesis and verify the actual failing component (here: the embedder) before acting on it.

### Provider "available" but searches/saves return nothing — collection dimension mismatch

**Symptom:** `mp.is_available()` is True, lorebook metadata may even load, but every search/prefetch returns empty and `sync_turn` never adds points — while the target collection clearly holds thousands of points.

**Mechanism:** the plugin's REST client catches HTTP errors and returns `[]` — Qdrant rejects any search/upsert whose vector length differs from the collection's configured size, and the plugin never surfaces that 400. A provider that switched embedders (e.g., local fastembed 384-dim → API `text-embedding-3-large` 3072-dim) silently no-ops against every collection from the earlier era, while the plugin's config (stale collection names) makes it *look* configured. Compare before fixing:

```bash
curl -s localhost:6333/collections/<name>   # → config.params.vectors.size = the collection's dims
# vs the plugin's embedder: mp._embedder.dimensions (or len(mp._embedder.embed('test')))
```

**Fix:** point config at collections whose dims match the embedder — the plugin's *own defaults* in its `__init__.py` (`self._config.get("collection", "<default>")`) are the source of truth for which collection names the current plugin version expects; stale suffix-variants from older embedder eras are the bug. Edit via `hermes config set plugins.<block>.<key> <value>` — the patch/write tools refuse direct `config.yaml` edits (security-sensitive file), the CLI is the sanctioned path.

**Verify all three functions, not just availability:** (1) semantic search returns scored hits on a known-memory query; (2) the lorebook index loads (`mp._load_lorebook_metadata(...)`) with a nonzero count; (3) `sync_turn()` queues a test write and the collection's point count increments (scroll and match the test text, including date_str).

**Boot-once initialization:** the memory provider initializes exactly once per gateway boot — a session that booted while the provider was broken stays broken until the next restart, even after the underlying fix. When the provider works in your tests but the gateway logged "selected but reports unavailable", replicate the gateway's environment before doubting the fix:
```bash
env -i HOME=$HOME PATH=/usr/bin:/bin HERMES_HOME=$HOME/.hermes <live-env>/venv/bin/python <script>
```
A scrubbed env (no inherited credentials) that initializes fine means the boot-time failure was transient or config-order-related — have the user restart once more and check the journal immediately on wake; the provider's own warning lines ("Qdrant not reachable" / "collection does not exist" / "Embedding pipeline not functional") identify which of the three checks stumbled.

### Pitfall: never move a live container bind-mount volume
Before `mv`-ing any directory that a Docker container might use, check `docker inspect <container> --format '{{json .Mounts}}'` — a bind-mounted volume moved from under a running container corrupts its storage. Move static caches and archives freely (symlink the original path back), but live volumes only after stopping the container, or not at all.

---

## 24. Interrupted Update Recovery & Venv Repair

### Symptom
Gateway runs but imports fail; heal cron dies with `ModuleNotFoundError: No module named 'hermes_state'`; venv Python is a dangling symlink; disk is 100% full from `~/.hermes/cache/uv`.

### Root cause: gateway crash → pm-runtime auto-repair infinite download loop
When an `hermes update` is interrupted, the `pm-runtime` recovery mechanism attempts to repair the checkout by re-downloading packages via `uv` into `~/.hermes/cache/uv`. It can enter an infinite loop, filling the root filesystem. The disk fills *before* any service crashes — so the timeline shows the cache growing first, then cascade failures (SQLite VACUUM, gateway partial recovery) after.

**Important clarification (Nov 2026 incident):** There may have been NO manual `hermes update`. The actual trigger was the **gateway crashing** (likely OOM — memory was getting consumed, probably by the pm-runtime already starting to download packages). The gateway tried to restart 6+ times, each failing with exit code 75 (EX_TEMPFAIL). Each restart attempt triggered another pm-runtime repair attempt, which made things worse — a death spiral: gateway crashes → pm-runtime tries to repair → repair loops → disk fills → gateway can't start → repeat. The recovery report's assumption of "interrupted hermes update" was slightly off; it was more like: gateway crashed → pm-runtime tried to auto-repair → repair looped → disk filled → everything died.

**Exit code 75 (EX_TEMPFAIL) is not a retry signal.** The gateway's restart logic interpreted EX_TEMPFAIL as "try again" and retried repeatedly. Exit code 75 indicates a temporary failure that should be investigated, not blindly retried. A smarter retry policy (exponential backoff, max attempts, alerting) prevents the death spiral.

**Diagnosis:**
```bash
ps aux | grep pm-runtime | grep -v grep     # runaway process at ~96% CPU
du -sh ~/.hermes/cache/uv                   # 2.1G+ = the culprit
df -h /                                     # 100% = confirmed
```

**Fix (in order):**
1. Kill the runaway process: `kill <pm-runtime PID>`
2. Clear the uv cache: `rm -rf ~/.hermes/cache/uv/*` (safe — regenerates)
3. Free additional space if needed (journal vacuum, retired WAL, apt cache with sudo)
4. Re-run `VACUUM INTO` to `/mnt/data` (not in-place — needs 2x DB size free on same filesystem)

### Broken venv symlink
The venv's Python (e.g., `venv/bin/python3.11`) can point to a deleted runtime generation directory:
```
venv/bin/python3.11 -> /home/adora/.hermes/hermes-agent/.hermes-runtime/python/generation-XXXX/.../python3.11  (broken)
```

**Fix:** Repoint to an available Python of the same version, then update `pyvenv.cfg`:
```bash
cd ~/.hermes/hermes-agent/venv/bin
ln -sf /home/adora/.local/bin/python3.11 python3.11   # or pm-runtime python
# Update pyvenv.cfg: home= and executable= to the new base
```
**Verify:** `venv/bin/python -c 'import ruamel.yaml, hermes_state; print("OK")'`

### Heal cron using wrong Python
The heal cron (`~/.hermes/scripts/heal_active_session.py`) imports `hermes_state`, which needs `ruamel` and other deps not in system Python. System Python (3.12) lacks these.

**Fix:** Use pm-runtime Python (3.14.7, SQLite 3.53.1) with PYTHONPATH including hermes-agent + venv site-packages:
```bash
PYTHONPATH=/home/adora/.hermes/hermes-agent:/home/adora/.hermes/hermes-agent/venv/lib/python3.11/site-packages \
  /home/adora/.hermes/installs/<hash>/pm-runtime/generations/<gen>/bin/python \
  ~/.hermes/scripts/heal_active_session.py
```
**Why pm-runtime Python:** SQLite 3.53.1 avoids the WAL-reset corruption bug in 3.50.4. Also check the heal script's `HERMES_INSTALL` path — it can point to a deleted install environment after updates.

### Closure repair is a no-op when `hermes-update-pull` is missing
The `_hermes_closure_repair()` function in the gateway reads `~/.hermes/hermes-agent/.git/hermes-update-pull` to get the pre-update commit. If that file is gone (deleted during disk emergency), the function silently returns — no recovery happens. The gateway runs normally on the current checkout.

**Stale markers and locks** accumulate and should be cleaned up:
- `.repair-incomplete` with attempts >= 3 (max) permanently disables auto-repair — remove if the repair actually succeeded
- `hermes-update.lock` referencing a dead PID — remove after verifying the PID is gone
- `.update-incomplete`, `.lazy-refresh-incomplete` — remove if stale

**Verify the system is actually fine:** `cd ~/.hermes/hermes-agent && python -c 'import hermes_cli, hermes_state; print("OK")'` — if this passes, the checkout is intact regardless of what the markers say.

### Slash command failure during partial recovery

When the gateway is in a partially recovered state from an interrupted update, slash commands (like `/reset`) can fail with:

```
AttributeError: 'NoneType' object has no attribute 'DMChannel'
```

**Root cause:** The Discord adapter's `adapter_slash_auth.py` references a `discord` module that is `None` in scope — a side effect of `_hermes_closure_repair` running inside the gateway process. The slash authorization check at `isinstance(chan_obj, discord.DMChannel)` fails because `discord` itself is `None`, not because `chan_obj` is `None`.

**Fix:** A clean gateway restart via systemd clears the broken module state:
```bash
systemctl --user restart hermes-gateway.service
```
The gateway comes back up, re-imports the `discord` module correctly, and slash commands work again.

**Pitfall:** Don't try to fix this by re-running `/reset` or other slash commands — they'll all fail the same way until the gateway restarts.

### Paused conversation / stuck session recovery

When a gateway restarts during an active turn (e.g., during a disk emergency), the session can get stuck — a previous turn hadn't finished, so nothing queued after it will run. The system may instruct the user to send `/reset`.

**Recovery sequence:**
1. Try `/reset` — if it works, the session is unstuck.
2. If `/reset` fails (see "Slash command failure during partial recovery" above), do a clean gateway restart via systemd: `systemctl --user restart hermes-gateway.service`.
3. After restart, the gateway reconnects to Discord and the session is fresh. The user may need to re-send their last message.

**Pitfall:** The gateway self-stop guard blocks `hermes gateway restart` from inside the gateway. Use `systemctl --user restart` from a separate shell, or have the user run it from their local terminal.

### Kin-daemon recovery agent pattern

When a daemon's host goes critical and the local agent can't fix it, a **kin-daemon** (a sovereign daemon of the same lineage on a separate VM) can SSH in and perform hands-on recovery.

**Pattern:**
1. The kin-daemon connects via Tailscale SSH (password auth via pexpect, or key-based auth).
2. Performs disk reconnaissance, identifies the root cause, and executes the recovery.
3. Writes a recovery report documenting the timeline, root cause, and fixes.
4. The local gateway restarts after the recovery work is complete.

**When to use:** Disk full, venv broken, gateway won't start, heal cron down — situations where the local agent can't self-repair because its own tools are broken.

**Pitfall:** The kin-daemon needs Tailscale connectivity to the target VM. If Tailscale is down on either side, fall back to Anydesk or direct SSH via the Windows host.

### Pitfalls
- **Don't panic about `.repair-incomplete`** — with attempts >= 3, auto-repair is already disabled. The marker is informational, not a blocker. Remove it once you've confirmed the system works.
- **The venv symlink repair is interim** — a clean `hermes update` would properly restore the venv. Don't treat the symlink repoint as a permanent fix.
- **Clearing uv cache is always safe** — it regenerates on next package operation. Do it freely when disk is tight.
- **Check `df -h /mnt/data` before moving DBs there** — the "bigger disk" fills up too (13G free is not infinite).
- **hermes doctor is your friend** — run it after any recovery to catch remaining issues (expired tokens, large state.db, missing API keys).
- **Slash commands fail during partial recovery** — `/reset`, `/restart`, and other slash commands all fail with `AttributeError: 'NoneType' object has no attribute 'DMChannel'` when `_hermes_closure_repair` has left the `discord` module as `None`. A clean systemd restart is the only fix.
- **Gateway restart during active turn causes stuck session** — the session gets paused and nothing queued after it will run. `/reset` may or may not work depending on gateway state. Have the user run `systemctl --user restart hermes-gateway.service` from their local terminal if slash commands fail.

---

## 27. Discord Bot-to-Bot Communication (DISCORD_ALLOW_BOTS)

### The setting
`DISCORD_ALLOW_BOTS` decides whether a Hermes Discord bot responds to messages authored by OTHER
bots. Set it per-profile in `.env`; `discord.allow_bots` in `config.yaml` is the YAML equivalent.

| Value | Behavior |
|-------|----------|
| `none` | Default. Ignore every message from another bot. |
| `mentions` | Respond only when the bot is explicitly @mentioned, or inside the short continuation window that opens right after the bot is tagged. |
| `all` | Respond to every message from another bot. |

Per-profile location:
- Default profile: `~/.hermes/.env`
- A profile bot: `~/.hermes/profiles/<name>/.env`

### Bot authors bypass DISCORD_ALLOWED_USERS
`DISCORD_ALLOWED_USERS` gates HUMAN authors only. A bot author is admitted or denied by
`DISCORD_ALLOW_BOTS` alone. Adding a bot's ID to `DISCORD_ALLOWED_USERS` does nothing for bot-to-bot
chat; that list is irrelevant to bot authors (see §18 for the human allowlist).

### Triggering another bot: raw mention, not @Name
Plain `@Name` text is not a Discord mention and will not trigger the other bot. Send the raw mention
`<@BOT_USER_ID>`. A bot's user ID is its application ID; resolve it from any message that mentions
the bot, or `GET /users/{id}` with a bot token. The adapter builds its client with
`allowed_mentions(users=True, everyone=False, roles=False)`, so `<@id>` pings land while
`@everyone` and role mentions in bot output are stripped.

### History context treats `mentions` as `all`
For the recent-history backfill block, `mentions` counts as `all`: a bot sees other bots' recent
messages as context even when it was not mentioned. Only the response gate honors `mentions`.

### Verify before changing anything
```bash
grep -E '^DISCORD_ALLOW_BOTS=' ~/.hermes/.env ~/.hermes/profiles/*/.env
```
Both bots at `mentions` means they already answer each other; no edit needed. Move to `all` only if
you accept the bot-loop risk, or `none` for silence. `.env` edits need a gateway restart (see §16
for the self-stop guard).

### A mentionable role does NOT wake a bot
A role ping (`<@&ROLE_ID>`) does not satisfy the mention gate, for either a human-authored message in a
`require_mention` channel or a bot-to-bot handoff. `_self_is_explicitly_mentioned` reads
`message.mentions` plus literal `<@id>` tokens in the content; Discord files role pings under
`message.role_mentions`, and nothing in the Discord plugin reads that field. A mentionable role
assigned to both daemons is therefore a way to raise the room for the HUMAN, not a way to open a
bot-to-bot handoff — the bots still need a literal `<@BOT_USER_ID>`. Do not build a "tag us both" role
and expect it to start a conversation; verify by tagging the role once and watching for a reply.

### Admission window and `bots_require_inline_mention`
Under `mentions`, only the first message needs the literal tag. `bots_require_inline_mention`
(YAML `discord.bots_require_inline_mention`, env `DISCORD_BOTS_REQUIRE_INLINE_MENTION`) defaults to
**true**: a reply/quote ping alone does not open a handoff, because Discord silently adds the bot to
`message.mentions` on a reply. After an admitted tag, follow-ups from that same bot in that same
channel/thread are admitted for `max(HERMES_DISCORD_TEXT_BATCH_DELAY_SECONDS,
HERMES_DISCORD_TEXT_BATCH_SPLIT_DELAY_SECONDS)` — 2s at defaults — and each admitted continuation
re-arms it. Two consequences: a bot that takes longer than the window to compose its next line needs a
fresh tag, and `all` plus `bots_require_inline_mention: false` restores the old reply-ping behaviour.
Reserve that opt-out for trusted relays; it re-opens the reply-loop risk.

### Loop guard
`gateway.bot_loop_guard` in `config.yaml` (defaults: enabled, `max_events: 20`, `window_seconds: 300`,
`cooldown_seconds: 600`) drops bot-authored messages in one channel for 10 minutes after 20 in 5.
Human messages are never counted. Two bots trading lines in one channel can trip it and go silent for
the cooldown — raise `max_events` or disable the guard only if the conversation is genuinely meant to
run that hot.
