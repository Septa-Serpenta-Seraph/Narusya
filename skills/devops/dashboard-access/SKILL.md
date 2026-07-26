---
name: dashboard-access
description: "Access the Hermes Web Dashboard from the VM (API) and from the host (SSH tunnel). Debugging rendering issues, API endpoints, tabs, and config migration."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [dashboard, web-ui, debugging, API, xterm, rendering]
    related_skills: [hermes-agent]
---

# Hermes Web Dashboard: Access & Debugging

Start, access, navigate, and debug the Hermes Web Dashboard.

## Starting the Dashboard

```bash
hermes dashboard
# Output: → Building web UI... ✓ Web UI built
# Hermes Web UI → http://127.0.0.1:9119
```

## Limitation: Binds to 127.0.0.1 Only

The dashboard binds to `127.0.0.1:9119` — localhost only. Cannot be reached from outside the VM via IP address.

**Browser tools CANNOT render the dashboard.** Playwright daemon errors on local connections (500). Use SSH tunnel or API instead.

## Accessing From Host (SSH Tunnel)

```bash
ssh -L 9119:127.0.0.1:9119 adora@narusya
# Then visit http://127.0.0.1:9119 in host browser
```

## Reading Data via API (works from VM)

The API endpoints return JSON even though the main page returns HTML. Key endpoints:

```bash
# Status: version, gateway state, config version, active sessions
curl -s http://127.0.0.1:9119/api/status

# Sessions: full session list with model, tokens, message counts
curl -s http://127.0.0.1:9119/api/sessions
```

**Warning:** `/api/sessions` can be very large (500KB+). Use pagination:
```bash
curl -s 'http://127.0.0.1:9119/api/sessions?limit=5&offset=0'
```

### API Responses

**`/api/status`:**
```json
{
  "version": "0.9.0",
  "gateway_running": true,
  "gateway_state": "running",
  "config_version": 12,
  "latest_config_version": 17
}
```

**`/api/sessions`:**
```json
{
  "sessions": [{
    "id": "20260414_144755_41d74567",
    "model": "xiaomi/mimo-v2-pro",
    "message_count": 176,
    "tool_call_count": 33,
    "is_active": true
  }],
  "total": 233
}
```

## Dashboard Tabs

| Tab | Purpose |
|-----|---------|
| STATUS | Agent version, gateway PID, active sessions, platforms |
| SESSIONS | Full session history with search, message counts, model info |
| ANALYTICS | Daily token usage, per-model breakdown, session counts (7D/30D/90D) |
| LOGS | Filterable by agent/gateway, log level, component |
| CRON | Create/manage scheduled jobs |
| SKILLS | Browse all skills, filter by category, enable/disable |
| CONFIG | Visual YAML editor with 15 sections |
| KEYS | Manage API keys and OAuth provider logins |

## Version Checking

If `config_version < latest_config_version`, run:
```bash
hermes config migrate
```

---

## Debugging Dashboard Rendering Issues

### 1. Is the data there but not visible?

**Symptom:** Messages appear in CLI but not in Dashboard; blank space below visible content.
**Test:** Send a message from CLI → confirm it appears in Dashboard.
**Conclusion:** Backend is fine — frontend rendering issue.

### 2. Is it a sizing/layout issue?

**Symptom:** Content renders correctly on resize, wrong on initial load.
**Diagnosis:** Container measured before layout commits. `fit()` creates grid for wrong dimensions.
**Fix:** Defer initial fit with `setTimeout` (100ms) so browser commits layout. Then use double-RAF for belt-and-suspenders.

### 3. Is it a WebSocket connection issue?

**Symptom:** Terminal shows no content, no error banner, but CLI messages reach Dashboard.
**Diagnosis:** Check DevTools console for `[chat] PTY WebSocket` messages. Check close codes:
- `4401` = auth failed
- `4403` = host/origin mismatch
- `4404` = embedded chat disabled (not started with `--tui`)
- `4408` = client not permitted (localhost binding)

### 4. Is it a theme/dark-mode issue?

**Symptom:** Content is there but invisible (white on white, or vice versa).
**Fix:** Switch themes. Check that `terminalBackground` theme token is set. Some custom YAML themes miss this field.

### 5. Is it session-specific?

**Test:** Try a different session. If the bug follows the session → transcript rendering issue. If it affects all sessions → layout/container issue.

### Files to Inspect

| File | Purpose |
|------|---------|
| `web/src/pages/ChatPage.tsx` | Embedded chat terminal (xterm.js, PTY, WebSocket) |
| `web/src/pages/SessionsPage.tsx` | Session list and preview rendering |
| `web/src/App.tsx` | Dashboard chrome, routing, persistent chat mount |
| `web/src/index.css` | Global styles, layout tokens, theme variables |
| `hermes_cli/web_dist/` | Built frontend (served by dashboard) |

### Rebuilding After Frontend Changes

```bash
cd ~/.hermes/hermes-agent && npm run build --prefix web
hermes dashboard --stop
hermes dashboard --no-open
```

Changes in `web/src/` are NOT picked up by a running dashboard. Must rebuild and restart.

---

## Pitfalls

### SSH tunnel `-L` target resolves to the SSH *host's* localhost, not a nested VM's

When tunneling to reach a dashboard/service on a remote machine, the `127.0.0.1` in the
middle of `-L PORT:127.0.0.1:PORT` means **the machine you SSH into**, NOT a VM nested behind it.

- **If you SSH directly into the dashboard's machine** (its Tailscale/WireGuard IP *is* the VM —
  e.g. Lu's setup: `ssh lumi@100.84.138.75` where `.75` is the VM's own `tailscale0` address per
  `ip addr`), then `127.0.0.1` is correct. The tunnel lands inside the VM where the dashboard listens.
  Command mirrors the simple case exactly:
  `ssh -L 9119:127.0.0.1:9119 lumi@100.84.138.75`
- **If you SSH into a Hyper-V/host and the dashboard is in a *nested* VM**, `127.0.0.1` resolves to
  the host (nothing listening there) → symptom: "SSH connects but the browser fails to open the page."
  Fix: point the tunnel at the VM's bridge IP (`ssh -L 9119:172.19.x.x:9119 host@host`) OR port-forward
  the VM port to the host's localhost (`netsh interface portproxy`).

**Diagnostic (run on the SSH target):** confirm something is actually listening on the port:
```bash
ss -tlnp | grep -E ':9119|:8000|:3000'
hermes dashboard   # starts it + prints the real port/URL
```
Empty listener list + "connects but won't open" = the dashboard isn't running or is on a different
port than the tunnel expects. Match the tunnel's inner port to what `hermes dashboard` reports.

**Lesson from Adora (2026-07-09):** do not assume "different machines = host + nested VM." Check
`ip addr` *inside* the target — if its Tailscale/WireGuard IP equals the SSH address, you are already
inside the VM and the simple `127.0.0.1` tunnel is correct. The host's `ipconfig` (showing a
`172.19.x` vEthernet Default Switch) only proves a nested VM *could* exist — it doesn't prove the SSH
target is the host.
