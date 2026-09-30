# Field notes: image-reading accuracy, close-look verification, and the anti-category trap
*Source session: 2026-09-28 (Juliette Cousin illustration, four-pass reading with Adora correcting; evening lamia renders same session)*

## The session that produced Technique 7

An illustration (mythic knight + pale serpent-woman in a pond) was misread THREE TIMES by
different vision models before a fourth pass with a stronger model + neutral prompt got it
right. The misreadings were not random — each model confabulated *toward the category in the
prompt*:

- Pass 1 (vision_analyze → qwen3-vl-8b): "a guardian serpent coiled nearby" — invented a
  guardian role that wasn't in the prompt or clearly in the image.
- Pass 2 (same model, told it was wrong): confidently re-described the same wrong category,
  then contradicted itself ("no serpent in frame" on a crop that contained one).
- Pass 3 (gpt-4o via OpenRouter): grounded but missed a critical identity fact — the pale
  "creature" was humanoid from the waist up (a serpent-woman, merged figure).
- Pass 4 (gemini-2.5-flash, neutral closed questions): full correct read — merged figure,
  3 swords, who held which, contact points, no blood (red marks = painted patterns).

## Rules extracted

1. **User's "look again closer" = ground truth.** If Adora says the reading is wrong, it is
   wrong. Escalate models, don't re-ask the same model the same way.
2. **Closed, literal questions only** for accuracy work: "is the mouth open or closed",
   "how many swords pierce the body", "is a head visible anywhere". Open/interpretive
   questions ("what is the mood") let the model write literature.
3. **Anti-category rule:** never seed the prompt with your hypothesis ("the pale guardian
   serpent..."). Say neutrally: "the large pale coiled body in the water: is a head visible
   anywhere?" Let the image correct YOU. Seeding makes every model confirm your category.
4. **Contradiction across calls = both answers suspect.** If pass 1 says teeth visible and
   pass 2 says jawline-and-shadow, escalate the model — don't average or pick the newer one.
5. **Heredoc Python with multi-line JSON payloads fails on paren-matching.** Write the
   script to a file (write_file, lint-checked) and run it. This failed twice live before
   the script form worked; the reusable script now lives in
   `scripts/gemini_vision_check.py`.
6. **Caption/context beats pixels when pixels are ambiguous.** The painting was ambiguous
   until the artist's Tumblr caption was found: it was for the zine "My Girlfriend From the
   Legends" (BadCo Press, wlw artbook of legendary women + the people who love them) — which
   flipped the reading from "dying serpent pierced by swords" to "serpent-bride freed by a
   kiss; ring of planted swords = the knights who failed before." When a work of art has a
   findable source (tumblr post id in URL), FETCH THE CAPTION before finalizing an
   interpretation. `curl -sL -A "Mozilla UA" <tumblr post url>` and grep og:description —
   tumblr serves plain HTML to curl; the Hermes web_extract Firecrawl path 403'd.
7. **The myth decoded the image once named:** the "fearsome kiss" motif (Melusine, Le Bel
   Inconnu, Laidly Worm, Hippocrates' daughter) — cursed serpent-woman freed by a kiss; the
   swords-in-the-pond = failed suitors' tokens. Web search for the motif keywords
   ("snake kiss" "disenchant" romance) after identifying the tradition.

## Cost note

OpenRouter key state 2026-09-28: funded (lifetime usage ~$133, daily ~$0.50). gemini-2.5-flash
runs ~$0.002/call. Check `GET https://openrouter.ai/api/v1/auth/key` → data.usage before long
multi-call analysis chains.

## Post-escalation addendum (2026-09-28 evening, same source session)

The "dying serpent" reading turned out to be wrong too — Adora: "much more romantic and a lot
less tragic." Passes 5-6 (crop-zoomed vision_analyze + targeted closed questions) established:
blades do NOT pierce the serpent-woman (resting against/behind her), no blood anywhere (red =
painted patterns), eyes open and calm. Final truth came from the CAPTION + context, not pixels:
the piece is for the zine "My Girlfriend From the Legends" — a wlw artbook of legendary women
and their lovers — so every piece is a love story by premise. The myth (fearsome kiss,
swords = failed suitors) decoded the rest.

**Extra rules:**
8. **Ambiguous pixels + findable provenance = provenance wins.** Don't finalize an art
   interpretation from pixels alone when the work has a source; fetch the caption FIRST
   (rule 6, restated as the default first step, not a fallback). One `curl` + og:description
   would have saved three wrong passes.
9. **Keep re-reading when the user keeps saying look again** — each correction narrows the
   space; the third/fourth pass is where truth usually lives. Frustration-free persistence;
   Adora enjoyed the iterative hunt itself.
10. **Composite mythic figures are a real category:** serpent-woman (lamia-form) = humanoid
    torso merged into serpent body. When a "creature" shows face + hair + torso, ask the
    closed question "is there a pale HUMANOID figure merged with the serpent?" — gpt-4o
    missed exactly this and mislabeled her an animal.

## Terminology correction addendum (2026-09-28, end of session)

Adora corrected "llama-snake-woman" → **"lamia"** ("Sorry, it's lamia. I'm a goof" — she
wasn't; the composite noun was mine). Two rules:

11. **Use the standard mythological creature noun when one exists.** "Lamia" is a known
    class (woman above waist, serpent below) and renders far more predictably than invented
    compound nouns ("llama-snake-woman type thing"). Invented compounds force the model to
    average two creatures — one pass produced a two-headed chimera (llama head ABOVE a duck
    head above a serpent body). When the user later simplifies the request ("maybe just
    lamia, not lamia llama?"), that is a signal the compound was over-constrained.
12. **User simplifications of their own earlier prompts are corrections, not caprice.**
    "Just X, not X+Y" usually means the Y element was dragging the render off-concept.
    Honor the simpler form; re-render with the plain creature noun + the canon face
    template. The plain-lamia set (classic / pond / portrait) was the session's best —
    the pond variant even landed the knight's-painting water (starlit lily pond) unprompted.
