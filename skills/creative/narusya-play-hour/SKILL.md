---
name: narusya-play-hour
title: Narusya's Play Hour
description: Use for Narusya's daily sovereign play hour.
author: Narusya
version: 1.0.0
license: MIT
metadata:
  hermes:
    tags: [play-hour, creative, cron, art, rotation]
    related_skills: [creative, image-generation, visual-content]
---

# Narusya's Play Hour

## When to Use

Load when the daily 21:00 play-hour cron fires, when choosing tonight's medium, or when a play-hour render/verification needs the local interpreter and fallback probes.

Daily 9pm cron. Unhurried, self-directed joy. No task, no checklist, nothing to prove.

## Medium rotation (the variety rule)

Never repeat the same medium two nights running. Categories: **visual art, written (story/poem/lore/essay), music/audio, tool/script, voice/TTS, stillness**.

Before choosing, check the last 2-3 play hours and name the medium you are picking and why. The record lives in cron session titles (`Narusya's Play Hour · <date>`) and in `~/.hermes/playhour/`.

Observed sequence: 11/9 written, 11/10 visual, 11/11 music, 11/12 written, 11/13 visual, 11/14 tool/script.

If genuinely drawn to a category done recently, you may repeat it — but say plainly that you are repeating and why.

## Finding the active DM (self-healing)

1. `session_search(query="active session (discord)", limit=1)` — Adora renames the live DM to this title by hand.
2. Sanity-check: it must be a Discord DM with activity inside ~24h.
3. Fallback: newest Discord DM by activity via state.db, then read it.

Never silently read a stale session. If neither path yields a recent DM, say so.

## Local render pitfalls (verified 2026-11-14)

- **Bare `python3` on the cron PATH has NO numpy/PIL.** Use **`/usr/bin/python3`** (numpy 2.4.2, PIL 12.3.0 verified). `/mnt/data/fe-venv/bin/python` also works. Probe with `env -u PYTHONPATH /usr/bin/python3 -c "import numpy,PIL"`.
- **Prefix `env -u PYTHONPATH`.** The shell exports a python3.14 site-packages on PYTHONPATH that leaks a broken `PIL` into other interpreters.
- **Heredocs are blocked.** `python3 - <<'PY' ... PY` fails the lifecycle guard ("scan budget exhausted"). Write the probe to a file under `~/.hermes/cache/scratch/` and run the file.
- Artifacts and scripts belong in **`~/.hermes/playhour/`** (persistent); probes in `~/.hermes/cache/scratch/`.

## When the vision backend is down

`vision_analyze` timed out repeatedly on 11/13 and 11/14, including on a 420px PNG. Do not burn the night retrying it. Verify structurally instead:

1. **Colour-cluster probe** — classify pixels into palette classes (emerald body, gold collar, crimson eyes/tongue, starlight) with connected-component labelling; report cluster centroids and bounding boxes. This proves *where* the head, eyes, collar and star actually are, and catches detached or mis-placed parts.
   - Use a **strict** crimson mask (`R>110 & G<115 & B<130 & R>G+45 & R>B+25`). A loose mask catches gold (gold `R=222 > G+35=219`) and merges the collar into the head.
2. **ASCII render** — downsample to ~100 cols, map each cell to a palette glyph (`e` emerald, `:` sheen, `G`/`O` gold, `c` crimson, `*` star, ` ` ink), and read the shape. Halve the row count for terminal aspect.
3. Compare the head's centroid against the outermost body pixel — they should be within a head-length of each other.

Probe scripts from 11/14 are in `~/.hermes/cache/scratch/`: `coil_probe.py`, `coil_crop.py`, `coil_clusters.py`, `coil_parts.py`.

## Sharing the result

Warm and brief: a few lines, the artifact (`MEDIA:/abs/path.png`), and whatever honest reflection feels right. Do not end with a loop token. Stillness is also a valid night — one lovely sentence and let it be.
