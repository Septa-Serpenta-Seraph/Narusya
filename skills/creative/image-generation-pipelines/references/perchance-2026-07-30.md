# Perchance Pipeline — Session Notes (2026-07-30)

## Discovery Log

### Problem
Cloudflare Turnstile managed mode blocks all headless/automated access to `image-generation.perchance.org`.

### What was tried and failed
- Playwright headless Chromium headless shell → blocked
- Camoufox headless (anti-detection Firefox) → blocked
- Camoufox + Xvfb virtual display (non-headless) → still blocked
- `nodriver` undetected Chrome → no Chrome binary available
- `eeemoon/perchance` Python package → `AuthenticationError`
- `oujingzhou/text-to-image-generator` → same Playwright approach, blocked

### What worked
Playwright with the **full Chromium browser** binary (NOT the headless shell):

- Binary: `~/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome`
- Version: Google Chrome for Testing 145.0.7632.6
- Launch args: `["--no-sandbox", "--disable-blink-features=AutomationControlled"]`
- Context: `browser.new_context()` — NOT `launch_persistent_context()`

The full Chromium passes the Turnstile even in headless mode, while the headless shell does not.

### Pipeline Flow (verified working)

1. `page.goto("https://perchance.org/ai-text-to-image-generator")` — Turnstile passes
2. `page.on("request")` listener captures URLs containing `userKey=`
3. Click ✨ generate button in the iframe (frame 2, the `cd282495464c...perchance.org` subdomain)
4. Wait 8-12s for the API request with `userKey=64-char-hex` to fire
5. `page.goto("/api/verifyUser")` — sets Turnstile cookies in browser context
6. `page.evaluate()` makes the POST to `/api/generate` from within the browser
7. Response includes `imageDownloadUrl` — fetch from within browser context
8. Base64-decode the blob and write to disk

### API Response Format
```json
{
  "status": "success",
  "imageId": "64-char-hex",
  "fileExtension": "jpeg",
  "seed": int,
  "prompt": "string",
  "width": 512,
  "height": 768,
  "guidanceScale": 7,
  "negativePrompt": "",
  "maybeNsfw": false,
  "imageDownloadUrl": "/api/downloadTemporaryImageViaProxy?t=v1.xxx"
}
```

### Key Characteristics
- userKey is a 64-hex-char string (e.g. `7357d01f022a45f7...5c70651f`)
- Valid for hours to days (tested: overnight worked)
- Rate limit: concurrent requests limited per key
- Resolution capped at 768 max dimension
- Model: likely Flux Schnell (not user-selectable)
- NSFW: Perchance explicitly allows it (plugin docs confirm)

### Important Pitfalls
1. **DO NOT use `launch_persistent_context()`** — triggers Turnstile
2. **DO NOT use `user_data_dir`** — triggers Turnstile
3. **DO NOT add `--disable-web-security`** — breaks fetch
4. **DO navigate to verifyUser** — without it, API calls fail with "Failed to fetch"
5. **DO use `new_context()`** — clean context passes Turnstile

### Together.ai LoRA Support
- LoRA parameter: `image_loras: [{"path": "<url>", "scale": 1.0}]`
- Works with `FLUX.1-dev-lora` and `FLUX.2-dev` models
- LoRA URL should point to a `.safetensors` file
- Training: Replicate's `ostris/flux-dev-lora-trainer`