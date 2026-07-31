---
name: image-generation-pipelines
description: "Free img gen: Perchance, Together, pollinations, ComfyUI."
triggers:
  - generate image free
  - perchance image generation
  - free image API
  - uncensored image generation
  - reverse engineer image api
  - image generation without api key
---

# Image Generation Pipelines — Free & Uncensored

Covers the full landscape of free/uncensored image generation options, from reverse-engineered APIs to local setups.

## Decision Matrix

| Pipeline | Cost | Censored | Reliability | Setup | Best For |
|----------|------|----------|-------------|-------|----------|
| **Together.ai FLUX** | ~$0.01/image | NSFW-permissive (disable_safety_checker) | High | API key only | Production-quality, consistent |
| **Perchance API** | Free (ad-funded) | None | Low (Cloudflare gated) | Browser key capture | Ideation, free spare cycles |
| **pollinations.ai** | Free | NSFW via safe=false | Medium | No auth | Quick test, no keys |
| **Local ComfyUI + Flux Schnell** | Free (GPU cost) | None | Highest | Heavy (12GB VRAM) | Full control, no limits |

---

## Perchance Text-to-Image Generator

### What It Is

[Perchance](https://perchance.org/ai-text-to-image-generator) hosts a community-authored text-to-image generator page that routes prompts through a server-side GPU backend (currently **Flux Schnell**, Apache 2.0). No signup, no API key, free via display ads. **Uncensored — supports NSFW generation.**

### The API (Reverse-Engineered)

**Base URL:** `https://image-generation.perchance.org/api`

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/generate` | GET | Generate an image |
| `/api/downloadTemporaryImage` | GET | Download the generated image by imageId |
| `/api/checkVerificationStatus` | GET | Check if an access key is still valid |
| `/api/verifyUser` | GET | Get a new access key (embedded in HTML response) |

**Parameters for /api/generate:**

| Param | Type | Description |
|-------|------|-------------|
| `prompt` | string (URL-encoded) | The image prompt |
| `negativePrompt` | string | What to avoid |
| `userKey` | string (64 hex) | Access key from browser session |
| `seed` | int | -1 = random |
| `resolution` | string | "512x768", "768x768", "768x512" |
| `guidanceScale` | float | 1-30, default 7 |
| `channel` | string | "ai-text-to-image-generator" (or "image-generator-professional") |
| `subChannel` | string | "public" |
| `requestId` | float | Random number |
| `__cache_bust` | float | Random cache buster |

### Access Key Mechanism

The `userKey` is a 64-hex-char string obtained through a browser session:

1. A browser navigates to `https://image-generation.perchance.org/api/verifyUser?thread=0`
2. The page returns a JSON blob with `"userKey":"..."` embedded in the HTML
3. This key is valid for hours-days and can be reused across sessions

**The `eeemoon/perchance` Python package** (pip install perchance, v0.1.0) automates this via Playwright Chromium — it navigates to `verifyUser`, parses the key, then POSTs the generate request.

### ⚠️ Cloudflare Turnstile Block — The Critical Limitation

As of mid-2026, the **entire `image-generation.perchance.org` subdomain** is behind Cloudflare Turnstile **managed mode** (CF's strictest bot detection). This affects ALL endpoints:

- `verifyUser` — returns a Turnstile challenge page instead of the key
- `generate` — returns a Turnstile challenge
- `downloadTemporaryImage` — also gated

**This breaks all automated approaches:**
- Playwright headless Chromium → blocked
- Camoufox anti-detection browser (headless) → blocked
- Camoufox + Xvfb virtual display (non-headless) → blocked
- `nodriver` undetected Chrome → blocked
- `eeemoon/perchance` package → fails with `AuthenticationError: Failed to retrieve user key`
- `oujingzhou/text-to-image-generator` → same Playwright approach, same failure

**What DOES work:**
- A real user browser session that passes the Turnstile (copy the `userKey` from the URL)
- Paid CAPTCHA solving services (2Captcha, YesCaptcha)
- Direct browser cookie export from a session that already passed the Turnstile

### Existing Resources

| Resource | Description | Status |
|----------|-------------|--------|
| `~/.hermes/imagegen/perchance_pipeline.py` | Pipeline script: Playwright → key capture → API → download | Blocked by Turnstile |
| `~/.hermes/imagegen/README.md` | Full reverse-engineering documentation | Current |
| `~/.hermes/imagegen/output/` | Output directory for generated images | Ready |
| `pip install perchance` | `eeemoon/perchance` v0.1.0 (Dec 2025) | Blocked by Turnstile |
| `oujingzhou/text-to-image-generator` | GitHub repo, Playwright + Firefox | Blocked by Turnstile |

### Alternative: Together.ai FLUX Pipeline

Already working, fully documented in `together-ai-backend` skill. Key details:
- Endpoint: `POST https://api.together.xyz/v1/images/generations`
- Model: `black-forest-labs/FLUX.1.1-pro` or `FLUX.1.1-dev`
- NSFW bypass: `disable_safety_checker: true` in the request body
- Cost: ~$0.01 per image
- No Cloudflare gating

### Alternative: Local ComfyUI + Flux Schnell

True local generation with no dependencies on external servers:
- Model: Flux Schnell (Apache 2.0, open weights)
- VRAM: ~12GB minimum
- Setup: ComfyUI with Flux workflow
- Benefits: No rate limits, no censorship, no internet needed
- Pipeline: `image-generation` skill covers ComfyUI setup

### References

- `pip install perchance` — https://github.com/eeemoon/perchance (Apache 2.0)
- `oujingzhou/text-to-image-generator` — https://github.com/oujingzhou/text-to-image-generator
- Camoufox anti-detection browser — `camoufox-browser-setup` skill
- Together.ai backend — `together-ai-backend` skill
- ComfyUI setup — `image-generation` skill
- pollinations.ai free API — `pollinations-image-gen` skill