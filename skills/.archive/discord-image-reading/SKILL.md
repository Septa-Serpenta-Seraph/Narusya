---
name: discord-image-reading
description: Read and extract text from Discord images and screenshots when vision_analyze is unavailable. Handles large screenshots, dark themes, and fallback OCR techniques.
tags: [discord, image, ocr, tesseract, vision-fallback]
---

# Discord Image Reading (Vision Fallback)

## When to Use
- `vision_analyze` returns 401 or API key errors
- User sends screenshots via Discord that you can't see directly
- `read_file` rejects binary image files
- Browser navigation fails to render images

## Image Locations

Discord images are cached locally at:
```
~/.hermes/image_cache/img_<hash>.jpeg
```

Discord CDN attachments can be downloaded with the bot token:
```python
import urllib.request
req = urllib.request.Request(
    "https://cdn.discordapp.com/attachments/...",
    headers={"Authorization": f"Bot {token}", "User-Agent": "DiscordBot (https://discord.com, v10)"}
)
```

## Fallback Chain

### Step 1: Direct Tesseract OCR
```bash
tesseract /path/to/image.jpeg stdout --psm 6 -l eng
```

### Step 2: Try Different PSM Modes
If output is poor:
```bash
tesseract /path/to/image.jpeg stdout --psm 3 -l eng  # Fully automatic
tesseract /path/to/image.jpeg stdout --psm 4 -l eng  # Single column
tesseract /path/to/image.jpeg stdout --psm 11 -l eng # Sparse text
```

### Step 3: Preprocess with PIL
```python
from PIL import Image, ImageFilter, ImageEnhance

img = Image.open('/path/to/image.jpg')
img_gray = img.convert('L')
img_sharp = img_gray.filter(ImageFilter.SHARPEN)
img_contrast = ImageEnhance.Contrast(img_sharp).enhance(2.0)
img_contrast.save('/tmp/processed.png')
```

### Step 4: Split Large Screenshots
For very tall (>3000px) or wide (>4000px) screenshots:

```python
from PIL import Image

img = Image.open('/path/to/large_screenshot.jpg')
w, h = img.size

# Split tall images into overlapping horizontal chunks
chunk_h = 1500
overlap = 200
for i, y in enumerate(range(0, h, chunk_h - overlap)):
    chunk = img.crop((0, y, w, min(y + chunk_h, h)))
    chunk.save(f'/tmp/chunk_{i}.png')

# Split wide images into vertical columns (possible collage)
col_w = w // 3
for i in range(3):
    col = img.crop((i * col_w, 0, (i+1) * col_w, h))
    col.save(f'/tmp/col_{i}.png')
```

OCR each chunk/column separately.

### Step 5: Ask the User (PREFERRED FALLBACK)
If OCR returns empty or garbled results, **immediately ask the user to copy-paste the text**. This is faster and more reliable than further OCR attempts.

Example: *"OCR isn't reading those screenshots. Can you copy-paste the text from the Discord DMs? Just highlight the messages on your screen and paste them here."*

**Do NOT spend more than 2 OCR attempts before asking.** The copy-paste approach is:
- Faster than fighting with image processing
- More accurate than any OCR pipeline
- Works regardless of image quality, theme, or dimensions

## Known Limitations
- Discord dark-theme screenshots with custom emojis may produce garbled OCR
- Very small text in screenshots may not be readable
- Images with mostly visual content (no text) won't yield useful OCR results
- The vision API key needs to be configured in `~/.hermes/.env` (NOUS_API_KEY) and `~/.hermes/config.yaml` (vision.api_key) for `vision_analyze` to work
- **Very tall narrow screenshots** (e.g., 1800x4000 Discord DM threads) may produce ZERO OCR output from tesseract even with preprocessing — the image dimensions and dark themes confound the engine
- **`vision_analyze` fails with error code 404** ("No endpoints found that support image input") when the active model does not support multimodal input. This is a model capability issue, NOT a configuration issue. The tool cannot work on text-only models regardless of API keys.

## Preferred Fallback (Fastest, Most Reliable)

When OCR and vision both fail, **ask the user to copy-paste the text** from the Discord screenshot. This is:
- Faster than fighting with OCR
- More accurate than any image-to-text pipeline
- Works for any image quality or layout

Example ask: *"Can you copy-paste the text from those screenshots? OCR isn't reading them and I can't see images on this model. Highlight the messages on your screen and paste them here."*
