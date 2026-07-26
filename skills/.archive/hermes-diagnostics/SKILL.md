---
name: hermes-diagnostics
description: Diagnose and fix common Hermes Agent issues — broken browser tools, PATH problems, stale sockets, gateway connectivity.
category: software-development
triggers:
  - "browser tool not working"
  - "agent-browser not found"
  - "gateway issues"
  - "playwright broken"
---

# Hermes Agent Diagnostics

## When browser_* tools fail

Symptoms: `browser_navigate`, `browser_screenshot`, etc. all return errors or empty responses.

### Diagnosis
```bash
# Check if agent-browser exists
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

# Restart gateway (PATH is cached)
hermes gateway restart
# Or use /restart in Discord
```

### Fallback
If browser tools still broken, use Playwright scripts directly:
```python
from playwright.sync_api import sync_playwright
# Scripts work even when agent-browser wrapper doesn't
```

## Stale Socket Cleanup
```bash
# Playwright sockets accumulate and can cause hangs
find /tmp -maxdepth 1 -name 'playwright*' -type d -mmin +60 -exec rm -rf {} + 2>/dev/null
```

## Gateway Health
```bash
# Check gateway process
ps aux | grep hermes-gateway
# Check logs
tail -50 ~/.hermes/logs/gateway.log
```

## Image Analysis Fallback: Tesseract OCR

When `vision_analyze` fails with "No endpoints found that support image input" (model doesn't have vision), and the image is a local file (e.g., from `~/.hermes/image_cache/`), fall back to Tesseract OCR:

```bash
# Check if tesseract is available
which tesseract

# OCR an image file directly
tesseract /path/to/image.jpeg stdout 2>/dev/null
```

**When to use:**
- `vision_analyze` returns 404 (model doesn't support images)
- Image is a local file (not a Discord CDN URL — those return "content no longer available")
- Image contains text (screenshots, chat logs, documents)

**Limitations:**
- Tesseract works best on clean text screenshots; noisy/complex layouts may produce garbled output
- Discord CDN image URLs cannot be accessed by either `vision_analyze` or `tesseract` — only locally cached copies work
- For images that are purely visual (photos, art), neither method works without a vision-capable model

See `references/ocr-fallback.md` for full details and workflow.

## Hermes Dashboard (Web UI) — Access via API

When browser tools (`browser_navigate` etc.) can't render the dashboard (no Playwright daemon, broken socket, etc.), hit the API endpoints directly from the VM.

### Find the dashboard port
```bash
ss -tlnp | grep hermes
# Look for the port bound to 127.0.0.1 (e.g., 9119)
```

### Available API endpoints
```bash
# System status (JSON)
curl -s http://127.0.0.1:9119/api/status

# Session list
curl -s http://127.0.0.1:9119/api/sessions

# Root / returns HTML (React app) — NOT useful from curl
curl -s http://127.0.0.1:9119/
```

### Key endpoints
| Endpoint | Returns | Notes |
|----------|---------|-------|
| `/api/status` | JSON | Version, gateway state, platform status, active sessions |
| `/api/sessions` | JSON array | All sessions with metadata, system prompt, token counts |

### From external machine (SSH tunnel)
The dashboard binds to `127.0.0.1` by default. To access from the host machine:
```bash
ssh -L 9119:127.0.0.1:9119 adora@narusya
# Then visit http://127.0.0.1:9119 in browser
```

### Quick system health check via API
```bash
curl -s http://127.0.0.1:9119/api/status | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'Version: {d[\"version\"]} ({d[\"release_date\"]})')
print(f'Config version: {d[\"config_version\"]} (latest: {d[\"latest_config_version\"]})')
print(f'Gateway: {d[\"gateway_state\"]} (PID: {d[\"gateway_pid\"]})')
for platform, info in d.get('gateway_platforms', {}).items():
    print(f'{platform}: {info[\"state\"]}')
print(f'Active sessions: {d[\"active_sessions\"]}')
"
```

### Methodical bug investigation approach
When dashboard shows errors:
1. **Check logs first** — `grep "error_pattern" ~/.hermes/logs/errors.log | tail -5`
2. **Get full traceback if available** — `grep -A10 "error_pattern" ~/.hermes/logs/errors.log`
3. **Check if bug is already fixed** — `grep -n "offending_code" path/to/file.py` + check file modification time (`ls -la`)
4. **Verify current state** — run the code or check the service is working
5. **Report findings with evidence** — show the date range, occurrence count, and current code state
