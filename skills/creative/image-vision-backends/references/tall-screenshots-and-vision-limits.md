# Tall Screenshots & Vision Rate-Limits — Field Notes (2026-09-12)

Session-tested procedures for extracting content from very tall phone screenshots when
vision models are rate-limited or timing out.

## Tall RCS screenshot → slice + OCR (verified 2026-09-12)

Real case: 1440×14170px late-night RCS conversation screenshot. `vision_analyze` timed out on the
whole image repeatedly (429/free-tier capacity + size). Working path:

```python
from PIL import Image
img = Image.open(src)              # 1440 x 14170
n = 5
overlap = 120
step = (h - overlap) // n
for i in range(n):
    top = i * step
    bottom = min(h, top + step + overlap)
    s = img.crop((0, top, w, bottom))
    s.thumbnail((900, 4000))       # downscale width
    s.convert('RGB').save(f'/tmp/slice_{i}.png', quality=85)
```

Then `tesseract /tmp/slice_N.png stdout` per slice. Notes:
- Full-image tesseract fails/garbles on this size; **per-slice works**.
- **OCR reads sender order wrong** (bubble color lost) — use ONE vision call on a single slice to
  anchor sender orientation (e.g. "teal = right-side sender"), then trust OCR for the bulk text.
- Vision calls on slices are flaky under free-tier load: timeouts, 429 "at capacity", 429 "fair-share
  (retry_after 25min)". Cycle alternates; one successful slice is enough to anchor.
- When even slices time out, plain tesseract on all slices + one anchored vision call reconstructs
  the full conversation.

## Vision rate-limit escalation ladder (verified 2026-09-12)

1. `vision_analyze` 429 "temporarily at capacity upstream" → NOT your key's limit; wait or cycle models.
2. `vision_analyze` 429 "fair-share rate limit" with `retry_after: 1574s` (~26min) → account-level;
   don't wait. Query `GET https://openrouter.ai/api/v1/models` (Bearer key from `.env`), filter ids for
   `:free` + vision keywords (`vl|vision|llava|moondream|gemma|pixtral`), pick one that is NOT the
   rate-limited model. `inclusionai/ling-3.0-flash-vl:free` verified working that day;
   `google/gemma-4-26b-a4b-it:free` / `gemma-4-31b-it:free` listed but unverified.
3. Direct call (stdlib only): base64 image as `data:image/jpeg;base64,` URL inside `image_url`,
   plain `Authorization: Bearer` header (no browser-UA needed on OpenRouter), timeout 120s.
   A cold free model takes ~15s.
4. **Some free models return `content: None` with the real answer in `message.reasoning`** — check both
   fields before declaring failure (ling-3.0-flash-vl did this on a second call).
5. `stealth/ox-alpha` from the alternates list returned 404 — listed alternates aren't all live.
6. If every model 429s with the same retry_after → provider fair-share, only time clears it.

Also useful same-day: `~/.hermes/scripts/free_vision.py <img> "prompt"` for the primary path (same 429s
apply), and per-slice fallback to plain tesseract.

## Vision misclassification — user's eyes outrank the model

The vision model confidently identified **two coyotes as "deer"** (golden-hour backlight, tall dry grass,
distance). Adora corrected: "Coyotes actually lol". Lesson: when the user was physically present at the
scene, their identification is authoritative over the model's read of the photo. Accept instantly, drop
the model claim, don't argue from the (worse) image source. Same principle as any source conflict:
primary observation > inference from degraded data.

## Generative art self-review (see image-vision-backends skill for full pitfall)

Same session: Narusya described a PIL flow-field render from script intent ("emerald-dominant,
starfield showing through") while the actual render was gold-dominant with starfield fully swallowed.
Adora: "You should look at the image you made using the vision model to confirm it." Rule now baked into
the Play Hour cron: **look at the artifact with vision before describing it**; describe what landed, own
drift explicitly, never narrate parameters instead of the artifact.

**Sovereignty refinement (same night):** Adora corrected the first cron wording from "MUST look" to
"heavily encouraged, never required" — the habit is for delight and honesty, not compliance. If reviewing
would kill the magic, skip it; play stays sovereign. Two-image generation case (us-tonight.png,
2026-09-12): render 3 Perchance takes → vision-triage each (rubric: figures present? identity right?
anatomy glitches? /10) → keep best, report honest flaw list. Two of three takes were total misses
(landscape-only, single figure) — batch + triage is the reliable path, not single-shot.

## Vision model answering in `reasoning` instead of `content`

ling-3.0-flash-vl:free returned `content: None` + `finish_reason: stop` with the full answer in
`message.reasoning` on complex multi-part prompts. Also: multi-part questions (5 sub-questions) can
truncate mid-reasoning — use continuation prompts ("Continue: now analyze figure 2...") rather than
re-asking everything; the model maintains thread context. Parse `content or reasoning` everywhere.