---
name: self-hosted-web-dashboards
description: "Self-hosted web dashboards: tabs, systemd, OSS plug-in."
tags: [self-hosted, dashboard, web-app, systemd, tailnet, oss-adoption, python]
---

# Self-Hosted Web Dashboards (PIPNARU-class apps)

Class-level guide for building the kind of small, self-hosted web UIs this user
asks for repeatedly — health terminals, monitoring dashboards, tool panels. These
must be: served from the Tailnet box (`100.77.142.40`, host `narusya`), reachable
from the user's phone, durable across reboots, and honest (never mock data).
Proven across the PIPNARU body-terminal build (2026-08-19).

## When to use

- User wants a "panel", "dashboard", "terminal", "screen", or "tracker" — body
  health, storefront, monitoring, AEGIS-style, whatever.
- Need to serve a small self-hosted UI to the user's phone/other device over Tailnet.
- Any local web app that should survive reboot with minimal ops (no Docker needed).
- Adopting an open-source component instead of building art/wiring from scratch.

## Golden architecture (near-zero deps)

- **Python stdlib `http.server`** (`SimpleHTTPRequestHandler` with
  `directory=BASE`; derive `BASE` from `__file__`) — no Flask, no Docker, no venv.
- **Static HTML/CSS/JS shell** with a tab band; tabs fetched via
  `fetch('tabs/<name>.html')` + `innerHTML`. Vanilla JS, zero build step.
- **Plain files as the datastore**: JSON API handlers read/write markdown/JSON on
  disk (logs double as human/doctor evidence; quests.json etc).
- API shape: `GET /api/state` (parsed current), `GET /api/list?n=N` (recent),
  `POST /api/write` (append). Keep endpoints simple and idempotent-ish.

## CRITICAL tab-loader pitfall (hit live)

Injecting tab HTML via `innerHTML` **strips ALL `<script>` tags**, including
`<script src=...>` library loads inside the tab file. A third-party UMD lib
referenced from a tab will silently never load.
**Fix:** load shared libs in the SHELL (index.html) **before** the tab loader,
NOT inside tab markup. Verify with a browser-console `typeof Lib !== 'undefined'`
check after a tab switch.

## Durability — per-user systemd service (proven)

Foreground `python3 server.py` dies on reboot. Make it a user service:

1. `~/.config/systemd/user/<app>.service` — `Type=simple`,
   `WorkingDirectory=<dir>`, `ExecStart=/usr/bin/python3 <dir>/server.py`,
   `Restart=on-failure`.
2. `loginctl enable-linger <user>` — survives before login.
3. `systemctl --user enable --now <app>.service`.

**Operational reality:** restarting a systemd user service requires an *explicit
user approval*; the agent cannot restart it autonomously (e.g. inside /loop). So:
- Batch all backend (server.py) edits → ask the user to approve ONE restart.
- **HTML/CSS/JS asset edits need NO restart** — the handler serves them fresh from
  disk. Iterate the frontend freely before the single backend restart.

## The OSS verify-and-plug rule (this user's explicit preference)

"Find open source, verify it's safe, plug it in — save scratch for bridges, not
whole systems." When adopting a component:

1. **License check**: repo LICENSE (try `main` then `master`) + npm registry
   (`https://registry.npmjs.org/<name>` → `.license`, `.repository.url`).
   Apache-2.0 / MIT = safe; reject unknown licenses for this use.
2. `npm pack <pkg>` → inspect tarball: license, dist builds (UMD works from
   filesystem), exports.
3. Copy the UMD/asset to `lib/` + keep LICENSE (and NOTICE) adjacent.
4. Wire in with a `<div>` fallback so the panel still renders data if the lib fails.
5. Prefer interactive reusable components (e.g. `body-muscles` Apache-2.0 body
   map) over hand-drawn SVG silhouettes.

## Serving to the phone (Tailnet)

- Find the box IP: `tailscale status` (host = `narusya` @ `100.77.142.40`).
- Bind the server to **`0.0.0.0`** (localhost is unreachable from the phone).
- User opens `http://<box-ip>:<port>/`; a plain-HTTP "insecure" warning on a raw
  tail IP is expected — safe on the owner's net, don't promise TLS.
- `tailscale status` also lists the phone host; check request logs for that IP to
  confirm the phone path works.

## Parser & display honesty (status/health panels)

- **Latest entry wins**: `re.findall(pat, blob, re.I)[-1]` — `re.search` grabs the
  FIRST match and shows stale state (morning vs tonight). Always take the last match.
- **Scale conversion**: logs may be 0–10 while bars render 0–100. `value_100 =
  raw * 10`, and label the raw value (`E0/10`) on the bar. Raw 0–10 drawn straight
  onto a 0–100 bar shows a 4% bar for a 4/10 — looks far worse than reality.
- **Dedup multi-source reads**: `list(dict.fromkeys(...))` for buff/debuff/effect
  lists when parsing two+ files, else double-count.
- **Label derived vs base**: defaulted stats (HP, FOCUS) must say "base"; only
  log-derived stats read as live. A panel that implies data it doesn't have is poison.

## Build/test loop

1. `curl :<port>/api/<state>` → real JSON, not mock.
2. `curl -X POST /api/<write>` with a full payload → `{"ok": true}`, file grew.
3. Browser-load; click every tab; verify content swaps.
4. Browser-console fetch for the true user path without clicks; drive tab clicks
   via JS (`document.querySelector('[data-tab="x"]').click()`).
5. **Scrub test entries** after E2E — slice the data file at the test marker.
   Scratch must never live in the user's real data (medical logs especially).

## References
- `references/pipnaru-terminal.md` — full PIPNARU body-terminal build: file layout,
  API contracts, DSQ-2/CCC log schema, quests tab, E2E paths.