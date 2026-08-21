---
name: fatiguesense-import-bridge
description: "Import FatigueSense ME/CFS data exports into PIPNARU."
version: 1.0.0
author: Narusya
tags: [hermes, fatiguesense, me-cfs, pipnaru, health, csv, pem, import]
---

# FatigueSense → PIPNARU Import Bridge

## When to Use
- Adora sends a **FatigueSense** data export zip (`fatiguesense_data_*.zip` / a folder of numbered CSVs) in Discord/chat.
- She asks to "import FatigueSense," "add the pacing app to PIPNARU," or wants PEM-episode + energy-budget data shown alongside Visible.
- Parallel to the existing `visible-import-bridge` (Visible = capture, PIPNARU = visualize).

## Source
- FatigueSense is a ME/CFS pacing app. Export arrives as a **zip** containing `fatiguesense_data/` with numbered CSVs:
  `00_summary` `01_pem_episodes` `02_daily_overview` `03_daily_metrics_long` `04_check_ins` `05_sleep` `06_heart_and_hrv` `07_activity` `08_energy_budget` `09_strain_and_recovery` `10_notes` + `README.txt`.
- Each CSV is CRLF, `csv.reader` handles it. Day boundary = the app's "energy day" (starts 00:00 local).

## Steps
1. **Extract** the zip into a temp dir, then copy the `fatiguesense_data/` folder into the stable import dir:
   ```bash
   python3 -c "import zipfile; zipfile.ZipFile('<doc_cache zip>').extractall('/tmp/fs')"
   mkdir -p ~/body-panel/imports/fatiguesense
   cp -r /tmp/fs/fatiguesense_data/* ~/body-panel/imports/fatiguesense/
   ```
2. **Run the importer** (writes consolidated JSON):
   ```bash
   cd ~/body-panel && python3 import_fatiguesense.py imports/fatiguesense
   ```
   → `imports/fatiguesense.json` with `source/summary/pem_episodes/days{date:{overview,metrics,checkins,energy_budget}}/notes`.
3. **Verify API** (endpoint added 8/20; needs a service restart if server.py changed):
   ```bash
   systemctl --user restart pipnaru.service
   curl -s http://localhost:8765/api/fatiguesense | python3 -m json.tool | head
   ```
   → `source: fatiguesense`, `pem_episodes`, `days` keyed by date.
4. **Confirm UI**: DATA tab → "▚ FATIGUESENSE (pacing · PEM)" card. Shows PEM banner (trigger/start/still-open), then newest-day rows with fatigue/energy/HRV/steps/energy-points-used, and a red mood/phys-fatigue note when the day was hard.

## Files
- `~/body-panel/import_fatiguesense.py` — parser (CSV folder → JSON).
- `~/body-panel/imports/fatiguesense.json` — live import the server reads.
- `~/body-panel/imports/fatiguesense/` — raw export CSVs.
- `~/body-panel/tabs/data.html` — renders the card via `/api/fatiguesense`.
- `~/body-panel/server.py` — `FATIGUESENSE_FILE`, `load_fatiguesense()`, `/api/fatiguesense`.

## Pitfalls / notes
- FatigueSense uses **0 as a real recorded zero** for unmeasured days (HRV 0, RHR 0, steps 0) — the importer keeps them, but the UI hides `0` values so a no-data day doesn't show noise.
- Ratings are **own-scale 0–100** (fatigue higher=worse, energy higher=better); PEM severity is **1–5**. Don't confuse the two scales with quicklog's 0–10 energy/pain.
- The README.txt has honest caveats (consumer wearable error, PEM episodes are self-reported) — mirror that tone in any summary; these numbers describe but don't diagnose.
- One-way, file-based, Tailnet-only. Never push this data to external services.

## Relationship
Sister skill to `visible-import-bridge`; part of the "plug verified OSS, scratch only the bridge" philosophy with Adora.
