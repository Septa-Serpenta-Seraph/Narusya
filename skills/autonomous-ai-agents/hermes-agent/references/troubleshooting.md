# Troubleshooting

### Voice not working

**Symptom:** voice messages reach the transcript as
`[voice message could not be transcribed automatically; the audio is available at: <path>]` instead of
text. That `<path>` is a real local file — transcribe it yourself rather than telling the user you
can't hear the message.

**Cause:** `stt.provider: local` needs `faster-whisper`, which is an optional extra (`stt-whisper` /
`voice`), not part of the core install. When it is missing, the gateway logs
`STT provider 'local' configured but unavailable` and substitutes the marker above.

**Fix (durable):** install the extra with the explicit form, which bypasses the lazy-install gate:
```bash
python -c "import pm; pm.sync_venv(['stt-whisper'], explicit=True)"
# equivalent documented hint: hermes pm install --extra stt-whisper
```
The sync publishes a new committed generation; an already-running process keeps its old interpreter, so
the gateway needs a restart (`/restart`, or a clean systemd restart — see the self-stop guard) before it
picks the extra up.

**Pitfall — the lazy-install error names the wrong knob.** Going through
`pm.extras.ensure_import('stt-whisper')` (or letting `_transcribe_local` lazy-install) from an
interpreter that is not the install's dependency environment raises
`venv: not installed and lazy installs are disabled ... this process is not running from the install's
dependency environment`. The hint says to enable `security.allow_lazy_installs`, but that flag is
usually already true — the real gate is `running_from_selected_environment` in `pm.client.sync_venv`,
which compares `sys.path` against the committed generation's site-packages. Use the `explicit=True`
form; do not go hunting for a config flag that is not the problem.

**One-off transcription without changing the install:** resolve the committed generation and use its
interpreter.
```python
from pm.environments import selected_venv
from pm.paths import repo_root
venv = selected_venv(repo_root())   # ~/.hermes/installs/<hash>/environments/<hash2>/venv
```
Run `<venv>/bin/python` with `faster_whisper.WhisperModel` on the cached clip. On short clips `base`
mis-hears; `small` with `beam_size=5` is a real step up.

**Alternate providers:** `GROQ_API_KEY` (free tier), `VOICE_TOOLS_OPENAI_KEY`, `MISTRAL_API_KEY`, or a
custom local command via `HERMES_LOCAL_STT_COMMAND` (placeholders `{input_path}`, `{output_dir}`,
`{language}`, `{model}`) / `stt.providers.<name>: type: command` in YAML.

### Tool not available
1. `hermes tools` — check if toolset is enabled for your platform
2. Some tools need env vars (check `.env`)
3. `/reset` after enabling tools

### Model/provider issues
1. `hermes doctor` — check config and dependencies
2. `hermes auth` — re-authenticate OAuth providers (or `hermes auth add <provider>`)
3. Check `.env` has the right API key
4. **Copilot 403**: `gh auth login` tokens do NOT work for Copilot API. You must use the Copilot-specific OAuth device code flow via `hermes model` → GitHub Copilot.

### Changes not taking effect
- **Tools/skills:** `/reset` starts a new session with updated toolset
- **Config changes:** In gateway: `/restart`. In CLI: exit and relaunch.
- **Code changes:** Restart the CLI or gateway process

### web_extract shows a stale page (result caching)
`web_search`/`web_extract` cache results for 20 minutes (PR #94618) — a
repeat fetch of the same URL within the TTL is served from cache, which
can look like "my website changes aren't showing up."

Automatic carveouts (always fetched live, never cached):
- localhost / 127.0.0.1 / `*.local` / `*.localhost` / single-label LAN
  hostnames / private + link-local IP ranges (dev servers, hot-reload
  builds, chat-GUI artifact previews)
- URLs matched by `security.website_blocklist`
- failed responses and keyless-rescue-served responses

Developing a site tested over the PUBLIC internet (Vercel/Netlify
preview, ngrok/cloudflared tunnel, staging domain)? Public DNS isn't
auto-carved-out — list the host in config.yaml:

```yaml
web:
  cache_exempt_hosts:      # always fetched live; effective immediately
    - mysite.vercel.app
    - "*.ngrok-free.app"
    - mysite.dev           # suffix match: also covers preview.mysite.dev
```

Blunt instruments: `web.cache_ttl_minutes: 1` (min) or
`web.cache_enabled: false` disables both caches entirely.

### Skills not showing
1. `hermes skills list` — verify installed
2. `hermes skills config` — check platform enablement
3. Load explicitly: `hermes -s name` (or the skill's own `/<name>` slash command)

### Update failures (`hermes update` / `/update` exits nonzero)
Diagnose from receipts, not guesses: `~/.hermes/logs/update_receipts/latest.json` (plus per-run files beside it) records `outcome`, `stop_reason`, `steps`, and pre/post SHAs for every attempt.

- **Instant exit 1, empty `steps` (~2s runtime):** a pending interactive prompt the runner cannot answer through the gateway — most commonly an un-restored autostash left by a previous update (`git stash list` shows `hermes-update-autostash-*`). Run `hermes update --yes` from a terminal; it accepts the config-migration and stash-restore prompts non-interactively. Check stashes afterward: autostashed lockfile drift is safe to drop, but `git stash show --stat` before removing anything.
- **"Refusing to move this install... Downgrading is unsupported":** the install sits on a newer canary/main commit than the latest stable release, so the "Update available" notice is downgrade-bait. This is a guard, not a breakage — the correct response is to leave the install alone (or deliberately track the canary channel), never to force it.
- **A successful update left `git stash` entries:** updates autostash local repo changes and re-apply them post-pull; if restoration was skipped, the tree looks clean while user patches sit parked in the stash. `git stash show --stat` reveals what's there.
- Gateway-invoked `/update` is fine for routine pulls; use terminal `hermes update --yes` whenever a prior update left unfinished business.

### Gateway issues
Check logs first:
```bash
grep -i "failed to send\|error" ~/.hermes/logs/gateway.log | tail -20
```

Common gateway problems:
- **Gateway dies on SSH logout**: Enable linger: `sudo loginctl enable-linger $USER`
- **Gateway dies on WSL2 close**: WSL2 requires `systemd=true` in `/etc/wsl.conf` for systemd services to work. Without it, gateway falls back to `nohup` (dies when session closes).
- **Gateway crash loop**: Reset the failed state: `systemctl --user reset-failed hermes-gateway`

### Gateway + SSH both down simultaneously

When the Discord gateway stops responding AND SSH to the VM fails at the same time, it is a VM-level event (reboot, OOM kill, network partition) — not a tailscale session expiry (which kills only SSH). Tailscale session expiry is covered in the `tailscale-session-recovery` skill.

Diagnosis order:
1. Check tailscale: `tailscale status` + `tailscale ip -4`. If tailscale shows `NeedsLogin`, it is a session expiry — follow tailscale-session-recovery.
2. If tailscale is healthy but SSH still fails, the VM itself went down (OOM, kernel panic, host reboot). Wait for it to come back; check host-level monitoring.
3. If SSH works but gateway is dead, check `ps aux | grep gateway` and `~/.hermes/logs/gateway.log`. Restart with `hermes gateway` or the service manager.

### Active session healing after reset

After any session reset (`/new`, `/reset`, gateway restart, compression split), the literal title `"active session (discord)"` stays on the OLD session. Crons and later searches resolve the live DM by that title, so they read stale context.

Fix: run the idempotent heal script:
```bash
python3 ~/.hermes/scripts/heal_active_session.py
```
It queries `state.db` for DM sessions ordered by `last_activity_at`, finds the one holding the active title, and swaps the title onto the newest session if they differ. The displaced holder gets a dated name (e.g. "Oct 22, 2026"). Safe to run on a schedule (crontab every 30 min).

### State.db WAL mode quirk

`~/.hermes/state.db` uses WAL (Write-Ahead Logging). A direct `sqlite3.connect()` may show 0 bytes or empty tables because committed data lives in the `-wal` file, not the main DB file. The main file can appear as 0 bytes even when the DB has gigabytes of data.

Fix before querying:
```python
conn = sqlite3.connect('/home/adora/.hermes/state.db')
conn.execute('PRAGMA wal_checkpoint(TRUNCATE)')
# now tables and data are visible
```
Or use the `hermes_state` module which handles this internally.

### Platform-specific issues
- **Discord bot silent**: Must enable **Message Content Intent** in Bot → Privileged Gateway Intents.
- **Slack bot only works in DMs**: Must subscribe to `message.channels` event. Without it, the bot ignores public channels.
- **Windows-specific issues** (`Alt+Enter` newline, WinError 10106, UTF-8 BOM config, line endings): see `references/windows-quirks.md`.

### Auxiliary models not working
If `auxiliary` tasks (vision, compression, session_search) fail silently, the `auto` provider can't find a backend. Either set `OPENROUTER_API_KEY` or `GOOGLE_API_KEY`, or explicitly configure each auxiliary task's provider:
```bash
hermes config set auxiliary.vision.provider <your_provider>
hermes config set auxiliary.vision.model <model_name>
```

### "Reset permissions" / auto-approving everything
See `references/security-privacy.md` — wipe the "Always allow" stores, don't touch yolo mode.

