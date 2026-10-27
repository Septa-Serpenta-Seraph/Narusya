# PIPNARU — Full Build Detail (2026-08-19)

Self-hosted body-health terminal for Adora: three-tab **PIP-NARU** (STAT/DATA/LOG),
green CRT phosphor theme. Built from scratch in one session; all lessons below hit live.

## File layout (~/body-panel/)

```
server.py              # Python stdlib http.server, binds 0.0.0.0:8765, /api/* handlers
index.html             # tab shell: rotary tab band (STAT/DATA/LOG), fetches tabs/*.html,
                       # arrow-key navigation, clock + date in top bar
css/pip.css            # shared theme: --ph:#4aff6a phosphor, scanlines, vignette, .fill bars
js/api.js              # API.stats() / API.logs(n) / API.log(payload) fetch wrappers
tabs/stat.html         # pipgirl SVG silhouette + HP/STAM/HYDR/FOCUS bars + effects,
                       # auto-refresh every 15s via /api/stats
tabs/data.html         # last-7-entries energy/pain trend table via /api/logs
tabs/log.html          # rich input form: sliders, symptom chips, sleep/meds/HR/activity,
                       # POSTs to /api/log; minimum = energy+pain only
```

## API contract

- `GET /api/stats` →
  `{hp, stamina, focus, hydration, status, buffs[], debuffs[], last_entry, pain?}`
  Parsed from `~/health/adora.md` + `~/health/logs/quicklog.md`; buffs/debuffs
  **dedup'd** (`list(dict.fromkeys(...))`) because two log files double-count.
- `GET /api/logs?n=7` → `{entries: [{date, energy, pain, raw}]}` — splits the
  quicklog on `\n(?=\*\*20\d\d-\d\d-\d\d)`.
- `POST /api/log` (JSON body) → writes a human-readable markdown block to
  `~/health/logs/quicklog.md`, returns `{"ok": true}`.

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

- Box = `narusya` @ `100.77.142.40`; phone = `shellmobile`. `python3 server.py`
  binds `0.0.0.0` so the phone can open `http://100.77.142.40:8765/`.
- Plain-HTTP warning on the phone is expected — own net, safe.
- Foreground http.server dies on reboot / /stop — tell the user it needs a
  relaunch or offer a startup script (was offered, not built yet).

## E2E verification (the loop that proved it without a human click)

1. `curl -s http://localhost:8765/api/stats` → real JSON.
2. `curl -s -X POST http://localhost:8765/api/log -H "Content-Type: application/json"
   -d '{...full payload...}'` → `{"ok": true}`; check file grew.
3. Browser-load `http://localhost:8765/`, assert all three tabs render.
4. Browser-console fetch exercises the true user path:
   `(async()=>{ const r=await fetch('/api/log',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...})}); return JSON.stringify(await r.json()); })()`
5. **Scrub test entries afterward** — slice the quicklog via Python at the test
   marker so the daemon's scratch never lives in the human's medical log.

## Gotchas hit live (all fixed)

- GRC: browser snapshot didn't expose tab ref IDs; used `browser_console` JS to
  drive tab clicks and verify `document.querySelector('.tab.active').dataset.tab`.
- ID mismatch: stat.html HTML used `stHp/stSt/stHy/stFo` but early JS referenced
  `hpFill/stFill/...` — patch to match before multi-tab integration.
- `.chip` styles were missing from the shared CSS when LOG tab first rendered —
  add chip styles to the theme up front.
- `server.py` first draft had `ROOT` undefined — define `BASE` from `__file__` and
  pass `directory=BASE` to `SimpleHTTPRequestHandler`.

## Research anchors (schema justification)

- DePaul Symptom Questionnaire-2 (DSQ-2) — validated ME/CFS domains: PEM,
  cognitive, fever/flu, pain, sleep disruption, orthostatic, genitourinary, temp.
- Canadian Consensus Criteria (CCC) — PEM + sleep + pain + ≥2 neuro/cog + ≥1 from
  two of autonomic/neuroendocrine/immune.
- Energy envelope / pacing — Leonard Jason; RTHM blog; 50% rule; Workwell RHR+15.
- App precedents: Bearable, Visible, ME/CFS Tracker (30-second quick log best practice).
- Fallout Pip-Boy 3000 tab architecture (STAT/INV/DATA/MAP/RADIO) as the UI skin
  precedent — cosmetic only; data stays honest.