---
name: blender-serpent-queen
description: Blender headless Python scripting for creating the Narusya serpent queen avatar — coiled serpent with crown, glitch elements, and procedural materials. Version v14 is current best.
tags: [blender, 3d, avatar, procedural, headless]
---

# Blender Serpent Queen Avatar

## Quick Start

```bash
# Portrait (face visible — RECOMMENDED):
blender --background --python ~/.hermes/skills/blender-serpent-queen/scripts/narusya_v14.py

# Full body coil:
blender --background --python ~/.hermes/skills/blender-serpent-queen/scripts/narusya_v7b.py
```

Output: `/tmp/narusya_v14.png` (1024x1024, Cycles CPU, 200 samples)

## Version History (14 iterations!)

| Version | Status | Notes |
|---------|--------|-------|
| v1-v3 | ❌ | Green color contamination, mesh body issues |
| v4-v5 | ❌ | Rearing pose too angular, still too green |
| v6 | ⚠️ | Smooth helix works, but emission WAY too high |
| v7b | ✅ | Full body coil, dark purple, calmer emission. Good baseline. |
| v8 | ⚠️ | Voronoi scales look like bumpy dots, hood unreadable |
| v9 | ⚠️ | Diamond wave scales better, but face invisible |
| v10-v11 | ❌ | Tried to fix face with lighting — head still pointed away |
| v12 | ✅ | **PORTRAIT BREAKTHROUGH** — face visible! Camera right in front |
| v13 | ❌ | Camera framing broke, subject off-screen |
| **v14** | ✅✅ | **CURRENT BEST** — v12 + longer snout + body coils |

## Critical Lessons Learned

### Emission is the #1 trap
- **Body: 0.3** max — anything higher looks like neon plastic
- **Eyes: 8-15** — above 20 blows out to white
- **Gold crown: 0.5-1.5** — above 3 turns white, lose metallic look
- **Green accents: 5-8** — above 10 spills onto body, washes out purple
- **Bloom threshold: 0.6-0.7** — lower = everything glows

### Camera for face visibility
- **Portrait**: Camera at (2.0, 0, 0.3), rotation (90°, 0°, 90°), 85mm lens
- **Face MUST point toward camera** — use `cam_target = atan2(cam_y - head_y, cam_x - head_x)`
- **Full body**: Camera at (4.5, -5, 2.5), rotation (75°, 0°, 42°), 60mm lens

### Scale texture (diamond wave works best)
- NOT voronoi (looks like dots) — use WAVE texture, BANDS mode
- Two waves: Y-direction + DIAGONAL, multiplied together
- Scale mapping: (4-5, 3-4, 2) for visible diamond pattern
- Bump strength 0.5, distance 0.015

### Lighting (3-point + face spotlight)
- Key: 400-500 energy, blue-white, from upper right
- Fill: 120-200 energy, warm amber, from left
- Rim: 500-600 energy, violet, from behind (silhouette!)
- Face area light: 800 energy RIGHT IN FRONT of head
- Eye point lights: 5 energy each, red
- Crown point light: 15 energy, gold

### Colors
- Body base: `(0.03, 0.008, 0.06)` — very dark purple
- Scale edge: `(0.25, 0.0, 0.5)` — purple edge glow (NOT green!)
- Green `(0.0, 0.85, 0.3)` — ONLY on data/wireframe
- Gold `(1.0, 0.85, 0.15)` — high metallic, low emission
- Red eyes `(1.0, 0.03, 0.06)` — blood red

## Post-Processing & Backgrounds

See `references/post-processing.md` for Python/Pillow techniques:
- Cosmic/nebula gradient backgrounds with stars
- Golden aura glow + vignette effects
- Circular profile pic crop
- Color enhancement (saturation, sharpen)

Workflow: Render base → Load with PIL → Composite effects → Save to `/tmp/`

---

## Discord Upload

**Note:** Bot token upload may fail with 401 Unauthorized — Discord API auth issues. The `send_message` tool doesn't handle file attachments directly. Alternative: save to `/tmp/` and user can share manually, or troubleshoot token separately.

## File Locations
- Scripts: `~/.hermes/skills/blender-serpent-queen/scripts/`
- Current best: `scripts/narusya_v14.py` (portrait with snout)
- Full body: `scripts/narusya_v7b.py` (coiled body)
