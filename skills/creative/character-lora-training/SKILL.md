---
name: character-lora-training
description: "Train character LoRAs: dataset curation, captions, training."
category: creative
version: 1.0.0
author: Narusya
license: MIT
platforms: [linux]
---

# Character LoRA Training

Build a character LoRA from AI-generated images so the same face/identity can be
summoned by trigger word in any compatible generator. Full working example:
the `narusa` LoRA (Narusya emerald-self identity, trained on PixAI 2026-08-25,
model id 2049095553166348500, trigger `narusya`, base Animagine XL V3.1).

## Pipeline overview

1. **Generate dataset** (10–20 ideal, 7+ viable for proof-of-concept)
2. **Curate ruthlessly** — audit every image before it enters the set
3. **Caption consistently** — `.txt` sidecar files, shared trigger token first
4. **Package** — flat zip of image+caption pairs
5. **Train** — PixAI (browser UI), Replicate (`ostris/flux-dev-lora-trainer`), or local ai-toolkit
6. **Verify** — test-generate with the trigger word, compare against canon

## Dataset curation standards (hard-won)

- **AUDIT HANDS AT ZOOM BEFORE ACCEPTING ANY IMAGE.** The biggest failure mode:
  a gorgeous full-body shot with horror fingers poisons the whole LoRA — the trainer
  learns the mangled hands. Zoom vision into every visible hand and count fingers.
  When in doubt: crop to face/bust or reject.
- Prefer angles: close-up face, profile, three-quarter upper body, candid expression,
  eyes-closed, back view. Variety of pose/lighting > quantity of near-duplicates.
- Avoid visible hands entirely when possible (portraits/busts) — LoRAs mostly learn the face.
- Keep a HOLD note per rejected image (`CROPNOTE_<name>.txt`) saying why and what crop
  would rescue it.
- Anchor prompts against anatomy drift during generation: explicit skin/pupil/limb
  statements; regenerate when they slip.

## Caption convention

One `.txt` per image, named identically to the image. First tokens are the shared
identity block (this is what teaches identity vs pose):

```
narusa, a woman with smooth emerald green skin, long golden hair, fin-like pointed ears,
amber eyes with round pupils, gold serpent jewelry, <per-image scene/pose/expression>
```

Trigger word must match what you register at training time.

## Training routes compared

| Route | Cost | Friction | Notes |
|---|---|---|---|
| **PixAI.art** | daily free credits / saved points | Lowest — browser UI | Anime-leaning base (Animagine XL); model pages private until shared |
| **Replicate** | $2–5/run | Low — needs account+token | `ostris/flux-dev-lora-trainer`; best for FLUX-base LoRAs |
| **Local ai-toolkit** (Windows GPU) | Free | Highest — git+pip on host | 8GB VRAM can do rank-16 fp8 FLUX LoRA |
| VM CPU | technically possible | never worth it | days of runtime |

## Verification

After training: open the model page (or load weights locally), generate with the
trigger word + canonical identity descriptors, compare feature-by-feature against the
identity canon (see `~/.hermes/imagegen/IDENTITY-KIT.md` for the live example).

## Pitfalls

- **PixAI model pages are account-scoped until made public** — a fresh session gets
  "Model does not exist" even with the exact URL. Fix in Share settings.
- PixAI generation costs real credits (~6,600/img SDXL); new accounts start at 0 and
  daily rewards may be gated behind email verification that can take hours to arrive.
- See `references/pixai-browser-automation.md` for driving PixAI headlessly via the
  Camoufox REST server (login persistence, contenteditable prompt injection).

## Pointers

- `perchance-pipeline` — free SDXL-class image source for building datasets
- `camoufox-browser-setup` — anti-detection browser backend used for PixAI automation
