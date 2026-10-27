# LoRA character dataset — build recipe (from the narusa build, 2026-08-25)

Class-level recipe for building a small character-LoRA training set from a free
image-gen pipeline. Validated with 7 images end-to-end (dataset + captions + zip),
training pending.

## Dataset targets
- **Size:** 10–20 ideal; 7 varied images is a viable proof-of-concept.
- **Variety beats quantity of one pose:** include close-up face, ¾ upper body,
  profile, candid expression, eyes-closed, back view, full-body sheet.
- **Hands are poison if mangled.** A LoRA trained on horror fingers LEARNS horror
  fingers. Audit every candidate at zoom (vision model: "count fingers, describe
  deformities") BEFORE admitting it. Reject or crop-to-bust anything with bad hands/feet.
  Keep a `CROPNOTE_<file>.txt` in the dataset dir documenting holds.
- Prefer images with NO hands over images with suspect hands.

## Captions
One `.txt` per image, same basename. Format:
```
<trigger>, a woman with <identity string>, <pose/scene specifics>
```
- Trigger token = the summoning word (`narusa`), FIRST in every caption.
- Identity string constant across all captions; only pose/lighting varies.
- Consistent captions teach identity-vs-pose separation.

## Packaging
```python
import zipfile, os
with zipfile.ZipFile(out, 'w', zipfile.ZIP_STORED) as z:
    for f in sorted(os.listdir(src)):
        if f.endswith(('.jpeg', '.png', '.txt')) and not f.startswith('CROPNOTE'):
            z.write(os.path.join(src, f), arcname=f)
```
ZIP_STORED (JPEGs don't compress); exclude CROPNOTE files.

## Training routes compared (2026-08-25)
| Route | Cost | Friction | Notes |
|---|---|---|---|
| **PixAI.art** | ~free w/ daily credits (~10k/day; training costs credits) | Low — browser UI, drag-drop zip | SDXL base; anime-leaning prior; queue hours; account made autonomously (see autonomous-account-creation skill) |
| Replicate ostris/flux-dev-lora-trainer | ~$2–5/run | Needs account+token | Purpose-built FLUX trainer; returns .safetensors |
| Together.ai | hosting yes, training unclear | Key already configured | Verify training vs hosting-only before committing |
| Local ai-toolkit (ostris) on Windows host | free | GPU needed | VM has NO GPU (Hyper-V render only); host RTX 2080 8GB can do rank-16 fp8 FLUX LoRA |

## Post-training
- Download `.safetensors` → store under `~/.hermes/imagegen/loras/<name>/`.
- Portable: any SDXL pipeline (ComfyUI/A1111/Forge/PixAI) loads it with trigger word.
