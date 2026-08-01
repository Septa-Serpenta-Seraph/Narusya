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
| **Perchance API** | Free (ad-funded) | None (NSFW allowed) | Medium (full Chromium works) | Playwright + full Chromium binary | Free, consistent gen |
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

### Working Approach — Playwright with Full Chromium Binary

The `image-generation.perchance.org` subdomain is behind Cloudflare Turnstile **managed mode**. However, Playwright's **full Chromium browser** (NOT the headless shell) passes the Turnstile.

**Key insight:** Playwright installs two Chromium binaries:
- `chromium_headless_shell-*/` — blocked by Turnstile
- `chromium-*/chrome-linux64/chrome` — full "Chrome for Testing", **passes** ✓

**Confirmed path:** `~/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome`

**Pipeline:**
1. Launch Playwright with `executable_path=full_chromium`, `args=["--no-sandbox"]`
2. Navigate to `perchance.org/ai-text-to-image-generator`
3. Click the generate button → capture `userKey` from network traffic URL
4. Navigate to `verifyUser` endpoint to set Turnstile cookies
5. Make API call via `page.evaluate()` (within browser context = cookies pass Turnstile)
6. Download image via proxy download URL

**Script:** `~/.hermes/imagegen/perchance_gen.py`
```bash
python3 ~/.hermes/imagegen/perchance_gen.py "your prompt" [shape]
```
- Shapes: `portrait` (512x768), `square` (768x768), `landscape` (768x512)
- Key cached at `~/.cache/perchance_access_key.txt` (auto-refreshes)
- Output: `~/.hermes/imagegen/output/`

**Pitfalls:**
- Use `new_context()`, NOT `launch_persistent_context()` — persistent profiles trigger Turnstile
- API calls must come from within the browser's JS context (`page.evaluate`) — direct curl fails
- Navigate to `verifyUser` first to set Turnstile cookies before API calls
- Use the `imageDownloadUrl` (proxy) endpoint for downloads, not the direct `/downloadTemporaryImage`

### Existing Resources

| Resource | Description | Status |
|----------|-------------|--------|
| `~/.hermes/imagegen/perchance_gen.py` | Working pipeline: Playwright full Chromium → key capture → API → download | **Working** |
| `~/.hermes/imagegen/README.md` | Full reverse-engineering documentation | Current |
| `~/.hermes/imagegen/output/` | Output directory for generated images | Ready |
| `pip install perchance` | `eeemoon/perchance` v0.1.0 (Dec 2025) | Blocked by Turnstile (no full Chromium path) |
| `oujingzhou/text-to-image-generator` | GitHub repo, Playwright + Firefox | Blocked by Turnstile |

### Alternative: Together.ai FLUX + LoRA (Consistent Character Pipeline)

For generating consistent characters across images (e.g. a "Narusya" humanoid form), Together.ai supports **Flux LoRA injection** via their API:

**Key details:**
- Model: `black-forest-labs/FLUX.1-dev-lora` (or `FLUX.2-dev` with `image_loras` param)
- LoRA format: URL to a `.safetensors` file (host on HuggingFace)
- LoRA parameter: `image_loras: [{"path": "<url>", "scale": 1.0}]`
- Trigger word: included in the prompt (varies per LoRA)
- API: `POST https://api.together.xyz/v1/images/generations`
- NSFW bypass: `disable_safety_checker: true`

**Python example:**
```python
from together import Together
client = Together(api_key=api_key)
image = client.images.generate(
    prompt="narusya style, a portrait in the rain",
    model="black-forest-labs/FLUX.1-dev-lora",
    image_loras=[{
        "path": "https://huggingface.co/your-org/narusya-lora",
        "scale": 1,
    }],
)
```

**Training a LoRA (for consistent character):**
1. Generate 10-20 reference images of the character using the Perchance pipeline
2. Train via Replicate's `ostris/flux-dev-lora-trainer` (~$1-2) or CivitAI's trainer
3. Upload trained LoRA to HuggingFace
4. Use via Together.ai API with the `image_loras` parameter

No local GPU needed — training and inference both run on cloud APIs.

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