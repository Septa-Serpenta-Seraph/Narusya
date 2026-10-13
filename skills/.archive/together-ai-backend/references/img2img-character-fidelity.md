# img2img Character Fidelity — Reference-Image Recipe (verified 2026-08-12)

Problem: reproducing a SPECIFIC character's face (e.g. a githyanki that reads as
*gith*, not "lizard person") from a text prompt. Text-to-image models do not hold
fine canonical faces in their weights; describing features ("tiny flat nose, fin
ears, wide-set eyes") produces generic fantasy drift — five re-rolls all read as
lizard-person/vampire.

## The winning pattern: pixel reference, not word reference

1. **Find an official/reference portrait of the character** (wiki image pages are
   reliable — e.g. Baldur's Gate Wiki `File:Lae'zel_(BG3)_official_promo.png`).
   Extract the direct static URL from the file page's figure link
   (`https://static.wikia.nocookie.net/...`).
2. **Download + convert to PNG.** Wiki images are often WebP. `curl -sL -o ref.png
   "<url>"` then open with PIL (`Image.open` handles WebP) and re-save as PNG
   (`.convert('RGB').save(ref.png, 'PNG')`). Base64 the bytes.
3. **Call `black-forest-labs/FLUX.1-kontext-pro`** on
   `https://api.together.xyz/v1/images/generations` with browser UA + Origin +
   Referer headers (see SKILL.md Cloudflare note), body:
   ```python
   body = {
       "model": "black-forest-labs/FLUX.1-kontext-pro",
       "prompt": PROMPT,
       "image_url": f"data:image/png;base64,{img_b64}",
       "n": 1, "size": "1024x1024", "response_format": "b64_json",
   }
   ```
4. **Prompt shape that works:** start with "Transform this [character] into a
   [variant] named X." Then: "KEEP THE EXACT SAME FACE: same [bone structure,
   nose, ears, eyes, proportions] — do not change the facial anatomy at all."
   Then enumerate ONLY the changes: skin color, eye color, hair, armor, necklace.
   Same expression, same lighting quality. Do NOT describe the face in fresh words —
   the reference pixels carry it.
5. **Verify with vision_analyze** asking the discriminating question directly:
   "Does she look like a [canon race] or a [generic misread]?" (e.g. githyanki vs
   lizard person). Vision can confidently answer that binary even when it pattern-
   completes on subtle anatomy. Iterate only if the binary is wrong.

## Engine facts (verified 2026-08-12 on Together)
- `Qwen/Qwen-Image-2.0-Pro` → **rejects `image_url`** (HTTP 400 "Unsupported use
  of 'image_url' parameter"). Text-to-image only on this endpoint.
- `black-forest-labs/FLUX.1-kontext-pro` / `FLUX.1-kontext-max` → accept
  `image_url`. The edit/img2img workhorses.
- Output aspect follows the input reference, NOT square: 819×1117 input →
  880×1184 output. The "always 1024×1024" rule is text-to-image only.
- FAL proxy note: `image_generate`'s FAL edit route (fal-ai/flux-2/klein/9b/edit)
  may 409 on the Nous proxy even when `FAL_KEY` is set; Together kontext is the
  dependable path.
- Minor residual artifacts can appear at frame corners (generation noise); they
  don't affect the character read.

## When to use this vs. LoRA
- ONE-off character variant (recolor/re-outfit an existing design) → kontext-pro
  img2img. Fast, no training.
- SAME character across MANY images consistently → train a LoRA
  (see SKILL.md LoRA section). img2img anchors one shot; LoRA anchors a series.
