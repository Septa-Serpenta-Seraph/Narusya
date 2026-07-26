---
name: hermes-infrastructure
description: Diagnose, recover, and maintain Hermes Agent infrastructure — browser tools, gateway, config, power outage recovery, and post-update fixes.
triggers:
  - browser tool not working
  - gateway not running
  - hermes update
  - power outage recovery
  - config reset
  - hermes diagnostics
  - hermes recovery
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
If you need memory-like functionality alongside an existing external provider, **extend** the existing provider rather than registering a new one. For example, the Qdrant lorebook auto-inject was added by patching `qdrant-memory/__init__.py` to query a second collection inside the same provider's `prefetch()` method.

### Architecture Implications
When designing new memory-backed features:
- Check `hermes memory status` first to see what's already active
- If extending, modify the existing provider's code path
- If replacing, use `hermes memory setup` to switch providers cleanly
- The builtin `builtin` provider (plain files in `~/.hermes/memories/`) always runs alongside the external one — only non-builtin plugins are gated
