# Vault Boy design research — how Bethesda/Interplay actually did it

Source: Wikipedia "Vault Boy", Fallout Fandom wiki "Vault Boy", multiple artist interviews. Aug 2026.

## The origin pipeline (not one genius stroke, a hand-off chain)

1. **Leonard Boyarsky** (creative director, Fallout 1) did the first concept art — the "skill guy."
   He drew inspiration from **1950s films** and the **Monopoly board game's Rich Uncle Pennybags**.
2. **George Almond** drew the first few skill/perk cards, beginning the progression.
3. **Tramell Ray Isaac (T.Ray)** took over and **finalized the "look."**
4. **Natalia (Natalya) Smirnova** redrew *every* Vault Boy image for Fallout 3, 4 and 76.

Lesson: iconography is iterated through multiple passes by different people — a curation
pipeline. An agent can reproduce the *process* (concept → several refinement passes) but
should not expect the first pass to be iconic.

## The design rubric (what makes it READ at any size)

1. **Base it on a recognizable cultural archetype** — Rich Uncle Pennybags / 50s ad-man,
   not an invented blob. Everything about Vault Boy evokes the 1940s: hairstyle, dimpled smile, art style.
2. **One signature pose** — the thumbs-up. Developers (Brian Fargo, Tramell Isaac) confirmed
   the thumb is NOT a mushroom-cloud distance gauge; it's simply Vault Boy's **"positive attitude"** —
   "everything is ok, when it really isn't." The meaning lives in the pose, and is sardonic.
3. **Simple silhouette that reads at a foot OR a wall.** He's a corporate mascot in the style of
   50s corporate mascots — simple shapes, bold contrast.
4. **Inset contrasting features** — face and hair are darker shapes set into the lighter head.

## The ME/CFS-honest adaptation (PIPNARU "Adora-Girl")

- Keep the rubric, swap the pose meaning: Vault Boy = "all good (when it isn't)";
  Adora-Girl = **"all good — because I actually rested."**
- Inset dark hair + two dot eyes + smile on a lighter green head; rest arm thumbs-up;
  clean "N" monogram (two filled columns + one thick diagonal — thin three-stroke "N" reads as Cyrillic И).
- Name the figure something the user picks ("Adora-Girl" was chosen here).

## Tooling note

FAL image backend was out of balance during this work — the PNG route (PIL ImageDraw)
was the reliable fallback and turned out to be the *better* technique anyway for tiny icons.
See SKILL.md core rule.