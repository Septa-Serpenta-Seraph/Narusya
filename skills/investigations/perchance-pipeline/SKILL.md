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
| `https://image-generation.perchance.org/api/generate` | Generate image (GET) |
| `https://image-generation.perchance.org/api/downloadTemporaryImage` | Download generated image by imageId |
| `https://image-generation.perchance.org/api/checkVerificationStatus` | Check if access key is still valid |

## Access Key Authentication

The API uses a 64-hex-char `userKey` param. The key is obtained by:
1. Open the generator page in a headless browser (Playwright)
2. Click "generate" button
3. Capture the `userKey` parameter from the resulting network request
4. Cache the key; re-fetch when it expires

## Python Client

Script lives at `~/.hermes/scripts/perchance_pipeline.py`.

Key generation parameters:
- `prompt`: URL-encoded prompt text
- `negativePrompt`: What to avoid
- `userKey`: 64-hex access key
- `seed`: -1 for random
- `resolution`: 512x768 (portrait), 768x512 (landscape), 768x768 (square)
- `guidanceScale`: 1-30 (default 7)
- `channel`: 'ai-text-to-image-generator' (the specific generator Adora uses)
- `subChannel`: 'public'

## Known Public Packages

- `pip install perchance` — async Python API (uses Playwright under hood, Chromium)
- `oujingzhou/text-to-image-generator` — CLI tool on GitHub (uses Playwright, Firefox)

## Limitations

- Access keys expire — must re-capture periodically
- Backend can change silently (author swaps models without notice)
- No character consistency between generations
- Resolution capped at ~1024 on a side
- No commercial license guarantee (Flux Schnell is Apache 2.0 though)