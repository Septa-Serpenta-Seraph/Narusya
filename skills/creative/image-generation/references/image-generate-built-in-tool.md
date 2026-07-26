# Built-in `image_generate` Tool (FAL.ai via Nous Subscription)

The `image_generate` tool is a Hermes built-in (not ComfyUI). It routes through FAL.ai, managed by the Nous subscription. Active model: FLUX 2 Klein 9B.

## What Works
- **Text-to-image** — pass `prompt` only. Generates from text description.
- **Aspect ratios** — `landscape` (16:9), `portrait` (16:9 tall), `square` (1:1)
- Results are hosted on `v3b.fal.media` and can be analyzed with `vision_analyze`

## What Does NOT Work (Nous Subscription Limitations)
- **Image-to-image / editing** — passing `image_url` routes to `fal-ai/flux-2/klein/9b/edit`, which returns 403: "This model may not yet be enabled on the Nous Portal's FAL proxy"
- **Reference images** — `reference_image_urls` also routes to the edit model and gets the same 403
- **Fixing it** — would need a direct `FAL_KEY` env var (bypasses Nous proxy) or enabling the edit model on the Nous Portal

## FLUX Behavioral Patterns (Empirically Observed)

### People Rendering Bias
FLUX has a **strong default toward cheerful/wholesome character rendering**. Even with aggressive negative prompting:
- "NOT cute", "NOT cheerful", "NOT a teenager", "feral", "dark circles under eyes", "hard smirk"
- Result: still produces a broadly smiling, youthful, happy character

This is a model-level bias, not a prompting failure. Strategies that help (but don't fully solve):
- Use "woman in her late twenties" not "young woman" (avoids teenager rendering)
- Describe specific clothing textures and colors rather than vague "engineer outfit"
- Use "tight smirk" not "grin" — though FLUX may still render a full smile
- Paint a scene reference (Moebius, Blade Runner, heavy metal album cover) to shift art style away from Ghibli/default anime
- Accept that FLUX will tend toward wholesome — work WITH it rather than against it when possible

### Iterative Improvement Pattern
When the first generation doesn't land:
1. `vision_analyze` the output to get an objective description of what was actually rendered
2. Identify specific mismatches (wrong age, wrong expression, wrong art style)
3. Adjust the prompt with more specific/concrete language
4. Regenerate
5. Repeat — diminishing returns after ~4 attempts

### Using Discord PFPs as Appearance Reference
When trying to render a real person you can't use `reference_image_urls`:
1. Fetch their Discord avatar URL via the API (see discord-curl-api skill)
2. `vision_analyze` the avatar to extract appearance details (hair color, face shape, skin tone, eye color, clothing)
3. Feed those specific details into the text prompt
4. This gets you closer to the real person's appearance than pure imagination, but FLUX will still interpret freely

### When to Stop Iterating
- After 3-4 attempts, the model's biases are the limiting factor, not the prompt
- At that point, either accept the best result or suggest the user provide a selfie for a different generation approach (e.g., ComfyUI with ControlNet)
