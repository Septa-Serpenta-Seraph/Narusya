# Pollinations.ai — Keyless Image Generation (incl. NSFW)

When the `image_generate` tool is disabled or `FAL_KEY`/`OPENAI_API_KEY` are blank,
**pollinations.ai** gives free, keyless, no-signup text-to-image via a direct URL.
Confirmed working on this host (2026-07-09) for both SFW art and NSFW.

## Basic (SFW) call
```bash
PROMPT="a majestic floating sky castle of pale stone and glowing crystal spires at golden hour dusk"
ENC=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$PROMPT")
URL="https://image.pollinations.ai/prompt/${ENC}?width=1024&height=576&nologo=true&model=flux"
curl -sL --max-time 150 -o out.png "$URL"
```
- Returns raw JPEG/PNG bytes. Verify: `file out.png` → expect "JPEG image data" / "PNG image data",
  NOT a small error JSON or block page.
- `model=flux` is sharper than the default renderer. `nologo=true` strips the watermark.
- Free endpoint can be slow (10–60s); use `--max-time 150`.

## NSFW
Append `&safe=false` to the query string. Confirmed: explicit prompts render (not blocked) with this flag.
```bash
URL="https://image.pollinations.ai/prompt/${ENC}?width=768&height=1024&nologo=true&model=flux&safe=false"
```
Consent + whitelist still governed by BYPASS.md and the parent nsfw-creative-work skill.
Only adult, consensual, non-minor content.

## Quality caveats (honest)
- Free `flux` on pollinations is weak on anatomy (hands, limbs, precise stylized output).
  Expect imperfections; offer to re-roll or upgrade.
- For high-fidelity unfiltered output, an owned `FAL_KEY` → FLUX/dev is dramatically better.
- If the response is a small JSON error instead of an image, the model/param was rejected —
  try `model=flux` or drop unsupported params.

## Re-roll
Change the prompt slightly or append `&seed=<n>` to vary output deterministically.

## Perchance relationship
perchance.org's "ai text to image generator" routes to this same pollinations backend.
Driving pollinations directly via curl avoids the iframe the browser snapshot can't pierce.
