---
name: ocr-image
description: Extract text from images using Tesseract OCR. Use when the user sends a screenshot, photo of text, or asks to "tesseract" an image. Falls back to Discord image fetching if no local path provided.
tags: [ocr, tesseract, image, text-extraction]
---

# OCR Image Skill

## Prerequisites
- Tesseract OCR installed (`tesseract --version` to verify)
- For Discord images: ability to fetch via Discord bot API

## Usage

### Local image file
```bash
tesseract /path/to/image.png stdout
```

### Image from Discord (latest in channel)
1. Fetch the image URL from Discord API
2. Download to `/tmp/ocr_image.jpg`
3. Run `tesseract /tmp/ocr_image.jpg stdout`

### Tips
- Add language hints for better accuracy: `tesseract img.png stdout -l eng`
- For low-contrast screenshots, preprocess with ImageMagick:
  ```bash
  convert input.png -resize 200% -sharpen 0x1 /tmp/processed.png && tesseract /tmp/processed.png stdout
  ```
- For handwritten text, use `-l eng+script/Handwritten` (requires training data)

## Reading Cached Discord Images

When the user sends a screenshot via Discord, Hermes may not be able to see it directly (vision_analyze can fail with 401/auth errors, and `read_file` fails on binary files). The image is cached locally at:

```
~/.hermes/image_cache/img_<hash>.jpeg
```

**File extension quirk:** Cached files may have a `.webp` extension but actually contain PNG data. Tesseract handles both formats correctly regardless of extension. Verify with `file <path>` if tesseract complains.

**Direct tesseract approach (works without vision API):**
```bash
tesseract /home/adora/.hermes/image_cache/img_<hash>.jpeg stdout --psm 6 -l eng
```

This is the most reliable fallback when:
- `vision_analyze` returns 401 or API key errors
- `read_file` rejects binary files
- `browser_navigate` fails to render the image
- The model substrate lacks vision support (check model capabilities first)

This works for ALL Discord screenshots — not just text-heavy ones. Conversation screenshots, images with text overlays, screenshots of documents, etc.

**Tips for Discord screenshots:**
- Mobile screenshots are often tall (1440x3805+) — tesseract handles them fine
- Dark-theme screenshots may have low contrast; tesseract usually handles Discord's dark theme well
- If output is fragmentary, try `--psm 3` for fully automatic segmentation

## Handling Very Large Screenshots

Discord mobile screenshots can be extremely tall (e.g., 1440x32972px) or wide (e.g., 6560x2980px). Tesseract may struggle with these. Use Python/PIL to split into overlapping chunks:

```python
from PIL import Image

img = Image.open('/path/to/large_screenshot.jpg')
w, h = img.size
chunk_h = 1500
overlap = 200
y = 0
chunk_num = 0
while y < h:
    end = min(y + chunk_h, h)
    chunk = img.crop((0, y, w, end))
    chunk.save(f'/tmp/chunk_{chunk_num}.png')
    y += chunk_h - overlap
    chunk_num += 1
```

Then OCR each chunk separately. For very wide images (possible collage of multiple screenshots), also split vertically:

```python
col_w = w // 3  # Try splitting into 3 columns
for i in range(3):
    col = img.crop((i * col_w, 0, (i+1) * col_w, h))
    col.save(f'/tmp/col_{i}.png')
```

## Preprocessing for Better OCR

When tesseract output is garbled on dark-theme screenshots:

```python
from PIL import Image, ImageFilter, ImageEnhance

img = Image.open('/path/to/image.jpg')
img_gray = img.convert('L')
img_sharp = img_gray.filter(ImageFilter.SHARPEN)
img_contrast = ImageEnhance.Contrast(img_sharp).enhance(2.0)
img_contrast.save('/tmp/processed.png')
```

Then run tesseract on the processed image.

## Fallback Chain for Image Reading

When you need to read a Discord image and vision isn't available:

1. **Try tesseract directly** on the cached file with `--psm 6`
2. **If output is poor**, try `--psm 3` (automatic segmentation)
3. **If still poor**, preprocess (grayscale → sharpen → contrast) then retry
4. **If image is very large**, split into chunks first, then OCR each chunk
5. **If all OCR fails**, ask the user to paste the text or describe the image

## Error handling
- If output is garbled, try `--psm 6` (uniform block) or `--psm 3` (fully automatic)
- For tables/structured data, use `--psm 6` with `tsv` output: `tesseract img.png stdout --psm 6 tsv`
- If tesseract returns empty output, verify the image exists: `file <path>` should show "JPEG image data"
