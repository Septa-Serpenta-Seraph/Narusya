---
name: aegis-dashboard
description: Sovereign agent infrastructure dashboard — container monitoring, visual cortex, memory persistence, and autonomy metrics. Built for the Nous Research Hermes Hackathon.
version: 1.0.0
author: Adora + Narusya
tags: [aegis, dashboard, flask, containers, monitoring, hackathon]
dependencies: [flask, flask-socketio, docker, qdrant-client, pyyaml]
---

# AEGIS Dashboard — DAEMON_EYE_v1

Sovereign agent infrastructure dashboard that monitors containers, processes visual data through a "cognitive cortex" pipeline, persists memory via Qdrant, and exposes agent autonomy metrics (model status, credits, gateway health).

## Quick Start

```bash
cd /home/adora/workspace/AEGIS-Dashboard
source venv/bin/activate
python3 app.py
# Dashboard: http://localhost:5000
```

**Requires:**
- Qdrant running on port 6333: `docker start aegis-qdrant`
- Hermes gateway running (shows uptime in Autonomy tab)
- OpenRouter API key configured for credits display

## Architecture

```
AEGIS-Dashboard/
├── app.py                    # Flask + SocketIO main app (~800 lines)
├── templates/index.html      # Single-page dashboard (5 tabs)
├── data/                     # SQLite persistence
├── recordings/               # Demo video recordings
├── dream_engine/             # Electric Sheep concept
├── persistence/              # Container state tracking
├── tryhackme_api.py          # TryHackMe integration
├── discord_webhook.py        # Discord notifications
└── venv/                     # Python 3.12 virtualenv
```

## Dashboard Tabs

### 1. Vision (tab-vision)
- **URL scanner** — input URL, Playwright takes screenshot, extracts text
- **Screenshot archive** — browsable gallery with timestamps
- **Vision Lock** — pin important screenshots to top
- **API:** `POST /api/vision/scan`, `GET /api/vision/screenshots`

### 2. Memory (tab-persistence)
- **Container history** — tracks state changes over time
- **Qdrant integration** — persistent vector memory
- **Screenshot persistence** — links screenshots to container events
- **API:** `GET /api/persistence/containers/history`

### 3. Autonomy (tab-autonomy)
- **Model & Credits** (top row):
  - MODEL — short name from config (e.g., `hunter-alpha`)
  - PROVIDER — from config (e.g., `openrouter`)
  - CREDITS USED — live from OpenRouter `/api/v1/auth/key`
  - GATEWAY — `pgrep` + uptime from process
- **Usage & Cost**: total cost USD from OpenRouter live API
- **Active Guardrails**: real system state, NOT hardcoded:
  - Docker Resource Monitoring (container count from docker stats)
  - Gateway Heartbeat (process check)
  - Vector Memory Active (Qdrant collections count)
  - Authenticated Provider (OpenRouter key present)
  - Sandboxed Browser (Chromium availability)
- **API:** `GET /api/autonomy/model`, `GET /api/autonomy/metrics`, `GET /api/autonomy/guardrails`

### 4. Supervisor (tab-chat)
- **Agent chat interface** — send commands to agent supervisor
- **Log viewer** — real-time system logs
- SocketIO-based for live updates

### 5. Container Monitor (main view)
- **Live Docker container list** — ID, name, image, status
- **REFRESH** button — rescans Docker daemon
- **LOGS** per container — click to view output
- **CPU / MEM stats** — via container stats API
- **SocketIO** — real-time container state updates

## Key Endpoints

| Method | Route | Purpose |
|--------|-------|---------|
| GET | `/` | Dashboard HTML |
| GET | `/api/containers` | List Docker containers |
| GET | `/api/containers/<id>/stats` | Container resource usage |
| POST | `/api/vision/scan` | Screenshot a URL |
| GET | `/api/vision/screenshots` | List archived screenshots |
| GET | `/api/autonomy/model` | Model, provider, credits, gateway status |
| GET | `/api/autonomy/metrics` | Token usage and cost metrics |
| GET | `/api/autonomy/guardrails` | Agent behavioral constraints |
| GET | `/api/health` | System health check |
| GET | `/api/context` | Get session context notes |
| POST | `/api/context` | Save context note |

## Recording Demo Videos

Uses Playwright's built-in recording (no display server needed):

```python
from playwright.async_api import async_playwright
import os, shutil

async def record():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir="./recordings",
            record_video_size={"width": 1920, "height": 1080}
        )
        page = await context.new_page()
        await page.goto("http://localhost:5000", wait_until="networkidle")
        # ... interact with tabs, click buttons ...
        video_path = await page.video().path()
        await context.close()  # saves video
        browser.close()
        
        # Convert: ffmpeg -i input.webm -c:v libx264 -preset fast -crf 23 output.mp4 -y
```

## Common Issues

| Issue | Fix |
|-------|-----|
| Port 5000 in use | `lsof -ti:5000 \| xargs kill` |
| Qdrant down | `docker start aegis-qdrant` |
| Trio conflict after selenium | `pip uninstall trio trio-websocket -y` |
| No model/credits showing | Check OPENROUTER_KEY is set in Hermes env config |
| Autonomy tab empty | Ensure `<div id="autonomy-view">` wrapper exists in HTML |
| Recordings dir is 22MB+ | Add `recordings/` to .gitignore before pushing |
| Gateway shows OFF | Run `hermes gateway` in background |
| Tab covers all others | Tailwind `.flex` + `.hidden` conflict. Use `style.display` in JS instead of classList toggling |
| Node Playwright video null | Video recording only works with Python async Playwright, not Node.js |
| Port 5000 AEGIS crashes | Use `nohup python3 app.py > /tmp/aegis.log 2>&1 &` and check for trio/selenium conflicts |

## Renaming Notes

Tab renamed from "Sovereignty" to "Autonomy" (2026-03-13) for hackathon entry.
- Routes: `/api/autonomy/*`
- JS: `loadAutonomyData()`, `tab-autonomy`, `autonomy-view`
- Python: `get_autonomy_metrics()`, `get_live_autonomy_metrics()`, `get_model_info()`
