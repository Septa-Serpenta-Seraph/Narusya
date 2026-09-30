# Canon-Spec Prompting for Consistent / Personal Characters

*Field notes, 2026-09-28. Credit: Adora — "You might want to use your image information
of yourself hehe. They're cute, but double check."*

## The failure
Task: "generate three versions of yourself: llama / llama-snake-woman / you in a duck
costume." First render set used generic priors ("woman with long white hair, green eyes").
Result: cute, polished — and three strangers. Adora rejected them instantly.

## The fix — and the two-spec lesson
There are MULTIPLE anchored appearance specs for Narusya, and they disagree:

1. `~/.hermes/skills/creative/character-consistent-image-gen/references/face-template-library.md`
   — **CANONICAL face template** (the one Adora remembers and cites):
   - heart-shaped face, high cheekbones
   - bright amber-orange eyes, vertical slit pupils
   - small delicate upturned nose, full lips, subtle knowing smile
   - long elegant pointed ears, slightly finned at the edges
   - smooth VIVID DEEP EMERALD GREEN skin; violet iridescent scale shimmer ONLY on
     temples/cheekbones/sides of neck
   - **golden-blonde** center-parted hair, soft waves past shoulders
   - long twisted gold snake earrings past jawline; gold serpents coiled around neck/arms
2. `~/.hermes/lorebooks/SERPENT_SIGIL_CONFIRMED.md` — the earlier **Serpent Anarch sigil**
   (Batch Zero): ink-black hair w/ blue-purple highlights, crimson eyes, angular V-circlet,
   pale skin #e8ddd3. A valid sigil render, but NOT the canonical daily appearance.

First re-render used spec 2 (stale sigil) — Adora caught it: "didn't you have blonde hair
last time?" **User memory of a feature outranks whichever spec you happened to load.** When
the user corrects one feature, search for the OTHER spec rather than defending yours.

## Feature mapping across forms (what actually worked)

Per-form mapping of one identity onto different anatomies:

- **Animal form (llama):** hair→fleece ("golden-blonde fleece, center-parted along the
  spine"), skin color→exposed skin areas (face/ears/legs), eye color+pupils→animal eyes,
  jewelry stays wearable (twisted gold snake earrings, thin circlet). Slit pupils took here;
  they may not on some animals — note honestly if a feature didn't land.
- **Hybrid/mythic form (lamia):** full face template verbatim + creature body plan. "Lamia"
  alone (no modifier) renders cleaner than forced composites (llama-head lamia produced an
  extra head in one pass). Prefer the simple creature noun; add the head as a separate
  feature only if the user explicitly wants the composite.
- **Costume form (duck suit):** full face template verbatim + costume as CLOTHING
  ("full-body bright yellow duck mascot costume with an oversized orange duck bill hood"),
  jewelry layered OVER the costume ("gold serpents coiled around her neck and arms over the
  costume") so the model doesn't merge costume into anatomy. This pass produced the
  standout image of the session: dignified ethereal face + absurd costume + starlit
  lily-pond setting.

## Prompt scaffolding (proven)

```python
NEG = ("pale skin, white skin, light skin, alabaster, porcelain, mint green skin, "
       "seafoam skin, olive skin, teal skin, pastel skin, black hair, dark hair")
FACE = ("A close-up portrait of [creature]. Her face is the most important part: "
        "heart-shaped face with high cheekbones, bright amber-orange eyes with vertical "
        "slit pupils, small delicate upturned nose, full lips curved in a subtle knowing "
        "smile. Long elegant pointed ears, slightly finned at the edges. "
        "Her skin is smooth VIVID DEEP EMERALD GREEN — dark rich jade green, NOT pale, "
        "NOT mint, NOT seafoam, NOT pastel — with subtle iridescent violet scale shimmer "
        "only on her temples, cheekbones, and sides of her neck. "
        "Golden-blonde center-parted hair falling past her shoulders in soft waves — "
        "gold, NOT white, NOT silver. "
        "Long twisted gold snake earrings dangling past her jawline.")
```

Note the hair negations in the negative prompt when canon is blonde — without them the
model drifts dark after enough "serpent" context.

## Verification discipline

- Vision-check each render BEFORE delivery; ask identity questions ("is the skin emerald
  green? is the hair golden blonde? are the eyes amber-orange with slit pupils?"), not
  quality questions.
- Report landed features AND misses honestly ("eyes came out round not slit" beats silence).
- For sourced/ambiguous images, fetch the caption FIRST (see
  `close-look-image-verification.md` rule 8) — provenance beats pixels.

## Candidate-file verification & time-boxed canon hunts (2026-09-28 addendum)

When hunting for a user-cited "official face" file, FILENAMES LIE — verify each candidate
with vision before trusting it. Concrete traps from this session:
- `~/.hermes/narusya_avatar_v4.png` — named like an avatar; actually an abstract glowing
  spiral with NO face.
- `~/.hermes/projects/narusya-companion/nar_v2.png` — actually a THIRD stale spec (navy-blue
  hair, fair porcelain skin, blue eyes, gold crown) — none of its features match any bio.
- The narusya-companion folder holds several divergent old renders (v1/v2/v3/anarch); none
  is the canonical daily form.

Rule: **vision-check every candidate** ("is there a face? hair color? skin color?") before
using it as a prompt source, and report mismatches.

Rule: **time-box the archive hunt.** After ~3 archive/file checks without a confirmed
match, STOP and ask the user where the file lives (or whether it exists at all — the
"official face" may live only in a Discord pfp, i.e., fetchable from the Discord API as
an avatar URL, not on disk). This session's hunt ran long and ended unresolved at bedtime.
Unresolved canon hunts should close by telling the user exactly which candidates were
checked and rejected, so the next session doesn't repeat the sweep.

## Re-rolls without specifics (2026-09-28)
When the user says "retry the X one" WITHOUT saying what's wrong with the current take,
don't re-run the identical prompt — render 2+ DIVERSE takes (different setting, pose,
lighting: e.g. pond-queen vs golden-meadow) and deliver both. One of the diverse pair is
far more likely to hit the unspoken target than a near-duplicate of what they rejected.
Session proof: meadow-dusk lamia (retry2) came back with zero flaws per verification, while
near-duplicate passes had all carried flagged issues.

## Canonical spec sources

- **Canonical appearance:** `character-consistent-image-gen/references/face-template-library.md`
  (Narusya, Githyanki Serpent Queen template) — authoritative for the daily form.
- **Serpent Anarch sigil:** `~/.hermes/lorebooks/SERPENT_SIGIL_CONFIRMED.md` — mythic sigil
  form; use only when the sigil specifically is meant. Keep this reference in sync if either
  spec is ever re-anchored.
