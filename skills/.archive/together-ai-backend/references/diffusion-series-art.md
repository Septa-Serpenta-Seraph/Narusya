# Diffusion Series Art — Consistent Deck/Card Workflow (learned 2026-08-07, Serpent's Tarot)

Producing a consistent set of images (tarot decks, card sets, character sheets, series
art) with text-to-image models. Verified against a 78-card tarot deck build using
FAL FLUX 2 Klein (`image_generate`), Together FLUX.2-dev, and Qwen-Image-2.0-Pro.

## The two recurring failure modes of diffusion text-to-image

1. **Garbled text.** Models try to render titles/labels and misspell them
   ("THE EMPRES", stray Roman numerals). FIX: ban text from the generator entirely —
   append `NO text, NO words, NO letters, NO numbers, NO title` to EVERY prompt — and
   overlay clean titles in post-processing (PIL/Pillow with a serif font). This is the
   professional approach anyway: text composited after generation is always legible.
   Note: even "NO text" doesn't stop some models (FLUX.2-dev still adds numerals);
   inspect every card and reject/regenerate the offenders.

2. **Impossible ("M.C. Escher") geometry.** Tight spirals/coils render with coils
   passing through each other — the model doesn't understand 3D depth of overlapping
   loops. FIX: never prompt a tight spiral. Use:
   - readable S-curves instead of spirals
   - an anchor object (moon, staff, pillar, throne) that establishes foreground/background
   - explicit depth language: "winds clearly in front of X, then behind Y"
   - simple compositions: one subject + one anchor. Complexity breeds artifacts.

## Bulbous tail / truncated-appendage pitfall

Tightly-tucked tail ends render as a bulbous blob or clipped stump. Always add:
`tail tapering to a fine elegant point, no truncation, no bulbous ends` — and for
creatures that might sprout extra anatomy: `one continuous snake body, NO wings, NO limbs`.

## Vision-model QA gap (CRITICAL)

The qwen3-vl vision model has strong completion bias: it will describe a bulbous tail
as "a rounded form nestled within the coil" and Escher geometry as "stylized but
coherent" — it pattern-completes instead of inspecting. It reliably catches
garbled text and says "yes/no" when directly asked, but it MISSES subtle anatomy
artifacts. The human eye is the final quality gate for series art. Use vision for:
- "Is there ANY text/letters/numbers anywhere?" (reliable)
- "Does the serpent have impossible geometry?" (unreliable — verify by eye)
And zoom-crop (PIL) + upscale the suspicious region before asking vision again.

## Version management (naming discipline)

When iterating a card, KEEP every version under a distinct filename
(card02_v1_bulbous.png, card02_v2_escher.png, card02_highpriestess.png) and move
rejects into a `cards/_rejects/` subdir. Do NOT `mv` over the previous version
before confirming the new one is accepted — the keeper can get lost in a shuffle
(this happened 2026-08-07: a `mv` chain mislabeled the accepted V3 as a reject).
After any batch of moves, `ls -la` both dirs to confirm what actually landed.

## Engine selection for series art (2026-08-07 A/B on same 4 prompts)

| Engine | Text | Anatomy | Style | Verdict |
|---|---|---|---|---|
| FAL FLUX 2 Klein (`image_generate`) | garbles | Escher spirals | lush Mucha art nouveau | needs text-banned + simple poses |
| Together FLUX.2-dev | adds numerals anyway | better but can add wings/limbs | Celtic-knot drift | usable w/ strict prompts |
| **Qwen-Image-2.0-Pro** | none | coherent, obeys "one continuous snake" | art nouveau, full-frame | **best for this class** |

The general lesson: when a model repeatedly fails a compositional requirement, do a
quick same-prompt A/B across 2-3 engines (they're all cheap/free here) and pick the
one that follows instructions, not the prettiest one. Lock the winner's prompt
template into the project README with the failure-mode rules so all remaining
generations inherit the fixes.

## Post-processing recipe (titles + print PDF)

- **Together image endpoint is SQUARE-ONLY (verified 2026-08-08):** ALL models
  (Qwen-Image-2.0-Pro, FLUX.2-dev, etc.) return 1024×1024 regardless of
  `size`/`aspect_ratio` — `768x1344`, `832x1248`, `2:3` are silently ignored.
  Do NOT re-test size params; it's a platform constraint, not a model quirk.
  Pipeline: generate square → extend to portrait (1024×1756 ≈ 70×120mm) in post
  with PIL title bands (obsidian + gold lines + serif text), paste art centered.
  Uniform bands make the deck look MORE professionally unified, not less.
- Composite title text with PIL: `ImageDraw.text` + a serif TTF, white/gold on a
  banner, bottom of card. Then place cards on an A4/letter sheet for a printable PDF
  (PIL can save multipage PDF directly).
- 300 DPI target for print (1024px art prints ~3.4" at 300 DPI — acceptable for
  digital-first Etsy product; upsample with LANCZOS if needed).

## PIL overlay for layout conventions the generator can't do (verified 2026-08-12)

Some layout conventions are beyond text-to-image: the comic "off-screen speaker"
bubble (white bubble whose TAIL POINTS DOWN toward the panel edge, implying an
unseen speaker below the frame). Re-rolled 5× with escalating tail-direction
language ("tail points STRAIGHT DOWNWARD to the bottom border, do NOT point at the
character") — every attempt rendered the tail pointing at the character's mouth.
FIX: stop fighting the model; **generate the panel WITHOUT the offending element,
then draw it yourself with PIL.** This is the same principle as text-banning —
composite in post for full control.

PIL bubble recipe (DejaVuSans-Bold TTF; see `image_gen_and_vision_recipes.md` for
the rest of the toolchain):
- `draw.rounded_rectangle([x0,y0,x1,y1], radius=20, fill='white', outline='black', width=4)`
  for the bubble body.
- Tail as a filled triangle `draw.polygon([...], fill='white', outline='black')`,
  then re-draw the two tail edges with `draw.line(..., width=4)` so the outline
  reads correctly where it meets the bubble.
- **Wrap text to the panel width BEFORE drawing** — a single-line label wider than
  the panel gets silently clipped (654px text in a 512px panel → cut off at the
  edge; user caught it). Measure `draw.textbbox((0,0), line, font=font)`, split on
  words so each line ≤ panel_width − margin, then center each line with
  `draw.text((cx - lw//2, ty), ...)`.
- After compositing, run vision with "is the bubble fully visible / not cut off?"
  — that check IS reliable even when anatomy checks aren't.
