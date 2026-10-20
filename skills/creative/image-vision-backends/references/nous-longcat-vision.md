# Nous longcat-2.5-preview — vision via the Nous API

Free multimodal path when the built-in `vision_analyze` tool is out of OpenRouter credits (402).

## Auth

The Nous API key is NOT `NOUS_API_KEY` in `.env` (that returns 401). Read it from `~/.hermes/auth.json`:

```python
p = json.load(open('/home/adora/.hermes/auth.json'))['providers']['nous']
key  = p.get('agent_key') or p.get('access_token')   # JWT, ~2029 chars
base = p['inference_base_url']                       # https://inference-api.nousresearch.com/v1
```

Tokens are short-lived (~1h). If a call 401s, refresh via the portal flow rather than editing `.env`.

## Calling it

```python
body = {'model': 'meituan/longcat-2.5-preview:free', 'max_tokens': 6000,
        'messages': [{'role': 'user', 'content': [
            {'type': 'text', 'text': '<prompt>'},
            {'type': 'image_url', 'image_url': {'url': 'data:image/jpeg;base64,' + b64}}]}]}
```

POST to `<base>/chat/completions` with `Authorization: Bearer <key>`.

## Pitfalls

- **It is a reasoning model.** Output arrives as `choices[0].message.reasoning_content`; the final answer goes in `message.content`. With a low `max_tokens` the model burns the entire budget reasoning and `content` is missing entirely (`finish_reason: "length"`, `content` key absent).
  - Set `max_tokens` >= 6000 for vision tasks — and know that 6000 is **still not always enough**. A dense-text image (retail shelf, price tags) can exhaust even that on reasoning alone and return no `content` key at all. If a second call with a bigger budget also comes back empty, the model is stuck in a reasoning loop on that image: stop raising the cap and switch to OCR (tesseract) or another model.
  - Always read `content` and fall back to the tail of `reasoning_content`.
  - Still give it a tight instruction ("just the final list, no reasoning") — it ignores that often, so keep the budget generous anyway.
- **Payload size limit:** the API rejects images over 5,242,880 px (`Image total pixels exceeds maximum allowed size`). Resize first:
  ```python
  from PIL import Image
  im = Image.open(src); w, h = im.size; s = (5_000_000/(w*h))**0.5
  im.resize((int(w*s), int(h*s)), Image.LANCZOS).save(dst, quality=92)
  ```
  Phone screenshots (e.g. 1864x4096) exceed this; shelf photos usually do too.
- **Small text (price tags, labels) is unreliable.** On a dense retail shelf it guesses at partially-occluded tags and can loop on a single ambiguous word for thousands of tokens. Treat brand/price reads as leads to confirm, not facts — OCR (tesseract) is more trustworthy for tags and labels.
- Roughly 10 s per image, no cost.
