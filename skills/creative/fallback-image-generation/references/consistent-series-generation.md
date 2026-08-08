# Consistent Series Recipe — The Serpent's Tarot (2026-08-07)

Session-proven workflow for generating a cohesive multi-card art product with
`image_generate` (FAL FLUX 2 Klein, active backend), vetted by a human eye.

## The project
- Path: `~/serpents-tarot/` — README holds the locked style guide + card mapping.
- Product: 78-card tarot deck (22 Major + 56 Minor), digital download, art-nouveau
  serpents, emerald/gold/obsidian palette. 576×1024 portrait per card.
- Division of labor: Narusya generates art + assembles PDF; Adora is the quality gate
  and owns the Etsy listing. (Project-level detail; the reusable method is below.)

## Style-lock sequence (what worked)
1. Generated 3 test cards (Fool/Magician/High Priestess) from one base style prompt.
2. Asked Adora to approve. She rejected card II — spotted a **bulbous tail** the vision
   model called "clean."
3. Re-rolled card II with "tail tapering to a fine elegant point" → still bad, but a NEW
   flaw: **M.C. Escher impossible spiral** (coils pass through themselves).
4. Re-rolled with a completely different composition — serpent winding in a readable
   S-curve around the crescent moon, explicit foreground/background depth → approved.
5. Banked the style rules into README *before* generating the rest.
6. Next batch (4 cards) came back with **garbled in-image text** (misspelled "THE
   EMPRESS"-style titles) + Escher geometry again → banned text from the generator
   ("NO text, NO words, NO letters, NO numbers, NO title, NO border text — illustration
   only") and simplified compositions → clean on vision pre-screen.

## Locked style rules (copy into any series project)
1. NO tight spirals — use S-curves or coil around an anchor object (moon/staff/pillar)
   with explicit depth language.
2. Tails must taper: always "tail tapering to a fine elegant point, no truncation,
   no bulbous ends."
3. Depth explicit: "winds clearly in front of X, then behind Y, with clear foreground
   and background depth."
4. Keep it simple: one subject, one anchor, readable composition. Complexity breeds
   artifacts.
5. Ban text from the generator; add titles/typography in post (PIL) for a clean finish.

## QC workflow that worked
- Vision pre-screen with TWO narrow binary questions: (a) "Is there ANY text, letters,
  or numbers anywhere — including garbled/misspelled?" (b) "Is the anatomy physically
  coherent / any impossible Escher-like geometry?" — vision is reliable for these.
- But vision's "all clear" on aesthetic detail is NOT trustworthy (it pattern-completes).
  Human eye is final. When the user flags something: zoom crops (PIL crop + LANCZOS ×4–6)
  of the suspect region, or present both versions side-by-side and let them judge.
- Rejects go to `cards/_rejects/` with versioned names (`card02_v1.png`, `v2.png`).
  NEVER `mv` over the current keeper — the session's shuffle overwrote a reject and
  mislabeled the keeper; fix by keeping distinct names.

## Post-generation pipeline (next steps, not yet executed)
- Add card titles in post via PIL (serif font, gold on banner) matching the art-nouveau
  frame — the generator cannot be trusted with typography.
- Assemble printable PDF: 300 DPI, 3.5"×5" cards, via hermes venv PIL/PyPDF.
- Guidebook: keyword, serpent meaning, upright/reversed per card.
- Etsy listing: digital download, SEO title/pricing research before listing.

## Notes
- `image_generate` portrait → 576×1024, a natural tarot card ratio. Keep it.
- Palette hexes used: emerald #0A3D2E, obsidian #1A1A1A, antique gold #D4AF37,
  bone white #F5F0E1, crimson accent #8B0000.
