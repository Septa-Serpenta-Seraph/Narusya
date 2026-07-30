# Web API Reverse Engineering — Investigation Technique

**Trigger:** A user asks to understand or replicate how a web-based tool/pipeline works
**Goal:** Map the API endpoints, auth mechanism, model backend, and deployment architecture
**Tools:** `web_search`, `web_extract`, GitHub code analysis, browser automation (Playwright), HTTP clients

## Procedure

### Phase 1: Surface-Level Recon (what model? what license?)

Start with web search to identify the backend model and platform architecture:

```
web_search(query="<service name> model powering" limit=5)
web_search(query="<service name> reverse engineered API" limit=5)
web_search(query="<service name> free unlimited GitHub" limit=5)
```

Look for: Reddit threads announcing model changes, blog posts about the architecture, GitHub repos that already cracked the API.

### Phase 2: GitHub Code Analysis

Search for existing reverse-engineering tools:
- "pip install <packagename>" for Python packages wrapping the service
- GitHub topics: "perchance", "<servicename>-api", "<servicename>-cli"
- Review source code for:
  - API endpoint URLs (often hardcoded as constants)
  - Auth mechanism (API keys, tokens, access codes)
  - Request parameter structure (prompt, resolution, style, seed)
  - Download URLs (how images are retrieved after generation)

### Phase 3: Browser Inspection (if API details are insufficient)

Navigate to the service page with Playwright and inspect network traffic:

```python
from playwright.async_api import async_playwright
captured_urls = []
page.on("request", lambda req: captured_urls.append(req.url))
await page.goto(service_url, wait_until="domcontentloaded")
await page.wait_for_load_state("load")
# Click generate button to trigger the API call
btn = await page.query_selector("button#generateButtonEl")
await btn.click()
await asyncio.sleep(5)  # wait for network traffic
# Extract auth tokens/keys from URL patterns
key = re.search(r'userKey=([a-f\d]{64})', ''.join(captured_urls))
```

**Key patterns to extract from URLs:**
- Access keys / auth tokens (e.g., 64-hex-char `userKey`)
- API base URLs (e.g., `https://image-generation.perchance.org/api/generate`)
- Channel/generator identifiers
- Version numbers or model hints

### Phase 4: Direct API Testing

Once you have the endpoint and auth, test the generation API directly:

```python
import urllib.request
from urllib.parse import urlencode

params = urlencode({
    'prompt': prompt,
    'negativePrompt': neg_prompt,
    'userKey': access_key,
    'resolution': '512x768',
    'guidanceScale': '7',
    'channel': channel_id,
    'subChannel': 'public',
})
response = urllib.request.urlopen(f"{API_URL}?{params}", timeout=30)
data = json.loads(response.read())
image_id = data.get('imageId')
```

### Phase 5: Cloudflare Bypass Assessment

Many free-generation services use Cloudflare Turnstile or similar challenge systems:

- Turnstile in headless mode = blocked page load or incomplete render
- Mitigations tried (none guarantee success):
  - Use full non-headless browser
  - Custom user-agent strings
  - Wait longer for manual challenge completion
  - Use the `perchance` Python package (may handle this internally)
- **Best workaround:** Once you have a valid access key, cache it and use it directly
  via API calls — the key itself bypasses the Turnstile check for subsequent calls

## Known API Details: Perchance.org AI Text-to-Image Generator

| Field | Value |
|-------|-------|
| **API Endpoint** | `https://image-generation.perchance.org/api/generate` |
| **Download** | `https://image-generation.perchance.org/api/downloadTemporaryImage` |
| **Verify Key** | `https://image-generation.perchance.org/api/checkVerificationStatus` |
| **Model** | Flux Schnell (primary) / SDXL variants |
| **Auth** | 64-hex `userKey`, extracted from browser network traffic |
| **Resolution** | `512x512`, `512x768`, `768x512`, `768x768` |
| **Guidance Scale** | Float 1–30, default 7 |
| **Channel** | `ai-text-to-image-generator` or `image-generator-professional` |
| **Content Filter** | None — NSFW allowed |
| **License** | Apache 2.0 (Flux Schnell) |

## Pitfalls

- **Cloudflare Turnstile** blocks headless browser automation — the page won't fully load
- **Access keys expire silently** — cached keys may stop working mid-session
- **Backend model swaps without notice** — the quality/style can change when the author upgrades the page
- **Python venv pollution** — installing the `perchance` package via pip leaves a venv active in the terminal session, causing Python path conflicts for subsequent runs
- **Playwright version mismatch** — the system `playwright` CLI and the Python package's playwright may use different browser binary paths; always install browsers via the same Python interpreter that will run the script
- **Channel parameter matters** — each Perchance generator URL uses a different channel name; mismatched channel = generation failure