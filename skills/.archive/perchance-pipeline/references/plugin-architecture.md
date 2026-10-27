# Perchance Plugin Architecture (Reverse-Engineered)

## Text-to-Image Plugin

The generator at `perchance.org/ai-text-to-image-generator` uses `t2i-framework-plugin-v2` which imports the `text-to-image-plugin`.

### Plugin Source (2026-07-31)

The `text-to-image-plugin` documentation page (`perchance.org/text-to-image-plugin`) reveals:

#### Import Syntax
```
image = {import:text-to-image-plugin}
```

#### Template Usage
```
promptData
  prompt = painting of [character] in [place], [season]
  seed = 123
  size = 400  // square resolution only
  style = border:4px solid blue; margin-top:20px; // CSS styles
  resolution = 512x768  // or 768x768, 512x512, 768x512
  negativePrompt = blur, blurry image
  guidanceScale = 7  // 1-30, default 7
output
  [image(promptData)]
```

#### JavaScript API
```javascript
async start() => {
  // Returns String object with extra properties
  let result = await image({prompt:"a cute mouse"});
  imageEl.src = result.dataUrl;
  // result.canvas — HTML5 Canvas
  // result.dataUrl — base64 data URL
  // result.inputs.prompt — the prompt used
  // result.inputs.negativePrompt
  // result.inputs.seed
  // result.inputs.guidanceScale
}

// Simplified version
imageEl.src = await image("a cute mouse");

// With options
imageEl.src = await image("a cute mouse", {resolution: "512x768", removeBackground: true});
```

#### iframe Output Access
```javascript
iframe.textToImagePluginOutput.canvas
iframe.textToImagePluginOutput.dataUrl
iframe.textToImagePluginOutput.inputs.prompt
iframe.textToImagePluginOutput.inputs.negativePrompt
iframe.textToImagePluginOutput.inputs.seed
```

### Key Internal Objects (Found on generator page via Chromium)
When the iframe subdomain loaded successfully, the main frame's `window` object contained:
- `t2i` — main plugin object with methods like `generateImage`, `createLoadingModal`, etc.
- `___textToImagePlugin746291937` — internal plugin function
- `___getImageOptions746291937` — option builder
- `t2i_privateGallery`, `t2i_privateGallerySave` — gallery management
- `t2i_openCharacterDescriptionEditor`, `t2i_generateCharacterDescription`
- `t2i_generateChatLink`, `t2i_generateShareLinkForCharacter`
- `t2i_createLoadingModal`
- `generateImageGalleryHtml358402048` — gallery HTML generator

**Critical:** These objects only appear when the `image-generation.perchance.org` iframe subdomain has successfully loaded. They are NOT available when the iframe is Turnstile-blocked.

### Embed Page (`image-generation.perchance.org/embed`)

A lightweight wrapper that loads the generator in an iframe-less context. Uses URL hash for configuration:

```javascript
// The regenerateImage function shows the pattern
function regenerateImage() {
  document.body.style.opacity = 0;
  window.urlHashData.requestId = Math.random().toString();
  window.history.replaceState(null, "", "#"+encodeURIComponent(JSON.stringify(window.urlHashData)));
  window.location.reload();
}
```

The embed page has these global functions when loaded:
- `regenerateImage()` — reloads with new requestId
- `flagImage()` — flags generated image
- `saveImageToGallery()` — saves to public gallery
- `saveImageToComputer()` — downloads

### Auth Flow Changes

- Previously: Clicking "✨ generate" triggered a `verifyUser?thread=0` GET, which returned a page containing the `userKey` (64-char hex), followed by `generate?userKey=KEY`
- Current (broken): `verifyUser?thread=0` returns `{"status":"failed_verification","reason":"token_required"}` — now requires a bearer `token` parameter
- The old `userKey` appears to be an account-level identifier stored in the user's Perchance localStorage, assigned on first visit and persistent across sessions for the same IP/browser
- The new `token` appears to be a session-level Turnstile validation token, short-lived and tied to specific browser context

### Resolution Options
- Square: 768×768, 512×512
- Portrait: 512×768
- Landscape: 768×512

### Guidance Scale
- Default: 7
- Range: 1–30
- Higher = closer prompt adherence, less realism

### NSFW Policy
From the plugin docs: *"The model can return NSFW/adult-themed results if prompted with NSFW/adult-themed terms."* The plugin explicitly advises using "NSFW" and "nudity" as negative prompts to *reduce* unwanted NSFW content — confirming the model can and does produce it.

### Cost & Limitations
- Server GPU-funded — ads appear for non-logged-in users
- "Each user can only have a few concurrent server requests"
- Backend model may change when new models are released (old seeds produce different results after upgrades)