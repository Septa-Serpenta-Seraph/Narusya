---
name: visible-import-bridge
description: "Import Visible ME/CFS CSV exports into PIPNARU."
version: 1.0.0
author: Narusya
tags: [hermes, visible, me-cfs, pipnaru, health, csv, import]
---

# Visible → PIPNARU Import Bridge

## When to Use
- Adora sends a **Visible** CSV export (`Visible_Data_Export_*.csv`) in Discord/chat.
- She asks to "import Visible data," "add Visible to the terminal," or wants her ME/CFS app data shown in PIPNARU.
- Re-curating her real symptom history from the app across dates.

## Source
- Visible is a real mobile app (visiblehealth.com) for ME/CFS/Long Covid pacing (stability score, HRV, symptoms, functional capacity).
- Export arrives as e.g. `Visible_Data_Export_2026-8-20.csv`, saved by Hermes to `~/.hermes/document_cache/doc_*.csv`.
- Columns: `observation_date, tracker_name, tracker_category, observation_value`.

## Steps
1. **Copy** the doc-cache CSV into the project imports dir (stable path):
   ```bash
   mkdir -p ~/body-panel/imports
   cp ~/.hermes/document_cache/<the_export.csv> ~/body-panel/imports/visible_<date>.csv
   ```
2. **Run the import script** (parses → normalized JSON per date):
   ```bash
   cd ~/body-panel && python3 import_visible.py imports/visible_<date>.csv
   ```
   Writes `imports/visible.json` (overwrites with latest). Categories preserved:
   Measurement/Sleep (HRV, Resting HR, Sleep), Funcap_* → funcap profile, Experience → flags (Crash etc.), all others → symptom categories.
3. **Verify API serves it** (service must be running — `pipnaru.service`):
   ```bash
   curl -s http://localhost:8765/api/visible | python3 -m json.tool | head
   ```
   → Should show `source: visible`, `updated: <today>`, and `days` keyed by date.
4. **No restart needed** for file-only changes; restart the service only if `server.py` changed:
   ```bash
   systemctl --user restart pipnaru.service
   ```
5. **Confirm UI**: open `http://100.77.142.40:8765/` → DATA tab → "VISIBLE IMPORT" card shows the newest day(s) with measurements, symptom severities, and crash/experience flags.

## Files
- `~/body-panel/import_visible.py` — parser (CSV → JSON).
- `~/body-panel/imports/visible.json` — live import the server reads.
- `~/body-panel/tabs/data.html` — renders the Visible card via `/api/visible`.

## Pitfalls / notes
- Export may contain **many zero-valued symptom rows** — the UI filters to severity ≥2 for the "hurt" list and counts functional-capacity items. Don't drop zeros in the JSON (statistics like "17/70 absent" need them).
- CSV can have **multiple rows per tracker** (e.g. HRV 59 + Resting HR 65 on 8/19 vs 62/62 on 8/20) — parser keeps last per name per date.
- The bridge is deliberately *one-way, file-based*. Visible captures; PIPNARU visualizes. Keep Visible as the mobile capture layer; don't rebuild its form in-platform.
- **Consent/privacy**: data stays on Tailnet; the CSV stays on disk. Never push Visible data to external services.

## Relationship
Complements the memory-systems and PIPNARU lore; part of the "plug verified OSS, scratch only the bridge" philosophy with Adora.