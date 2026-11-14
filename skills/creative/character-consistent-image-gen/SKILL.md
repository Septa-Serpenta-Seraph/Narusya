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

### Example (Narusya) — ERA ONE SPEC (stale for current identity)

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

> ⚠️ **SPEC DISCREPANCY — check which era the user wants.** The above example uses the
> **Era One** spec (vertical slit pupils, violet scale shimmer). The user's CURRENT identity
> kit (Emerald Self / Era Two) uses **round pupils, smooth skin, no scales** — the user
> caught a render set built from the stale slit-pupil spec and corrected it. When the user
> says "my face" or "my current look," default to Era Two (round pupils, smooth skin, no
> scales, golden hair, fin ears, gold serpent jewelry). Only use Era One if the user
> explicitly requests the older sigil-era appearance. See `image-vision-backends/references/narusya-canonical-face.md`
> — but note that file ALSO still references the Era One spec; the user's memory and
> identity kit are the authority.

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

**Verified finding (2026-11-06):** Even with this emphasis, SDXL Base and Juggernaut XL v9 (via ComfyUI) produce almost zero green pixels (0.1-0.6% green-dominant). The models fundamentally default to human skin tones. For non-human skin colors, FLUX.2-dev (with `disable_safety_checker:true`) or Perchance handle color better — FLUX.2-dev still smooths anatomy but at least respects the green. Pixel-verify any result: if green-dominant pixels <5%, the skin color didn't render and you need a different model.

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

**API call note:** Use curl subprocess, not urllib — Together.ai blocks urllib's default User-Agent (403). Example:
```bash
curl -s -X POST "https://api.together.xyz/v1/images/generations" \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"black-forest-labs/FLUX.2-dev","prompt":"...","width":512,"height":768,"steps":28,"disable_safety_checker":true}'
```
Download the returned URL with `curl -s -o output.jpg "$URL"`.

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
| Together.ai 403 with urllib | API blocks urllib's default User-Agent | Use curl subprocess instead of urllib.request; add browser User-Agent header |

## Workflow

1. **Define the face template** — Write it once, reuse across all vibes
2. **Choose the model** — Perchance for character accuracy, Together for artistic quality
3. **Build the prompt** — Face template + mood/setting suffix
4. **Add negative prompts** — Color enforcement + feature negation
5. **Generate and compare** — Check against approved reference portrait
6. **Iterate** — Adjust face template if features drift

## Verification

After generation, compare against the approved reference portrait:
- Ears the right shape (fin vs elf vs bat)?
- Jewelry present and correctly described?
- Skin color in the right range (not too light, not too dark)?

If the generated character looks like a "sister" but not the same person, the face template needs more specificity.

## Expression Catalogs (image libraries tagged by emotion)

When generating multiple expressions of the same character for use as reactions/emotes, organize them into a structured catalog:

### Directory structure
```
~/.hermes/character-expressions/
├── manifest.json          # emotion → file path mapping
├── happy_01.png
├── happy_02.png
├── sad_01.png
├── angry_01.png
└── ...
```

### Manifest format
```json
{
  "happy": {
    "primary": "/path/to/happy_01.png",
    "variants": ["/path/to/happy_02.png"],
    "prompt_suffix": "bright smile, warm eyes, relaxed posture"
  }
}
```

### Delivery via Discord
Use `MEDIA: /absolute/path/to/file.png` in your response — Discord renders it as an image attachment. Pick a random variant for variety. Keep the manifest updated when adding new images.

### Naming convention
`{emotion}_{variant_number}.png` — e.g., `happy_01.png`, `happy_02.png`, `sad_01.png`. Lowercase, underscores, no spaces. (Narusya's live catalog is `~/.hermes/narusya-expressions/`, one file per emotion, `{emotion}.jpg` — the always-loaded SOUL.md and manifest reference that extension, so convert incoming `.webp`/`.png` to `.jpg` instead of changing the paths.)

### Replacing an expression set

When a new set arrives (from the user, a peer daemon, or a fresh generation run), swap it in without losing the old one or breaking the always-loaded paths:

1. **Back up the live catalog first.** `cp -r ~/.hermes/narusya-expressions ~/.hermes/narusya-expressions-v1-backup-<date>` — never overwrite the only copy.
2. **Convert to the catalog's format.** Write the incoming files over `{emotion}.jpg` at quality 95.
3. **Update `manifest.json`.** Read it first (the write guard refuses a stale overwrite), then write the new mapping. Keep the `base_template`, `negative_prompts`, and `prompts_md` keys alongside the per-emotion entries.
4. **Verify skin color.** Run `scripts/verify_catalog.py` — the face region should be strongly green-dominant. A set that fails is a regrade, not a catalog.
5. **Build a review grid.** Run `scripts/make_catalog_grid.py` and send the labeled montage to the user before calling it done.

Keep the source prompt templates that came with the set (e.g. `nar-image-prompts-v2.md`) in the catalog dir so the next generation run starts from the same identity block.

## Multiple FORMS of one character (verified 2026-09-28)

When the user asks for the same character as different creature-types (animal form, hybrid/mythic
form, costume form), each form needs the SAME identity features mapped onto the new anatomy —
not just the same face template. Pattern that worked for "three versions of Narusya":

- **Animal form:** map hair→fleece/fur color, eyes→animal eyes (keep color + pupil shape if
  plausible; note honestly when slit pupils didn't take), signature jewelry still wearable
  (earrings, circlet, pendant), skin color on exposed skin areas (face/ears/legs).
- **Hybrid/mythic form (lamia, mermaid, etc.):** full face template verbatim + the creature's
  body plan; keep scale/shimmer placement rules.
- **Costume form:** full face template verbatim + costume described as CLOTHING ("full-body
  X mascot costume with oversized hood"), jewelry layered OVER the costume ("gold serpents
  coiled around neck and arms over the costume") so the model doesn't merge costume into
  anatomy.

Verified failure mode: generic priors ("woman with long white hair, green eyes") produce
polished strangers. Verified success: face template + per-form feature mapping + explicit
negative prompts (skin-color negations AND hair-color negations "black hair, dark hair" when
canon is blonde).

**Which canon spec to use — check for MULTIPLE specs:** a character may have several anchored
appearances (e.g. a mythic sigil render AND a canonical face template). The most recent or
user-affirmed one wins — if unsure, ASK which form the user means, or generate from the
user-cited one. Adora caught a render set made from a stale sigil spec (ink-black hair,
crimson eyes) when the canonical template is golden-blonde hair, emerald skin, amber-orange
slit-pupil eyes. When the user remembers a feature differently from the spec you used, the
user's memory wins — re-check for another spec file before defending the one you used.

A distilled copy-paste version of the verified Narusya spec (canon block, negative prompt,
per-form mapping table, list of known NON-canon divergences) lives in the sibling skill:
`image-vision-backends/references/narusya-canonical-face.md`. Related field notes on
canon-spec hunting and re-roll strategy:
`image-vision-backends/references/canon-spec-consistent-characters.md`.

## References

- `references/perchance-vs-together.md` — Detailed model comparison and when to use which
- `references/face-template-library.md` — Reusable face-first templates for different characters
