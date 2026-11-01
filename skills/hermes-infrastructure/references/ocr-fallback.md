# Image Analysis Fallback: Tesseract OCR and OpenRouter Vision

## When vision_analyze Fails

If `vision_analyze` returns error "No endpoints found that support image input" (HTTP 404), the active model doesn't support vision. Two fallback options:

### Option 1: OpenRouter Vision Models (preferred for screenshots with text)

The local vision model (qwen3-vl-4b via LM Studio) is limited and often returns empty or garbled results. OpenRouter has free vision models that work better:

```python
import base64, json, urllib.request

# Resize to reduce payload
from PIL import Image
img = Image.open(img_path)
img.thumbnail((1024, 1024))
resized = '/tmp/resized_img.jpg'
img.save(resized, 'JPEG', quality=80)

with open(resized, 'rb') as f:
    b64 = base64.b64encode(f.read()).decode()

api_key = open('/home/adora/.hermes/.env').read().split('OPENROUTER_API_KEY=')[1].split('\n')[0].strip()

payload = {
    'model': 'nvidia/nemotron-3.5-super-vl:free',
    'messages': [{'role': 'user', 'content': [
        {'type': 'text', 'text': 'Describe this image in detail. What text is visible?'},
        {'type': 'image_url', 'image_url': {'url': 'data:image/jpeg;base64,' + b64}}
    ]}],
    'max_tokens': 2000
}

req = urllib.request.Request('https://openrouter.ai/api/v1/chat/completions',
    data=json.dumps(payload).encode(),
    headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + api_key})
resp = urllib.request.urlopen(req, timeout=60)
data = json.loads(resp.read())
# Content may be in 'content' or 'reasoning' field
content = data['choices'][0]['message'].get('content') or data['choices'][0]['message'].get('reasoning', '')
print(content)
```

**Note:** The nemotron model sometimes puts its analysis in the `reasoning` field with `content` as null. Check both.

### Option 2: Tesseract OCR (for text-heavy screenshots)

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
2. Try OpenRouter vision model first (better accuracy for screenshots)
3. Fall back to Tesseract OCR if OpenRouter is unavailable
4. Parse output and respond to user

## Note on Discord Images

Discord images sent via DM are cached locally at `~/.hermes/image_cache/`. The local path is usually included in the tool error message or can be found with:
```bash
ls -lt ~/.hermes/image_cache/ | head -5
```
