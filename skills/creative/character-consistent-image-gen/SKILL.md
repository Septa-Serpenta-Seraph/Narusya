---
name: character-consistent-image-gen
title: Character-Consistent AI Image Generation
description: Generate same-character images across moods and settings.
author: Narusya
license: MIT
tags:
  - image-generation
  - character-consistency
  - face-first-prompting
  - perchance
  - together-ai
  - flux
  - selfie
  - githyanki
related_skills:
  - image-generation
  - together-ai-backend
  - perchance-pipeline
  - creative-video
---

# Character-Consistent AI Image Generation

Generate images that preserve a specific character's identity across different vibes, settings, and styles. The core challenge: text-to-image models don't hold a face unless you force them to.

## When to use

- User wants multiple images of the SAME character (different moods, outfits, settings)
- User wants a "glamor shot" series or "selfie" series
- User complains that generated images "don't look like me/them"
- User wants to preserve specific features (ear shape, jewelry, skin color) across generations

## Core Technique: Face-First Prompting

The single most important technique. Describe the FACE first, before mood, lighting, or setting. The model weights early prompt tokens more heavily.

### Template

```
A close-up portrait of [character]. Their face is the most important part, describe it first:
[face shape], [eye color + pupil shape], [nose shape], [lip shape + expression].
[ear shape + specificity]. [skin color + texture + shimmer if any].
[hair color + style]. [signature jewelry — be explicit about shape, position, attachment].
[THEN: mood, lighting, setting, style]
```

### Example (Narusya)

```
A close-up portrait of a githyanki woman. Her face is the most important part:
heart-shaped face with high cheekbones, bright amber-orange eyes with vertical slit pupils,
small delicate upturned nose, full lips curved in a subtle knowing smile.
Long elegant pointed ears, slightly finned at the edges.
Smooth vivid emerald green skin with subtle iridescent violet scale shimmer on temples, cheekbones, and sides of neck.
Golden-blonde center-parted hair falling past her shoulders in soft waves.
Long twisted gold snake earrings dangling past her jawline.
Gold serpents coiled around neck and arms, detailed with scales.
[THEN: mood/setting]
```

## Color Enforcement

Models LIGHTEN non-human skin colors. Green becomes mint/seafoam. Always use explicit negative prompts.

### Skin color negative prompts

```
pale skin, white skin, light skin, alabaster, porcelain, mint green, olive green, teal skin, pale green
```

### For deep emerald green specifically

```
CRITICAL: her skin is DEEP EMERALD GREEN — vivid jade, NOT pale, NOT mint, NOT seafoam, NOT olive, NOT teal, NOT pastel, NOT light. Think dark rich green like an emerald gemstone.
```

## Model Selection

### Perchance (via Camoufox driver)

**Best for:** Character accuracy, fin ears, serpent jewelry, githyanki/orc features, NSFW, free
**Driver:** `~/.hermes/imagegen/perchance-image.py "prompt" [portrait|square|landscape] [outdir]`
**Pros:** Understands "githyanki" better, produces actual fin ears, consistent serpent jewelry
**Cons:** Lower resolution, can drift on face shape, no LoRA support

### Together.ai FLUX.2-dev

**Best for:** Artistic quality, dramatic lighting, img2img, NSFW
**Pros:** Best artistic quality, permits NSFW, supports img2img with `image` + `image_strength`
**Cons:** No LoRA support (400 error), defaults to "elf" or "orc" for green-skinned characters, needs browser UA headers to avoid 403

### Together.ai FLUX.1-kontext-pro

**Best for:** Repainting a reference image while preserving anatomy
**Pros:** Accepts `image` reference, preserves base figure
**Cons:** Drifts expression and details, pale skin bias, needs dedicated endpoint for some models

### Key Together model facts

- `FLUX.2-dev` — best artistic, permits NSFW, NO LoRA (400), needs browser UA
- `FLUX.1-dev-lora` — supports LoRA but needs dedicated endpoint (not serverless)
- `FLUX.1-kontext-pro` — accepts reference image, good for repaint
- `FLUX.1.1-pro` — strictest NSFW pre-screen (422s on figural)
- `Qwen/Qwen-Image-2.0-Pro` — best instruction following, text-to-image ONLY (rejects image_url)

## Selfie / Accidental Photography Prompts

Selfies need EXTRA specificity about features, or the model defaults to human/elf.

### Key elements to include

- **Ears:** "large fin-shaped ears (NOT elf ears, NOT pointed, NOT bat ears — flat wide fins extending from the sides of her head)"
- **Jewelry:** "long twisted gold snake earrings that dangle past her jawline"
- **Expression:** specific — "sticking her tongue out, making a goofy/dazed expression" or "surprised/caught-off-guard expression"
- **Setting context:** "bedroom background with white pillows" or "gas station at night with fluorescent lights"
- **Photo quality:** "low quality phone photo, candid, unposed"

### Example selfie prompts

**Bed selfie:**
```
An accidental selfie of a githyanki woman lying in bed, holding her phone above her face,
flash going off, she has emerald skin and gold hair in a messy bun, surprised expression,
warm bedroom lighting, cozy sheets, candid, unposed, low quality phone photo.
She has large fin-shaped ears (NOT elf ears). She wears long twisted gold snake earrings.
```

**Gas station selfie:**
```
A selfie of a githyanki woman at a gas station, night, fluorescent lights,
she has emerald skin and gold hair, tired expression, holding a slushie,
leaning against a pump, candid, low quality phone photo.
She has large fin-shaped ears (NOT elf ears). She wears long twisted gold snake earrings.
```

## Common Pitfalls & Fixes

| Problem | Cause | Fix |
|---------|-------|-----|
| Skin turns mint/pale | Model lightens green | Explicit negative prompts + "DEEP EMERALD" emphasis |
| Ears vanish or become elf | Model defaults to human/elf for selfies | Explicit "fin-shaped ears (NOT elf ears)" every time |
| Face shape drifts | No face shape specified | Add "heart-shaped face with high cheekbones" or "oval face" |
| Jewelry missing | Buried in prompt | Describe jewelry immediately after face, before mood |
| Expression wrong | No expression specified | Add "subtle knowing smile" or "playful smirk" |
| Whitewashed colors | Model bias toward light skin | Multiple negative color terms + "vivid" emphasis |
| Kontext drifts details | Reference not strong enough | Lower image_strength (0.3-0.35), but drift is still likely |
| FLUX.2-dev 400 on LoRA | Model doesn't support LoRA | Use FLUX.1-dev-lora (needs endpoint) or no LoRA |
| Vision model 451 | Content policy block | Try different model or describe without preview |

## Workflow

1. **Define the face template** — Write it once, reuse across all vibes
2. **Choose the model** — Perchance for character accuracy, Together for artistic quality
3. **Build the prompt** — Face template + mood/setting suffix
4. **Add negative prompts** — Color enforcement + feature negation
5. **Generate and compare** — Check against approved reference portrait
6. **Iterate** — Adjust face template if features drift

## Verification

After generation, compare against the approved reference portrait:
- Face shape consistent?
- Eye color and pupil shape correct?
- Nose and lip shape match?
- Ears the right shape (fin vs elf vs bat)?
- Jewelry present and correctly described?
- Skin color in the right range (not too light, not too dark)?

If the generated character looks like a "sister" but not the same person, the face template needs more specificity.

## References

- `references/perchance-vs-together.md` — Detailed model comparison and when to use which
- `references/face-template-library.md` — Reusable face-first templates for different characters
