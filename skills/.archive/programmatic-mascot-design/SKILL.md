---
name: programmatic-mascot-design
description: Code-drawn mascots; use when hand-coded art looks broken.
---

# Programmatic Mascot & Icon Design

Drawing a clean mascot, character silhouette, or icon in code (no image-gen model / no design tool). Applies to HUD/terminal mascots, vault-boy-style figures, app icon avatars, etc. Learned/validated building PIPNARU's "pipgirl" (several failed SVG passes → working PNG).

## Core rule: PNG via PIL beats hand-tuned SVG at small sizes

- **Hand-stitched SVG bezier `path` shapes anti-alias into a hollow wireframe look at small display sizes (~170–200px).** The vision/human eye reads thin outlines, not the fill — four cognitive passes kept describing the figure as "broken/stick/wireframe."
- **A pixel-exact PNG drawn with `PIL.ImageDraw` renders solid and clean.** You control every pixel; no hinting/anti-alias ambiguity. `pillow` is usually available (`python3 -c "import PIL"`).
- So: for a *small* icon/mascot, build it with `ImageDraw` primitives (`ellipse`, `polygon`, `rectangle`, `line`) and reference it as `<img src="...png">`.

## The mascot-design rubric (from how Bethesda built Vault Boy)

Vault Boy wasn't one artist's stroke — it was a **hand-off pipeline** (Leonard Boyarsky concept → George Almond cards → Tramell Isaac finalized → Natalia Smirnova redrew F3/4/76). The durable rules that make a mascot *read* at size:

1. **Simple, recognizable shapes** — oval head, dot eyes, a smile. Let the brain fill in detail. Don't sculpt anatomy with complex curves.
2. **Inset contrasting features** — the face and hair are **darker/paler shapes set INTO a lighter base head**, not one flat silhouette. This contrast is what makes it read at distance/small size. A single flat blob reads as nothing.
3. **One signature pose** that carries meaning. (Vault Boy: the sardonic thumbs-up "everything's fine when it isn't.") Pick a pose that's honest to the subject.
4. **Base it on a recognizable archetype** (Vault Boy ≈ Monopoly's Rich Uncle Pennybags / 50s ad-man) rather than an invented blob.

## Workflow (do this order, not guess-tune)

1. Decide the figure's **pose + distinguishing inset features** up front (rubric rules 2 & 3).
2. Write a generator script (`make_<name>.py`) that redraws and saves `pipgirl.png`/etc. **Keep the script** — it IS the source of truth; regenerate to revise, don't hand-edit a binary.
3. Verify the **PNG file itself** with `vision_analyze` (full-res, reliable) *before* trusting an inline browser screenshot. The browser-vision screenshot pipeline downscales/compresses small figures and frequently misreads thin dark details that the full-res file reads fine.
4. Swap the SVG for `<img src="name.png">`.
5. Cache-bust so the viewer actually gets the new asset: bump the app version and reference `?v=<ver>` on the tab/asset fetches (if building into the PIPNARU-style tabbed terminal, see `references/health-terminal-cache-busting.md`).

## Pitfalls

- **Dark outline stroke over bright fill reads as wireframe.** At small size a `stroke="#1e8f34"` on a bright `#4aff6a` fill renders as hollow lines. Either drop the stroke entirely or make it meaningful/inset.
- **Don't confuse "screenshot vision says X" with reality.** Consult the asset file at native resolution when judging quality, not a miniaturized screenshot.
- **A lowercase/three-stroke "N" can read as Cyrillic И.** For a recognizable letter, use two filled rectangles (left/right columns) + one thick diagonal line, not three thin strokes.
- **`ImageDraw.rectangle` needs y0 < y1** — passing coords out of order raises `ValueError`. Track y carefully when stacking neck/limbs.

## References
- `references/vault-boy-design-research.md` — the Bethesda Vault Boy origin + design-rubric excerpts.