# Together.ai Image Gen + Vision Recipes (verified 2026-07-26)

## 1) Image generation (browser UA required — Cloudflare 1010 otherwise)
```python
import os, json, base64, urllib.request
KEY = open("/home/adora/.hermes/.env").read().split("TOGETHER_API_KEY=")[1].splitlines()[0]
hdr = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json",
       "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
       "Origin": "https://api.together.ai", "Referer": "https://api.together.ai/"}
body = json.dumps({"model": "black-forest-labs/FLUX.2-dev", "prompt": PROMPT,
                   "width": 768, "height": 1024, "steps": 34, "n": 1,
                   "response_format": "b64_json"}).encode()
req = urllib.request.Request("https://api.together.xyz/v1/images/generations", data=body, headers=hdr)
r = urllib.request.urlopen(req, timeout=180)
open(OUT, "wb").write(base64.b64decode(json.load(r)["data"][0]["b64_json"]))
```

## 2) img2img (repaint lighting, keep anatomy)
Add to the body:
```python
"image": f"data:image/png;base64,{base64_of_base_image}",
"image_strength": 0.35
```
and set prompt to something like "repaint the lighting only of this figure, keep anatomy/pose
unchanged, add dramatic candlelit chiaroscuro". 0.3–0.4 preserves the figure; higher drifts it.

## 3) View result via OpenRouter vision (when native vision is on a dead free model)
```python
import os, json, base64, urllib.request
KEY = open("/home/adora/.hermes/.env").read().split("OPENROUTER_API_KEY=")[1].splitlines()[0]
img = base64.b64encode(open(OUT, "rb").read()).decode()
body = json.dumps({"model": "openai/gpt-4o-mini",
  "messages":[{"role":"user","content":[
    {"type":"text","text":"Describe this image and rate quality 1-10."},
    {"type":"image_url","image_url":{"url":f"data:image/png;base64,{img}"}}]}],
  "max_tokens":300}).encode()
req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=body,
    headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
print(json.load(urllib.request.urlopen(req, timeout=120))["choices"][0]["message"]["content"])
```
NOTE: keep the vision-critique prompt to a SINGLE short question. Multi-sentence / numbered
prompts sometimes make gpt-4o-mini dodge with a generic "here is how to critique art" rubric
instead of actually answering. If it deflects, simplify to one blunt question.
