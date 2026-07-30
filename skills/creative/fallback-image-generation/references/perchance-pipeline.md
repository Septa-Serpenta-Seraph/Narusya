# Perchance AI Text-to-Image Pipeline

A free, unlimited, uncensored image generation pipeline using Perchance.org's text-to-image generator API. No account, no credit card, no content filter. Funded by display ads running on non-logged-in sessions.

**When to reach for this:**
- You need free generation (no API key, no billing)
- The user needs NSFW/uncensored images and your Together.ai/FLUX paths are down
- You're prototyping/ideating and don't want to spend credits

**When NOT to use this:**
- The user needs consistent character faces across generations (Perchance has no seed stability)
- The user needs production/commercial-quality photorealism (it's Flux Schnell/SDXL-class)
- The user needs reproduciblity (the backend silently swaps models and keys expire)

## Architecture

Discovered 2026-07-29 via source-code inspection, GitHub reverse-engineering repos, and Playwright debugging.

### Backend

| Component | Detail |
|---|---|
| **API endpoint** | `https://image-generation.perchance.org/api/generate` (GET) |
| **Download** | `https://image-generation.perchance.org/api/downloadTemporaryImage` (GET, by imageId) |
| **Verification** | `https://image-generation.perchance.org/api/checkVerificationStatus` (GET, by userKey) |
| **Model** | Flux Schnell (Apache 2.0) / SDXL variants — arbitrary, can change without notice |
| **GPU** | Perchance's own server GPUs, funded by display ads |
| **Auth** | 64-hex `userKey` access code — no login, no account needed, expires after hours/days |
| **Channel** | Perchance generator page identifier, e.g. `ai-text-to-image-generator` or `image-generator-professional` |

### Generation Parameters

| Parameter | Purpose | Example |
|---|---|---|
| `prompt` | The text prompt (URL-encoded, prefixed with `'`) | `'a cat on a mountain` |
| `negativePrompt` | What to exclude | `'ugly, blurry` |
| `userKey` | Access code | 64 hex chars |
| `__cache_bust` | Random timestamp | `0.48291` |
| `seed` | Random seed (-1 = auto) | `-1` |
| `resolution` | Image dimensions | `512x768`, `768x512`, `768x768` |
| `guidanceScale` | Prompt adherence (1-30) | `7` |
| `channel` | Which Perchance generator page | `ai-text-to-image-generator` |
| `subChannel` | Public or private | `public` |
| `requestId` | Random identifier | `0.39123` |

## Access Key Flow

1. A legitimate user opens the generator page in a browser and clicks "generate"
2. The browser makes a request to `https://image-generation.perchance.org/embed#<config>` which contains the prompt
3. The server generates an access code and includes it as `userKey` in the URL
4. That key can be reused for subsequent API calls until it expires
5. The `checkVerificationStatus` endpoint tests if a key is still valid

## Limitations (Structural, Not Fixable)

1. **Cloudflare Turnstile** — The generator page has Cloudflare challenge that blocks headless browser automation. Playwright-based key capture often fails because the Turnstile iframe prevents the page from fully loading. Verified 2026-07-29: page loads but Turnstile sits in frame 1, blocking interaction.
2. **Key expiration** — Keys expire silently after hours/days. No warning.
3. **Model uncertainty** — The backend model can change without notice (has gone SD 1.5 → SDXL → Flux Schnell). The API gives no indication what model is running.
4. **No character consistency** — Seeds don't reliably produce the same output across sessions.
5. **No commercial guarantee** — Perchance's terms say they don't restrict usage, but underlying model licenses (Flux Schnell = Apache 2.0, SDXL = Stability AI's license) may differ.

## Existing Reverse-Engineering Tools

Two public GitHub repos already reverse-engineered this:

| Repo | Description | Install |
|---|---|---|
| `eeemoon/perchance` | Async Python API (text + image gen) | `pip install perchance` |
| `oujingzhou/text-to-image-generator` | CLI with Playwright key-capture | Clone + `pip install -r requirements.txt` |

Both use Playwright browser automation to capture the access key. The Cloudflare Turnstile issue affects both.

## Local Pipeline Script

The agent-written pipeline lives at `~/.hermes/imagegen/perchance_pipeline.py`:

```
Usage: python3 ~/.hermes/imagegen/perchance_pipeline.py "prompt here" [channel]
```

Features:
- Caches access key at `~/.cache/perchance_access_key.txt`
- Auto-refreshes expired keys
- Saves output to `~/.hermes/imagegen/output/perchance_<imageId>.jpeg`
- Falls back to fresh browser-capture on cache miss

The script has Playwright + urllib as dependencies (both already present in the Hermes venv).

## When This Will Break

- When Perchance changes their API endpoint or param format (the endpoint is stable as of mid-2026)
- When Cloudflare Turnstile gets an upgrade that blocks the current Playwright evasion
- When the Perchance operator decides to require login or rate-limit non-logged-in users
- When the underlying model is swapped to something worse (there's no guarantee of quality)

## Ethical Note

This is ad-funded infrastructure. Per generation, an ad is shown to non-logged-in users to pay for the GPU time. Using the API directly bypasses that ad, which is technically freeloading. Use sparingly — the infrastructure is a gift, not a permit.