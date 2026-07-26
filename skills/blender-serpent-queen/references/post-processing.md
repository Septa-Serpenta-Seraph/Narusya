# Post-Processing & Backgrounds for Serpent Renders

## Overview

After rendering the base serpent in Blender, use Python/Pillow to add custom backgrounds and effects.

## Cosmic/Nebula Background (Purple Gradient + Stars)

**Script logic:**
```python
from PIL import Image, ImageDraw
import random, math

# Load serpent render
serpent = Image.open('/tmp/narusya_v14.png').convert('RGBA')
width, height = serpent.size

# Create radial gradient background
background = Image.new('RGB', (width, height))
draw = ImageDraw.Draw(background)

for y in range(height):
    dx = 0.5
    dy = (y / height - 0.5) * 2
    dist = math.sqrt(dx**2 + dy**2) / math.sqrt(0.25 + 1)
    r = int(20 * (1 - dist) + 5 * dist)
    g = int(8 * (1 - dist) + 2 * dist)
    b = int(35 * (1 - dist) + 10 * dist)
    draw.line([(0, y), (width, y)], fill=(r, g, b))

# Add stars
stars_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
stars_draw = ImageDraw.Draw(stars_layer)
for _ in range(200):
    x = random.randint(0, width - 1)
    y = random.randint(0, height - 1)
    size = random.randint(1, 3)
    alpha = random.randint(100, 255)
    stars_draw.ellipse([x, y, x+size, y+size], fill=(255, 255, 255, alpha))

# Composite
result = background.convert('RGBA')
result = Image.alpha_composite(result, stars_layer)
result = Image.alpha_composite(result, serpent)
```

## Golden Aura + Vignette

**Pattern:**
```python
# Radial gradient glow (centered on upper portion)
glow = Image.new('RGBA', (width, height), (0, 0, 0, 0))

for y in range(height):
    for x in range(width):
        dist = math.sqrt((x - center_x)**2 + (y - center_y)**2)
        if dist < max_radius:
            intensity = (1 - dist / max_radius) ** 2
            alpha = int(intensity * 40)
            glow_draw.point((x, y), fill=(255, 215, 0, alpha))

# Blur for softness
glow = glow.filter(ImageFilter.GaussianBlur(radius=30))

# Vignette (darken edges)
for y in range(height):
    for x in range(width):
        dx = (x - width/2) / (width/2)
        dy = (y - height/2) / (height/2)
        dist = math.sqrt(dx**2 + dy**2)
        if dist > 0.7:
            darken = min(200, int((dist - 0.7) * 400))
            vig_draw.point((x, y), fill=(0, 0, 0, darken))
```

## Circular Profile Pic Crop

**Pattern:**
```python
mask = Image.new('L', (width, height), 0)
mask_draw = ImageDraw.Draw(mask)
inset = int(width * 0.02)  # 2% inset
mask_draw.ellipse([inset, inset, width-inset, height-inset], fill=255)

circular = Image.new('RGBA', (width, height), (0, 0, 0, 0))
circular.paste(result, mask=mask)
```

## Color Enhancement

```python
from PIL import ImageEnhance

# Boost saturation slightly
enhancer = ImageEnhance.Color(image)
image = enhancer.enhance(1.1)

# Sharpen
image = image.filter(ImageFilter.SHARPEN)
```

## Performance Notes

- PIL is available via Python (no install needed)
- For large images, the glow loop can be slow (~30 seconds for 1024x1024)
- Blur radius 30 works well for soft glow
- Always save as PNG to preserve alpha/transparency
- Output goes to `/tmp/` for easy access

## Workflow

1. Render base serpent in Blender (use `--background --python <script.py>`)
2. Load rendered PNG with PIL
3. Apply background/effect layers
4. Composite together
5. Save to `/tmp/`
6. Share via MEDIA: paths or Discord upload (if bot token works)
