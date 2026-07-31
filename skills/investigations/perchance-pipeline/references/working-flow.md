# Perchance Pipeline — Working Flow Transcript

## The Breakthrough (2026-07-30)

After trying Playwright headless shell, Camoufox, nodriver, and various Turnstile bypasses, the solution was:

**Use Playwright's FULL Chromium binary** — not the headless shell.

### Chromium Binary Paths

| Version | Path | Type |
|---------|------|------|
| 1208 | `/home/adora/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome` | Full Chrome for Testing ✅ |
| 1228 | `/home/adora/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome` | Full Chrome for Testing ✅ |
| Headless shell | `...chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell` | ❌ Fails Turnstile |

### What Works

```python
# Launch with FULL Chromium, not headless shell
browser = await p.chromium.launch(
    headless=True,
    executable_path="/home/adora/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome",
    args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
)
```

### The verifyUser Step

After capturing the userKey from network traffic, navigating to the verifyUser endpoint is CRITICAL — it sets the Turnstile session cookie that makes subsequent API calls work:

```python
await page.goto(
    f"https://image-generation.perchance.org/api/verifyUser?thread=0&__cacheBust={random.random()}",
    wait_until="domcontentloaded",
    timeout=30000
)
await page.wait_for_timeout(5000)
```

### API Call from Browser Context

All API calls must be made from within the browser's page context (using `page.evaluate`) because the Turnstile cookie only exists in the browser session:

```python
result = await page.evaluate("""
    async ({ userKey, prompt, resolution, negative_prompt, guidance_scale }) => {
        const url = `https://image-generation.perchance.org/api/generate?userKey=${userKey}&requestId=aiImageCompletion${Math.floor(Math.random() * 2**30)}&__cacheBust=${Math.random()}`;
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                generatorName: 'ai-image-generator',
                channel: 'ai-text-to-image-generator',
                subChannel: 'public',
                prompt: prompt,
                negativePrompt: negative_prompt,
                seed: -1,
                resolution: resolution,
                guidanceScale: guidance_scale
            })
        });
        return await response.json();
    }
""", {
    "userKey": user_key,
    "prompt": prompt,
    "resolution": resolution,
    "negative_prompt": negative_prompt,
    "guidance_scale": guidance_scale
})
```

### Proxy Download

The API response includes `imageDownloadUrl` — use this for downloading, NOT the `downloadTemporaryImage` endpoint:

```python
proxy_url = f"https://image-generation.perchance.org{result['imageDownloadUrl']}"
dl_result = await page.evaluate("""
    async (url) => {
        const response = await fetch(url, { credentials: 'include' });
        const blob = await response.blob();
        const reader = new FileReader();
        return await new Promise(resolve => {
            reader.onloadend = () => resolve({ data: reader.result.split(',')[1], size: blob.size });
            reader.readAsDataURL(blob);
        });
    }
""", proxy_url)
```

### Failed Approaches

| Approach | Result | Why |
|----------|--------|-----|
| Playwright headless shell (chromium-1208) | ❌ Turnstile blocks | Headless shell detected as bot |
| Playwright headless shell (chromium-1228) | ❌ Turnstile blocks | Same issue |
| Camoufox (headless, Firefox) | ❌ Turnstile blocks | Anti-detection not enough |
| Camoufox + Xvfb (non-headless) | ❌ Still blocked | Turnstile managed mode too strict |
| nodriver (undetected Chrome) | ❌ Binary not found | Playwright headless shell incompatible |
| eeemoon/perchance Python package | ❌ AuthenticationError | Package predates Turnstile |
| Direct curl to API endpoints | ❌ Cloudflare challenge | All endpoints behind Turnstile |
| curl with userKey from browser | ❌ Cloudflare on API too | Turnstile per-request, not per-session |