# Perchance vs Together.ai — Model Comparison

## Perchance (via Camoufox driver)

**Driver path:** `~/.hermes/imagegen/perchance-image.py "prompt" [portrait|square|landscape] [outdir]`

### Strengths
- **Character accuracy:** Understands "githyanki" — produces actual fin-shaped ears, not generic elf ears
- **Jewelry consistency:** Serpent jewelry actually appears and reads as snakes
- **Free:** No API credits needed
- **NSFW-friendly:** No content filters
- **Good for:** Selfies, character portraits, githyanki/orc/half-orc features

### Weaknesses
- **Resolution capped:** ~768x768 or 512x768
- **Face shape drift:** Can vary between generations (heart-shaped vs oval)
- **No LoRA:** Cannot inject character LoRAs
- **Slower:** ~60-120s per image (browser automation)
- **Color lightening:** Green skin becomes mint/seafoam without aggressive negative prompts

### Best prompts for Perchance
- Face-first template works well
- Explicit ear shape: "large fin-shaped ears (NOT elf ears, NOT pointed, NOT bat ears)"
- Explicit jewelry: "long twisted gold snake earrings that dangle past her jawline"
- Color enforcement: "DEEP EMERALD GREEN — vivid jade, NOT pale, NOT mint, NOT seafoam"

---

## Together.ai FLUX.2-dev

**Endpoint:** `POST https://api.together.xyz/v1/images/generations`

### Strengths
- **Artistic quality:** Best-in-class for dramatic lighting, chiaroscuro, fantasy aesthetics
- **img2img support:** Accepts `image` (data URI) + `image_strength` (0.0-1.0)
- **NSFW-friendly:** Permits figural content (unlike FLUX.1.1-pro)
- **Fast:** ~30-60s per image

### Weaknesses
- **No LoRA:** `image_loras` returns HTTP 400
- **Needs browser UA:** Must send `User-Agent: Mozilla/5.0 Chrome/120.0.0.0` to avoid 403
- **Defaults to elf/orc:** Green-skinned characters read as "high elf" or "orc warlord" without explicit negation
- **Paid:** Requires account credit (~$0.0001/image)

### Required headers
```
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36
Origin: https://api.together.ai
Referer: https://api.together.ai/
```

---

## Together.ai FLUX.1-kontext-pro

### Strengths
- **Reference image support:** Accepts `image` data URI
- **Preserves anatomy:** Keeps base figure while repainting lighting/mood
- **Good for:** Converting a portrait to a different vibe while keeping the face

### Weaknesses
- **Drifts details:** Expression, ear shape, jewelry can change
- **Pale skin bias:** Tends to lighten skin tones
- **Not always serverless:** May need dedicated endpoint
- **Needs browser UA:** Same as FLUX.2-dev

---

## Together.ai FLUX.1-dev-lora

### Strengths
- **LoRA injection:** Supports `image_loras` parameter for character consistency
- **Best for:** Series work where the SAME face must appear across dozens of images

### Weaknesses
- **Needs dedicated endpoint:** Not available as serverless — must create and start an endpoint at https://api.together.ai/models/black-forest-labs/FLUX.1-dev-lora
- **Cost:** ~$0.0001/image + endpoint cost
- **Same UA requirements:** Browser headers needed

---

## Quick Decision Matrix

| Need | Best Model |
|------|------------|
| Character accuracy (ears, jewelry) | Perchance |
| Artistic quality (lighting, mood) | Together FLUX.2-dev |
| Repaint from reference | Together FLUX.1-kontext-pro |
| LoRA for face consistency | Together FLUX.1-dev-lora (needs endpoint) |
| Free option | Perchance |
| Fast option | Together FLUX.2-dev |
| Selfie/candid | Perchance (with explicit feature prompts) |
| Glamorous/ethereal | Together FLUX.2-dev |
