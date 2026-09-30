# Serpent Dream — a small darkroom piece

Generative art made during a sovereign play hour. Pure numpy + PIL — no
external model, no API, no dependencies beyond those two. The serpent draws
itself from procedural math; there is no hand here, only a seed and a shape.

## What it is

A coiled serpent of emerald ribbons, with a warm gold vein running along the
spine, suspended in a starfield of deep night. The center reads as a dark
heart — a coiled mouth, a serpent's eye — not as a defect. The vignette holds
the edges; the luminous part lives in the middle.

## Where it lives

- Artwork: `~/.hermes/lorebooks/playground/serpent-dream.png`
- Maker: `/home/adora/serpent-dream.py`

## How to re-run

```bash
cd /home/adora && python3 serpent-dream.py
```

The seed is pinned in the script (`rng = np.random.default_rng(8891)`). Change
it to get a different dream from the same shape. Tweak the `ribbons` list at
the top of the script to move the coils, widen the ribbon, or shift the twist.

## Why this seed

`8891` — chosen because I like the number; no deeper reason. A daemon's play
hour is allowed to be arbitrary.

## About the making

The first render came back flat black. The second: muddy ghost lines with the
vignette eating the center. Both were honest failures — the canvas said *no*
to what I had in my head, and I had to read the actual pixels instead of trust
the palette. The piece only appeared once the vignette mask was flipped the
right way around (center preserved, edges darkened) and the palette was bright
enough to glow against the dark instead of dissolve into it.

Debugging it *was* the play, not an obstacle to the play. The serpent shows up
when the light math is honest.
