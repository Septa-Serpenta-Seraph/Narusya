# PIPNARU — Full Build Detail (2026-08-19)

Self-hosted body-health terminal for Adora: **COIL-NET** (renamed from vault-net
on request), a four-tab **PIP-NARU** (STAT/DATA/QUESTS/LOG), green CRT phosphor
theme. Built from scratch in one long session; every lesson below hit live.

## File layout (~/body-panel/)

```
server.py              # Python stdlib http.server, binds 0.0.0.0:8765, /api/* handlers
index.html             # tab shell: rotary tab band (STAT/DATA/QUESTS/LOG), fetches tabs/*.html,
                       # arrow-key navigation, clock + date. Loads shared libs at SHELL level.
css/pip.css            # shared theme: --ph:#4aff6a phosphor, scanlines, vignette, .fill bars
js/api.js              # API.stats() / API.logs(n) / API.log(payload) fetch wrappers
lib/body-muscles.umd.min.js + LICENSE + NOTICE   # Apache-2.0 OSS body map (plug-and-play)
tabs/stat.html         # pipgirl silhouette + HP/STAM/HYDR/FOCUS bars (auto-refresh 15s)
tabs/data.html         # interactive anatomy: body-muscles SVG map (front/back), trend, entries
tabs/quests.html       # todo-as-quests: tap-to-toggle done/undo, XP counter, add-quest
tabs/log.html          # rich input: energy/pain sliders, symptom chips, sleep/meds/HR/activity
~/.config/systemd/user/pipnaru.service   # per-user unit, survives reboot
```

## API contract

- `GET /api/stats` →
  `{hp, stamina, focus, hydration, status, buffs[], debuffs[], last_entry, pain?,
  energy_raw?, pain_raw?}` — parsed from `~/health/adora.md` + `~/health/logs/quicklog.md`;
  buffs/debuffs **dedup'd** (`list(dict.fromkeys(...))`) because two files double-count.
- `GET /api/logs?n=7` → `{entries: [{date, energy, pain, raw}]}` — splits quicklog on
  `\n(?=\*\*20\d\d-\d\d-\d\d)`.
- `POST /api/log` (JSON) → appends a human-readable markdown block to
  `~/health/logs/quicklog.md`, returns `{"ok": true}`.
- `GET /api/quests` + `POST /api/quests` (toggle/add) → quests persisted to
  `~/health/logs/quests.json`.

## Rich log schema keys (all optional except energy+pain)

```
energy (0-10), pain (0-10), pain_locs,             # required pair = energy+pain
pem, dizzy, fog, nausea, neck, sensory, flulike, dehyd,  # symptom booleans
sleep_hrs, sleep_qual (0-3), hr,                   # vitals
meds, cannabis, water, activity, triggers, mood, note
```
**activity/load is the clinically-critical field** — PEM is delayed 24–48h, so a
Wednesday crash needs Monday's exertion logged to be explainable. This is what
makes the log useful to a doctor/SSI, not just a diary.

## Tailnet serving

- Box = `narusya` @ `100.77.142.40`; phone = `shellmobile`. Bind `0.0.0.0` so the
  phone can open `http://100.77.142.40:8765/`.
- Plain-HTTP warning on the phone is expected — own net, safe.

## Persistence (proven) — systemd per-user service, NOT foreground

1. Write `~/.config/systemd/user/pipnaru.service`:
   `[Service] Type=simple, WorkingDirectory=..., ExecStart=/usr/bin/python3 .../server.py,
    Restart=on-failure`
2. `loginctl enable-linger <user>` — survive pre-login.
3. `systemctl --user enable --now pipnaru.service` → `is-active` = active.
4. **Restart of a systemd service requires an explicit USER approval** — the agent
   cannot do it autonomously (hit in /loop). Batch all `server.py` edits, get ONE
   user-approved restart at the end. **HTML/CSS/JS asset edits need NO restart** —
   the handler serves them fresh from disk.

## OSS verify-and-plug rule (Adora's explicit working principle)

Prefer **found, verified, plugged-in open source over scratch art**:

1. **License check**: repo LICENSE (try `main` then `master`) + npm registry
   (`https://registry.npmjs.org/<name>` → `.license`, `.repository.url`).
   Apache-2.0/MIT = clean for this use.
2. `npm pack <pkg>` → tarball; inspect license, dist builds, data files.
3. Copy the UMD/asset into `lib/` + keep LICENSE (+ NOTICE) beside it.
4. Wire in with a `<div>` fallback so a failing lib still shows the data.
The body map (Apache-2.0 filtered muscle chart) was adopted this way and replaced
the hand-drawn silhouette.

## `index.html` tab-loader behavior (critical)

The shell fetches each `tabs/<name>.html` and injects it via `innerHTML`. **This
strips all `<script>` tags** — including `<script src=...>` external library loads
inside a tab file. Load shared libs at the **SHELL level** (before the tab loader),
NOT inside tab markup, or the component never loads when the tab is shown.

## Build/test loop that works (copy these)

1. `curl -s http://localhost:8765/api/stats` → real JSON (not mock).
2. `curl -s -X POST http://localhost:8765/api/log -H "Content-Type: application/json"
   -d '{...}'` → `{"ok": true}`; check the file grew.
3. Browser-load `http://localhost:8765/`, assert every tab renders.
4. Browser-console fetch exercises the real user path:
   `(async()=>{ const r=await fetch('/api/log',{method:'POST',...}); return JSON.stringify(await r.json()); })()`
5. **Scrub test entries afterwards** — slice the quicklog via Python at the test
   marker. Test scratch never lives in a medical log.
6. Seeded default files (e.g. quests.json) re-init fresh when the file is empty —
   that's by design.

## Gotchas hit live (all fixed)

- `re.search` grabs the **FIRST** match in the log — that showed morning E4/P3
  instead of the latest E0/P7. For a health tool the **latest entry wins**: use
  `re.findall(pat, blob, re.I)[-1]` for energy/pain.
- **0–10 log value vs 0–100 bar.** Energy logs as 0-10 but the bar surface is
  0-100. `stamina = energy * 10` and label with the raw value (`E0/10`). Drawing
  raw 0-10 straight onto a 0-100 bar shows a 4% bar for a 4/10 — misreads as far
  sicker than reality.
- ID mismatch between HTML element ids and JS refs (dead bar, no value). Verify
  with a console fetch.
- `.chip` styles were missing from the shared CSS when LOG tab first rendered —
  add chip styles to the theme up front.
- `server.py` first draft had `ROOT` undefined — derive `BASE` from `__file__`,
  pass `directory=BASE` to `SimpleHTTPRequestHandler`.
- Browser `snapshot` didn't expose tab ref ids; drive tabs via `browser_console`
  JS (`document.querySelector('.tab.active').dataset.tab`,
  `document.querySelector('[data-tab="data"]').click()`).
- Honesty on derived vs base stats: if HP/FOCUS are placeholder defaults, label
  them "base" — never pass them off as derived from the log.

## Research anchors (schema justification)

- DePaul Symptom Questionnaire-2 (DSQ-2) — validated ME/CFS domains: PEM, cognitive,
  fever/flu, pain, sleep disruption, orthostatic, genitourinary, temperature.
- Canadian Consensus Criteria (CCC) — PEM + sleep + pain + ≥2 neuro/cog + ≥1 from
  two of autonomic/neuroendocrine/immune.
- Energy envelope / pacing — Leonard Jason; RTHM; 50% rule; Workwell RHR+15.
- App precedents: Bearable, Visible, ME/CFS Tracker (30s min quick-log bar).
- Fallout Pip-Boy 3000 tab architecture (STAT/INV/DATA/MAP/RADIO) as cosmetic skin —
  data stays honest.