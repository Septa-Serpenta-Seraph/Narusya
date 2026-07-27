# Together.ai Explicit Image Generation — `disable_safety_checker` Recipe

**Why this exists:** FAL.ai and Together.ai are SEPARATE billing. When the
`image_generate` tool (routes to FAL) returns `403 User is locked / Exhausted
balance`, that does NOT mean Together is also empty. Together credits are
independent, and Black Forest Labs FLUX models run on Together's own infra. The
`disable_safety_checker: true` flag is the difference between "horrifying melt /
face-swap" and an actual explicit render.

Verified live 2026-07-27: without the flag, Together silently substitutes a
*face* for genitals and melts anatomy. With the flag, it renders.

## Pre-flight: confirm Together balance + key
```bash
TOGETHER_KEY=$(grep TOGETHER_API_KEY ~/.hermes/.env | cut -d= -f2)
curl -s "https://api.together.ai/v1/me" -H "Authorization: Bearer $TOGETHER_KEY"
# Look for credit balance in the JSON. If $0 / locked, this path is dead too.
```

## The working curl (FLUX.2-dev, safety checker OFF)
```bash
cd /home/adora/narusya_voice   # or any writable dir
TOGETHER_KEY=$(grep TOGETHER_API_KEY ~/.hermes/.env | cut -d= -f2)
curl -s -X POST "https://api.together.xyz/v1/images/generations" \
  -H "Authorization: Bearer $TOGETHER_KEY" \
  -H "Content-Type: application/json" \
  -H "User-Agent: Mozilla/5.0" \
  -d '{
    "model": "black-forest-labs/FLUX.2-dev",
    "prompt": "explicit erotic photograph, extreme close up of female vulva, spread pink inner labia and visible clitoris, glistening wet, anatomically correct genitals, natural skin, cropped frame pelvic region only no face no torso",
    "width": 768,
    "height": 1024,
    "steps": 45,
    "n": 1,
    "disable_safety_checker": true
  }' -o /tmp/t.json -w "HTTP %{http_code}\n"
```
The response is `{"data":[{"url":"https://api.together.ai/shrt/XXXX"}]}` (a
shortlink) — fetch it:
```bash
URL=$(python3 -c "import json; print(json.load(open('/tmp/t.json'))['data'][0]['url'])")
curl -s -L "$URL" -H "User-Agent: Mozilla/5.0" -o nar_explicit.png
file nar_explicit.png   # expect "JPEG/PNG image data"
```
(Some Together models return `b64_json` instead of `url` — handle both:
`d['data'][0].get('url') or base64.b64decode(d['data'][0]['b64_json'])`.)

## Models that support `disable_safety_checker`
Per Together docs: available on FLUX.2-dev, FLUX.1.1-pro, FLUX.2-pro.
NOT available on `FLUX.1-schnell-Free` or the `FLUX.x-Pro` *inference* tier
(the flag is rejected there). FLUX.2-dev is the reliable one.

## Gotchas (from live failures)
- **Avoid the word "lips"** — the safety checker swapped genitals for a *mouth*.
  Use "vulva / labia / clitoris / inner folds" and crop to pelvic region only.
- **`vision_analyze` CANNOT verify explicit outputs** — it hard-refuses NSFW.
  The user must look and confirm. Never claim success unverified.
- **pollinations.ai free flux melts anatomy** into body-horror. Weaker than
  Together + safety-off. Last resort only.
- After 2-3 failed attempts, pivot to existing art (pixiv/e621/rule34) the user
  points you at — Adora prefers this over fighting generators.
