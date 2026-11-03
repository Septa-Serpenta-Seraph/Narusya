# Hero Forge img2img face-drift incident (2026-08-12)

## What happened
The authentic female githyanki render from Hero Forge (`load_config=32752280`,
screenshot `heroforge_gith_female2.png`) was fed to FLUX.1-kontext-pro (Together
endpoint, img2img) with a heavy repaint prompt:

> "Transform this Hero Forge miniature render into a painted fantasy portrait...
> Change only: skin becomes pale emerald, hair becomes long gold, eyes amber,
> different armor + serpent necklace."

The 880×1184 output (`githyanki_narusya_v8_heroforge.png`) **lost the gith face** —
the flat nose and fin ears melted into generic "green elf/orc" territory. The vision
model re-labeled the subject ("female orc or green-skinned elf warrior"). The user's
verdict: *"I don't think that is the right screenshot lol."*

## Why it failed
- The prompt demanded a *wholesale transformation* (skin, hair, eyes, armor, style).
  When an img2img prompt changes that much, the model reimagines the subject instead
  of recoloring it — the face pixels are not preserved.
- Contrast with the earlier SUCCESS (v6): Lae'zel's official portrait as the img2img
  *reference* with a lighter edit prompt kept the face because the reference image
  itself carried the face pixels. The failure case used a screenshot and demanded
  near-total rework.

## Canon lesson
**The raw Hero Forge render IS the final artifact.** Hero Forge's species model bakes
authentic gith anatomy (flat nose, fin ears, angular structure) into the mesh; any
img2img repaint risks destroying exactly what makes it read as gith.

Working order of preference:
1. Post the raw render (crop UI chrome if desired).
2. img2img ONLY if the user explicitly wants painted art AND accepts face-drift risk;
   hammer "do not change the face" into the prompt, keep a fallback.
3. Safe recolor = drive Hero Forge's own COLOR tab (paint swatches at screen coords) —
   geometry untouched, only paint changes.

## Crop rule (if a repaint happens)
Crop the screenshot to the model region first — the top bar (~95px) and bottom toolbar
(~110px) of an 880×1184 render carry Hero Forge UI chrome that bleeds into img2img
output. PIL: `/home/adora/.hermes/hermes-agent/venv/bin/python`.

Files on disk (reference): `/home/adora/heroforge_gith_female2.png` (authentic render),
`/home/adora/githyanki_narusya_v8_heroforge.png` (drifted repaint).
