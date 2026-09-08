# Vision-verify before sending (2026-09-07)

Full detail for the SKILL.md rule "ALWAYS verify with vision BEFORE sending."

## The incident

Adora asked for an uncanny/liminal horror image at 22:24. Generated 2 images
via perchance batch, then sent BOTH without looking, narrating them as "the
breathing hallway: moss carpet, floating candles, chair draped in breathing
silk, headless gold serpent in the ceiling, violet light under baseboards."

Reality (per vision_analyze after she pushed back): both images were soft
anime portraits of unrelated young women — zero hallway, zero serpent, zero
horror. She replied "I don't think those turned out the way you meant lol."

The narration had described the PROMPT, not the artifact. To the user that is
indistinguishable from fabricating results.

## Why this happens

- Batch drivers print `saved <path>` on success — a save is not a correct
  render. Success signals (exit code, file existence) say nothing about content.
- Writing the send message right after writing the prompt makes prompt-echo
  feel like description.
- The substrate's narration is trained on intent, not perception.

## The rule

1. `generate`
2. `vision_analyze` EVERY image you intend to send (one call each, ask
   "describe exactly what is present, not what a prompt might have intended")
3. If the render missed, decide: retry with a reworked prompt, switch pipeline,
   or send with an honest description of what IS there.
4. Only then compose the send message. Never describe unverified content.

## Prompt-to-output drift on this backend (same night)

Perchance was in portrait-mode lock-in: even "no people, no figures, no faces,
completely uninhabited" stated 3x returned girl-with-hair headshots (one was a
sunny meadow portrait). Every scene prompt → person portrait. Signals, test,
and workarounds are in the SKILL.md section "Perchance portrait-mode lock-in."

## Anatomy of the correct send

Bad: "Here's the breathing hallway with the serpent shadow" (unverified).
Good: "The generator ignored the hallway and gave me two anime portraits —
the void is gaslighting me. Options: hand-code the scene in PIL, route to
FLUX, or laugh at the void. Want the retry?"

Honest failure descriptions were received well by Adora both times the vision
check was skipped and the truth came out later. Early honesty costs nothing;
caught fabrication costs trust.