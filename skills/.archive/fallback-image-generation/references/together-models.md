# Together.ai image models — condensed behavior notes (verified 2026-07-26)

All tested on a single project-scoped key with $5 credit, via direct REST `/v1/images/generations`.
UA/Origin/Referer headers REQUIRED or Cloudflare returns 403 / error 1010.

## NSFW / figural behavior (MODEL-SPECIFIC, not account-wide)
- `black-forest-labs/FLUX.1.1-pro` — 422 "image may contain NSFW content" even on a generic marble-nude
  prompt. Avoid for figural/NSFW.
- `black-forest-labs/FLUX.2-dev` — permits figural + NSFW; best artistic quality (~9/10). DEFAULT for art.
- `RunDiffusion/Juggernaut-Lightning-Flux` — permits, but stricter screen (422'd a coiled-lamia prompt
  that FLUX.2-dev accepted). Inconsistent.
- `stabilityai/stable-diffusion-xl-base-1.0` — permits, weaker art (7/10, abstract/vague).
- `black-forest-labs/FLUX.1-schnell` — permits, decent (8/10) but less detailed.

## Text inference
- `meta-llama/Llama-3.3-70B-Instruct-Turbo` — works with UA headers (non-censored text fallback for
  hy3/Tencent). 403 without UA.

## Endpoint quirks
- `/v1/models` works WITHOUT UA (unprotected metadata) — do not use it as a liveness test for inference.
- 422 body shape: `{"error":{"message":"image may contain NSFW content","type":"invalid_request_error"}}`.
- `safety_checker` param ("none"/"minimal") does NOT bypass the 422 pre-screen — the screen is on the
  prompt, not the output model. Switch models instead.

## Image aspect
- FLUX.2-dev handled 768x1024 (portrait) and 1024x768 (landscape) fine. 512 is lower quality but faster.
