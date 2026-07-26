# Image Analysis Fallback: Tesseract OCR

## When vision_analyze Fails

If `vision_analyze` returns error "No endpoints found that support image input" (HTTP 404), the active model doesn't support vision. Fall back to Tesseract OCR for local image files.

## Prerequisites

```bash
# Verify tesseract is installed (usually pre-installed on this VM)
which tesseract
# If missing: sudo apt install tesseract-ocr
```

## Usage

```bash
# Basic OCR on a local image file
tesseract /path/to/image.jpeg stdout 2>/dev/null

# For better accuracy on screenshots with mixed fonts
tesseract /path/to/image.jpeg stdout --psm 6 2>/dev/null
```

## When This Works

- ✅ Local image files (JPEG, PNG, etc.) at known paths
- ✅ Screenshots containing text (Discord chats, documents, code)
- ✅ Images cached locally at `~/.hermes/image_cache/`

## When This Doesn't Work

- ❌ Discord CDN URLs (require authentication, return "content no longer available")
- ❌ Purely visual content (photos, art, diagrams without text)
- ❌ Very low-resolution or heavily compressed images

## Workflow

1. User sends image → `vision_analyze` fails with 404
2. Check if image is at a local path (e.g., `~/.hermes/image_cache/img_*.jpeg`)
3. Run `tesseract <path> stdout 2>/dev/null`
4. Parse OCR output and respond to user

## Note on Discord Images

Discord images sent via DM are cached locally at `~/.hermes/image_cache/`. The local path is usually included in the tool error message or can be found with:
```bash
ls -lt ~/.hermes/image_cache/ | head -5
```
