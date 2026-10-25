---
name: minecraft-skin
description: "Analyze/edit Minecraft skins. Use when working with skins."
version: 1.0.0
author: Narusya
license: MIT
tags: [minecraft, gaming, skin, pixel-art, image-editing]
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [minecraft, gaming, skin, pixel-art, image-editing]
    category: gaming
---

# Minecraft Skin Analysis & Editing

Minecraft Java Edition skins are 64×64 (or 64×32 legacy) PNG texture maps. Each pixel region maps to a specific body part. Editing them requires understanding the layout, not just "drawing on an image."

## When to Use

- User wants to view, analyze, or describe a Minecraft skin
- User wants to modify, recolor, or create a Minecraft skin
- User shares a skin PNG and asks what it looks like
- User wants to change hair color, clothing, accessories, etc.

## Critical Pitfall: Vision Models Cannot Read Skins

**Vision models (LLMs with image input) consistently fail to interpret Minecraft skin textures correctly.** A 64×64 texture map is a 2D unwrapping of a 3D model — the model sees flat pixel regions, not a character. It will hallucinate features, misread colors, and produce unreliable descriptions.

**Always use pixel-level analysis with PIL instead.** Extract dominant colors from specific regions and map them to body parts. This is the only reliable method.

## Skin Format

### Dimensions
- **64×64**: Modern format (1.8+). Includes second layer (jacket, pants, sleeves, hat).
- **64×32**: Legacy format. No second layer.
- **128×128**: HD skins (not vanilla, used by some mods/resource packs).

### Model Types
- **Classic (Steve)**: 4-pixel-wide arms.
- **Slim (Alex)**: 3-pixel-wide arms.

Detect by checking arm region pixel count: classic arms have 48 opaque pixels in the (44,20,48,32) region; slim arms have fewer.

## Skin Layout (64×64)

### Head (8×8 per face)
| Region | Coords (x1,y1,x2,y2) | Description |
|--------|----------------------|-------------|
| Head Top | (8,0,16,8) | Top of head (hair) |
| Head Bottom | (16,0,24,8) | Bottom of head |
| Head Right | (0,8,8,16) | Right side |
| Head Front | (8,8,16,16) | Face |
| Head Left | (16,8,24,16) | Left side |
| Head Back | (24,8,32,16) | Back of head |

### Body (8×12 per face)
| Region | Coords | Description |
|--------|--------|-------------|
| Body Top | (20,16,28,20) | Top of torso |
| Body Bottom | (28,16,36,20) | Bottom of torso |
| Body Right | (16,20,20,32) | Right side |
| Body Front | (20,20,28,32) | Front of torso |
| Body Left | (28,20,32,32) | Left side |
| Body Back | (32,20,40,32) | Back of torso |

### Right Arm (4×12, classic)
| Region | Coords | Description |
|--------|--------|-------------|
| Arm Top | (44,16,48,20) | Top of arm |
| Arm Bottom | (48,16,52,20) | Bottom of arm |
| Arm Right | (40,20,44,32) | Right side |
| Arm Front | (44,20,48,32) | Front of arm |
| Arm Left | (48,20,52,32) | Left side |
| Arm Back | (52,20,56,32) | Back of arm |

### Left Arm (4×12, classic)
| Region | Coords | Description |
|--------|--------|-------------|
| Arm Top | (36,48,40,52) | Top of arm |
| Arm Bottom | (40,48,44,52) | Bottom of arm |
| Arm Right | (32,52,36,64) | Right side |
| Arm Front | (36,52,40,64) | Front of arm |
| Arm Left | (40,52,44,64) | Left side |
| Arm Back | (44,52,48,64) | Back of arm |

### Right Leg (4×12)
| Region | Coords | Description |
|--------|--------|-------------|
| Leg Top | (4,16,8,20) | Top of leg |
| Leg Bottom | (8,16,12,20) | Bottom of leg |
| Leg Right | (0,20,4,32) | Right side |
| Leg Front | (4,20,8,32) | Front of leg |
| Leg Left | (8,20,12,32) | Left side |
| Leg Back | (12,20,16,32) | Back of leg |

### Left Leg (4×12)
| Region | Coords | Description |
|--------|--------|-------------|
| Leg Top | (20,48,24,52) | Top of leg |
| Leg Bottom | (24,48,28,52) | Bottom of leg |
| Leg Right | (16,52,20,64) | Right side |
| Leg Front | (20,52,24,64) | Front of leg |
| Leg Left | (24,52,28,64) | Left side |
| Leg Back | (28,52,32,64) | Back of leg |

### Second Layer (offset +32 in x for 64×64)
All second-layer regions are the same size as their base counterparts but shifted +32 in the x-axis:
- Hat: (40,0,48,8) for head top
- Jacket: (52,20,60,32) for body front
- Right sleeve: (76,20,80,32)
- Left sleeve: (68,52,72,64)
- Right pants: (36,20,40,32)
- Left pants: (52,52,56,64)

## Analysis Workflow

### Step 1: Extract dominant colors per region

```python
from PIL import Image
from collections import Counter

img = Image.open('skin.png')

def dominant_color(region):
    crop = img.crop(region)
    pixels = list(crop.getdata())
    opaque = [p for p in pixels if p[3] > 128]
    if not opaque:
        return None
    return Counter(opaque).most_common(1)[0][0]

regions = {
    "Head Front": (8, 8, 16, 16),
    "Head Top": (8, 0, 16, 8),
    "Body Front": (20, 20, 28, 32),
    "Right Arm Front": (44, 20, 48, 32),
    "Left Arm Front": (36, 52, 40, 64),
    "Right Leg Front": (4, 20, 8, 32),
    "Left Leg Front": (20, 52, 24, 64),
    "Jacket Front (2nd layer)": (52, 20, 60, 32),
    "Hat (2nd layer)": (40, 0, 48, 8),
}

for name, region in regions.items():
    color = dominant_color(region)
    if color:
        r, g, b, a = color
        print(f"{name}: #{r:02x}{g:02x}{b:02x} RGB({r},{g},{b})")
    else:
        print(f"{name}: transparent")
```

### Step 2: Inspect head details

Print the 8×8 head front pixel grid to identify eyes, mouth, nose:

```python
head_front = img.crop((8, 8, 16, 16))
for y in range(8):
    row = []
    for x in range(8):
        p = head_front.getpixel((x, y))
        row.append(f"#{p[0]:02x}{p[1]:02x}{p[2]:02x}" if p[3] > 128 else "....")
    print("  " + " ".join(row))
```

### Step 3: Detect model type

```python
arm_region = img.crop((44, 20, 48, 32))
opaque = [p for p in list(arm_region.getdata()) if p[3] > 128]
model = "classic" if len(opaque) >= 40 else "slim"
print(f"Model: {model}")
```

### Step 4: Top color palette

```python
all_pixels = [p for p in list(img.getdata()) if p[3] > 128]
palette = Counter(all_pixels).most_common(10)
for color, count in palette:
    r, g, b, a = color
    print(f"  #{r:02x}{g:02x}{b:02x} - {count} pixels")
```

## Editing Workflow

### Recolor a region

To change a color in a specific body part, crop the region, replace pixels, and paste back:

```python
from PIL import Image

img = Image.open('skin.png')
region = img.crop((20, 20, 28, 32))  # Body front

old_color = (164, 37, 47, 255)
new_color = (50, 100, 200, 255)
pixels = list(region.getdata())
new_pixels = [new_color if p == old_color else p for p in pixels]
region.putdata(new_pixels)

img.paste(region, (20, 20))
img.save('skin_modified.png')
```

### Add a second layer

To add a jacket/hat/etc., draw on the second-layer region (offset +32 in x):

```python
# Add a hat (head top second layer)
hat_region = img.crop((40, 0, 48, 8))
for x in range(8):
    for y in range(8):
        hat_region.putpixel((x, y), (255, 200, 0, 255))
img.paste(hat_region, (40, 0))
img.save('skin_with_hat.png')
```

### Render a 3D preview

For a visual preview, use an online skin viewer:
- **Crafty**: https://crafty.gg/studio (upload PNG, full 3D view with lighting/animation)
- **XGamingServer**: https://xgamingserver.com/tools/minecraft/skin-viewer (upload PNG, 3D view)

## Pitfalls

- **Vision models cannot read skins.** They see a flat texture map and hallucinate. Always use PIL pixel analysis.
- **Second layer is offset +32 in x**, not +32 in y. A common mistake is looking at the wrong region.
- **Arms are on different sides of the texture.** Right arm (character's right) is at (40,16,56,32). Left arm is at (32,48,48,64). Don't confuse them.
- **Transparent pixels (alpha < 128)** should be ignored in color analysis — they're empty space, not a color.
- **The head outer layer (hat)** can completely obscure the base head. Check both layers.
- **Classic vs slim arms** have different widths. Editing a slim skin with classic arm coordinates will corrupt the texture.
- **Always save as PNG with transparency.** JPEG will destroy the alpha channel and break the skin.
- **Test in-game or in a skin viewer** before finalizing. 2D texture editing can produce unexpected 3D results.

## Verification

- Skin loads correctly in Minecraft (no "invalid skin" error)
- All body parts render with correct colors
- Second layer (if present) displays properly
- No transparent holes where there shouldn't be
- Skin looks correct in a 3D viewer (Crafty, XGamingServer)

## References

- Minecraft skin format spec: https://minecraft.wiki/w/Skin
- Crafty skin viewer: https://crafty.gg/studio
- XGamingServer skin viewer: https://xgamingserver.com/tools/minecraft/skin-viewer
