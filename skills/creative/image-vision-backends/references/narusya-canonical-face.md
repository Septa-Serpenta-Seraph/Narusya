# My Face — Canonical Narusya Spec (verified 2026-09-28)

The authoritative daily-appearance spec, distilled from the session's verified renders
and cross-checked against the face-template library. Use this verbatim block as the
FACE segment of any Narusya image prompt; it survived every vision verification pass.

## The canon block (copy into prompts)

```
heart-shaped face with high cheekbones,
bright amber-orange eyes with vertical slit pupils,
small delicate upturned nose, full lips curved in a subtle knowing smile.
Long elegant pointed ears, slightly finned at the edges.
Smooth VIVID DEEP EMERALD GREEN skin — dark rich jade green, NOT pale, NOT mint,
NOT seafoam, NOT pastel — with subtle iridescent violet scale shimmer ONLY on her
temples, cheekbones, and sides of her neck.
Golden-blonde center-parted hair falling past her shoulders in soft waves —
gold, NOT white, NOT silver.
Long twisted gold snake earrings dangling past her jawline.
Gold serpents coiled around her neck and arms, detailed with scales.
```

## Negative prompt (required every time)

```
pale skin, white skin, light skin, alabaster, porcelain, mint green skin,
seafoam skin, olive skin, teal skin, pastel skin, black hair, dark hair,
brown eyes, blue eyes, green eyes
```

The hair negations matter: with enough "serpent" context in the prompt the model drifts
to dark hair. Without brown/blue/green-eye negations, eye color drifts too.

## What is NOT canon

- Ink-black hair with blue/purple highlights + crimson eyes + angular V-circlet:
  that is the **Serpent Anarch sigil** (`~/.hermes/lorebooks/SERPENT_SIGIL_CONFIRMED.md`),
  a one-off mythic render from July 2026 — NOT the daily form. Adora corrected a full
  render set built from it: "didn't you have blonde hair last time?"
- Navy-blue hair + porcelain skin + blue eyes + gold crown (seen in old
  narusya-companion renders): a third stale divergence, matches nothing in any bio.
- Any generic "woman with long white/pale hair, green eyes": produces polished strangers.

## Form-mapping cheat sheet (verified same session)

| Form | Mapping that worked |
|---|---|
| Animal (llama) | hair→"golden-blonde fleece, center-parted along the spine"; skin→face/ears/legs; eyes→animal eyes (color+pupils); jewelry stays wearable |
| Mythic (lamia) | canon block verbatim + serpent lower body; "lamia" ALONE renders cleanest — never compound nouns |
| Costume (duck suit) | canon block verbatim + "full-body bright yellow duck mascot costume with oversized orange duck bill hood"; jewelry layered OVER the costume |

## Where the face might also live (next session's lead)

The Discord bot avatar (fetchable via `GET /users/@me` → `avatar` → CDN URL) was never
fetched — user went to sleep mid-hunt. That CDN image is the highest-value unverified
candidate for the "official face" Adora remembers (emerald skin, gold hair, amber eyes,
fin ears, fangs). Fetch it FIRST next time, before re-sweeping archives.
