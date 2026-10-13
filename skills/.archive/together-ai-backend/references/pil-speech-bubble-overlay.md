# PIL Speech-Bubble / Text Overlay for Panels (verified 2026-08-12)

When a comic/meme panel needs speech bubbles, **generate the art WITHOUT the bubble** and draw it
in post with PIL. Image models render bubble *text* fine (Qwen-Image-2.0-Pro is text-capable;
FLUX garbles text) but cannot control *tail direction / attribution* — an off-screen speaker below
the panel needs the tail pointing DOWN at the panel edge, and models keep pointing the tail at the
character's mouth (reads as the character speaking). Verified on the Narusya/Miku meme: five
prompt re-rolls failed; one PIL overlay fixed it.

## Recipe
1. Generate panel art with Qwen-Image-2.0-Pro, leaving clean space where the bubble will go.
2. Draw the bubble with PIL: rounded rectangle + polygon tail pointing at the **speaker**
   (down toward the panel edge for off-screen speakers), white fill, thin black outline.
3. **Measure text before drawing** — `draw.textlength(text, font=font)`. If wider than the panel,
   wrap to multiple lines. Classic bug: text wider than the panel gets centered and cut off at
   the left edge (Narusya's "NARUSYA, DO YOU KNOW HOW TO READ?" overflowed the 512px panel at
   font size 28). Compute the box from wrapped lines, then center it.
4. Font: use a full-glyph font — DejaVu Sans at
   `/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf` (NOT DejaVuSansMono — missing glyphs).
5. Verify with vision: tail points the right way, nothing overflows, text spelled correctly.
   User's eye is the final quality gate — vision has completion bias and green-lights subtly
   broken text/layout; do not trust it alone.

## Model note
For text-bearing panels prefer Qwen-Image-2.0-Pro (accurate bubble text). FLUX.2-dev adds
numerals/garbles text; FLUX 2 Klein garbles badly. See `together-ai-backend` for the full
engine A/B table.
