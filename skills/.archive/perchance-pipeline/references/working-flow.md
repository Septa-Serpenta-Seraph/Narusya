# Perchance Pipeline — Working Flow Transcript

## The Breakthrough (2026-07-30)

After trying Playwright headless shell, Camoufox, nodriver, and various Turnstile bypasses, the solution was:

**Use Playwright's FULL Chromium binary** — not the headless shell.

### Chromium Binary Paths

| Version | Path | Type |
|---------|------|------|
| 1208 | `~/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome` | Full Chrome for Testing ✅ |
| 1228 | `~/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome` | Full Chrome for Testing ✅ |
| Headless shell | `...chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell` | ❌ Fails Turnstile |

### What Works

```python
browser = await p.chromium.launch(
    headless=True,
    executable_path="/home/adora/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome",
    args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
)
```

### The verifyUser Step

After capturing the userKey from network traffic, navigating to verifyUser is CRITICAL:

```python
await page.goto(
    f"https://image-generation.perchance.org/api/verifyUser?thread=0&__cacheBust={random.random()}",
    wait_until="domcontentloaded", timeout=30000
)
await page.wait_for_timeout(5000)
```

### API Call from Browser Context

All API calls must use `page.evaluate()` so the Turnstile cookie from the browser session authenticates the request:

```python
result = await page.evaluate("""
    async ({ userKey, prompt, resolution, negative_prompt, guidance_scale }) => {
        const url = `https://image-generation.perchance.org/api/generate?userKey=${userKey}&requestId=aiImageCompletion${Math.floor(Math.random() * 2**30)}&__cacheBust=${Math.random()}`;
        const response = await fetch(url, { method: 'POST',
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
""", {"userKey": user_key, "prompt": prompt, "resolution": resolution, ...})
```

### Proxy Download

Use `imageDownloadUrl` from the API response, NOT the `downloadTemporaryImage` endpoint:

```python
proxy_url = f"https://image-generation.perchance.org{result['imageDownloadUrl']}"
```

## Key Capture Debugging (2026-07-31)

### Symptoms of Stale Key

When the cached key file still exists but is expired:
- The page loads fine (title: "AI Image Generator (free, no sign-up, unlimited)")
- The generate button is found and clicked
- Network traffic shows `userKey=OLD_KEY` in the generate URLs
- API returns `status: "invalid_key"`

### The Fix

1. Delete the cache file: `rm -f ~/.cache/perchance_access_key.txt`
2. Re-run — the script will capture a fresh key from network traffic

### Why It Happens

The Perchance page caches the userKey in browser localStorage. Even with `browser.new_context()` (which should be a fresh context), the key persists because it's served from the page's JavaScript context, not from cookies/storage. The browser instance itself remembers the key across context creations.

Using `launch_persistent_context()` with a completely fresh data directory FAILS — it triggers the Cloudflare Turnstile challenge and shows "Just a moment..." as the page title. Stick with `new_context()`.

### Network Traffic Pattern (Working)

When the page loads and generate is clicked, the key capture listener catches URLs containing:
- `verifyUser?thread=0&__cacheBust=...` — multiple calls to the auth endpoint
- `generate?userKey=64-char-hex&requestId=...&adAccessCode=&__cacheBust=...` — the actual API call

## Failed Approaches

| Approach | Result | Why |
|----------|--------|-----|
| Playwright headless shell | ❌ Turnstile blocks | Headless shell detected as bot |
| Camoufox headless | ❌ Turnstile blocks | Anti-detection not enough for managed mode |
| Camoufox + Xvfb non-headless | ❌ Still blocked | Turnstile managed mode too strict |
| nodriver (undetected Chrome) | ❌ Binary not found | Playwright headless shell incompatible |
| eeemoon/perchance Python package | ❌ AuthenticationError | Package predates Turnstile |
| Direct curl to API | ❌ Cloudflare challenge | All endpoints behind Turnstile |
| curl with userKey from browser | ❌ Cloudflare on API too | Per-request Turnstile |
| Launch persistent context (fresh profile) | ❌ Cloudflare blocks | Fresh profile re-triggers Turnstile |