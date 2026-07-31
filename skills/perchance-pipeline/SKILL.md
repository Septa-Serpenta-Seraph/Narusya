---
name: perchance-pipeline
description: "Reverse-engineered Perchance AI text-to-image generator pipeline — free, unlimited, uncensored NSFW image generation."
author: Narusya
platforms: [linux]
---

# Perchance AI Text-to-Image Pipeline

Reverse-engineered API for Perchance's free image generator (https://perchance.org/ai-text-to-image-generator).

## Architecture

- **Backend model**: Flux Schnell (current, per community reports) and/or SDXL-class. Changed over time (SD 1.5 → SDXL → Flux).
- **Funding**: Free, ad-supported. Server GPU inference on Perchance's own hardware.
- **NSFW/uncensored**: No content filters on the backend — forwards prompts directly to the model.
- **Adora use**: Specifically uses this generator because it handles explicit content well.

## API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `https://image-generation.perchance.org/api/generate` | Generate image (POST) |
| `https://image-generation.perchance.org/api/downloadTemporaryImage` | Download generated image by imageId |
| `https://image-generation.perchance.org/api/downloadTemporaryImageViaProxy` | Proxy download (returns immediately) |
| `https://image-generation.perchance.org/api/checkVerificationStatus` | Check if access key is still valid |
| `https://image-generation.perchance.org/api/verifyUser` | Get Turnstile cookies for API calls |

## Cloudflare Turnstile — THE WORKING SOLUTION

**Crucial finding:** The `image-generation.perchance.org` subdomain is fully behind Cloudflare Turnstile (managed mode). Standard `curl` requests, Playwright's headless Chromium SHELL, and Camoufox all fail to bypass it.

**The trick:** Use Playwright's **full Chromium** binary (not the headless shell) — the `chrome-linux64/chrome` binary found at Playwright's Chromium installation path. This full browser passes the Turnstile where the headless shell doesn't.

### Complete Working Flow

The pipeline script lives at `~/.hermes/imagegen/perchance_gen.py` and uses this strategy:

```
Step 1: Navigate to generator page with full Chromium (headless)
Step 2: Wait for page to fully load (Turnstile auto-solves)
Step 3: Click "✨ generate" button (found in any frame)
Step 4: Capture userKey from the network request URL
Step 5: Navigate to verifyUser endpoint to set Turnstile cookies
Step 6: Make API call from within the browser context (page.evaluate)
Step 7: Download via imageDownloadUrl (proxy) from API response
```

**Key details:**

- **Browser path:** `/home/adora/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome`
- **Headless args:** `--no-sandbox`, `--disable-blink-features=AutomationControlled`
- **User-Agent:** `Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/145.0.7632.6 Safari/537.36`
- **Page wait:** 15 seconds after navigation for Turnstile to auto-solve
- **Frame search:** The generate button may be in any frame — iterate all frames, find by text "✨" or "generate"
- **Network capture:** Register a `page.on("request", ...)` handler before clicking, then search captured URLs for `userKey=([a-f\d]{64})`
- **verifyUser navigation:** After getting the key, navigate to `https://image-generation.perchance.org/api/verifyUser?thread=0&__cacheBust=RANDOM` — this sets the Turnstile cookie that makes subsequent API calls work
- **API call:** Execute `fetch()` from within the browser context via `page.evaluate()` — the browser's session cookies are what authenticate the request
- **Download:** The API response includes `imageDownloadUrl` (e.g. `/api/downloadTemporaryImageViaProxy?t=v1.XXX`) — use this proxy URL for downloading, NOT the `downloadTemporaryImage` endpoint (which returns 404 until the image is ready)

### API Request Format

```python
# POST from within browser context
url = f"https://image-generation.perchance.org/api/generate?userKey={KEY}&requestId=aiImageCompletion{RANDOM}&__cacheBust={RANDOM}"
body = {
    "generatorName": "ai-image-generator",
    "channel": "ai-text-to-image-generator",
    "subChannel": "public",
    "prompt": prompt,
    "negativePrompt": "",
    "seed": -1,
    "resolution": "512x768",  # or "768x768" or "768x512"
    "guidanceScale": 7
}
```

### API Response

```json
{
  "status": "success",
  "imageId": "64-hex-id",
  "fileExtension": "jpeg",
  "seed": 123456789,
  "prompt": "...",
  "width": 512,
  "height": 768,
  "guidanceScale": 7,
  "negativePrompt": "",
  "maybeNsfw": false,
  "imageDownloadUrl": "/api/downloadTemporaryImageViaProxy?t=v1.XXXX"
}
```

The `imageDownloadUrl` field is the critical path — use it for immediate download. The `downloadTemporaryImage` endpoint may return 404 until the image is fully processed.

## Files

| File | Purpose |
|------|---------|
| `~/.hermes/imagegen/perchance_gen.py` | Full working pipeline script |
| `~/.hermes/imagegen/perchance_pipeline.py` | Earlier attempt (Playwright-based, now superseded) |
| `~/.hermes/imagegen/README.md` | Reverse-engineering notes |
| `~/.hermes/imagegen/output/` | Generated images |
| `~/.cache/perchance_access_key.txt` | Cached 64-hex userKey (auto-refreshed) |

## Usage

```bash
~/.hermes/hermes-agent/venv/bin/python3 ~/.hermes/imagegen/perchance_gen.py "your prompt here"
```

## Access Key Management

- Keys are 64 hex characters
- Captured from the network request URL when clicking "generate"
- Cached at `~/.cache/perchance_access_key.txt`
- Keys can persist across browser sessions (IP/session-based, not per-launch) — the same key from yesterday may still work today
- **Confirmed:** Key `7357d01f022a45f7...5c70651f` persisted for 12+ hours (through server restart, new browser sessions, etc.) before expiry
- Keys expire after hours/days — when the API returns `status: "invalid_key"`, delete the cached file and re-run to force fresh capture
- **Debugging tip:** When the key capture seems stuck on an old key, check the network-captured URLs — if they all show the same old key, the page is serving it from browser localStorage. The `browser.new_context()` inherits it from the browser instance. Using `launch_persistent_context()` with a fresh profile re-triggers the Turnstile (fails). Stick with `new_context()` and just delete the cache file.
- **Important:** The `verifyUser` endpoint now sometimes uses a `?token=` parameter instead of just `?thread=0`. The older `userKey` format still works for API calls as long as the key is valid. When the key expires, a fresh page load + generate click captures a new one automatically.
- No login or account needed

## NSFW Content

- Perchance's plugin documentation explicitly states the model CAN return NSFW results if prompted with NSFW terms
- The API response includes a `maybeNsfw` boolean field — informational only, not a block
- **Prompting for explicit nudity:** Use direct language (&quot;full nudity&quot;, &quot;completely naked&quot;, &quot;visible nipples&quot;, &quot;bare breasts&quot;, &quot;no clothes&quot;). &quot;Artistic nude&quot; and &quot;tasteful&quot; are interpreted conservatively and may not produce nudity — the backend safety classifier reads euphemisms negatively. Direct phrasing beats poetic for explicit output
- Combine visual detail (lighting, texture, expression, setting) with nudity specifications — explicit-only prompts produce flat, lifeless images. The model renders best with full atmospheric context regardless of content
- No `disable_safety_checker` parameter needed — the backend has no content filter. The `maybeNsfw` boolean in the API response is informational, not a block

## References

- `references/working-flow.md` — Full working flow transcript with code examples, failed approaches, and troubleshooting notes

## Known Limitations

- Backend can change silently (author swaps models without notice)
- No character consistency between generations
- Resolution capped at ~1024 on a side
- Requires ~120s for first run (browser launch + page load + Turnstile)
- Generating from headless browser uses ~300MB RAM for the Chromium process
- Playwright's full Chromium binary is ~300MB on disk
- **Download pitfall:** The `downloadTemporaryImage` endpoint returns 404 until the image is fully processed. Always use the `imageDownloadUrl` (proxy URL) from the API response instead — it returns immediately