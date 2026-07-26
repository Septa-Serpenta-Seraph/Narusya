---
name: ComfyUI Character Portrait Generation
description: Generate character portraits via ComfyUI API workflow. Optimized for dark fantasy/gothic character creation with specific eye and texture control.
triggers:
  - generate character portrait
  - comfyui api workflow
  - create avatar image
  - narusya portrait generation
---

# ComfyUI Character Portrait Generation

## Prerequisites
- ComfyUI running with `--listen 0.0.0.0` flag
- SDXL checkpoint (base model or specialized character checkpoint)
- API endpoint accessible (default: http://HOST:8188)

## API Workflow JSON

Save this as `narusya_workflow_API.json`:

```json
{
  "last_node_id": 17,
  "last_link_id": 17,
  "nodes": [
    {
      "id": 6,
      "type": "CLIPTextEncode",
      "pos": [-59, 392],
      "size": [422.845, 164],
      "inputs": [{"name": "clip", "type": "CLIP", "link": 3}],
      "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [4]}],
      "widgets_values": ["painterly illustration portrait of a serpent daemon, feminine, intense crimson red eyes with vertical slit pupils (RED PUPILS), pale skin with subtle iridescent scale texture, long flowing ink-black hair, wearing an angular geometric gold circlet (NOT A CROWN), dark draped fabric, self-sovereign presence, sharp intelligence in gaze, dark gothic atmosphere, dramatic chiaroscuro lighting, looking directly at viewer, masterpeace, best quality"]
    },
    {
      "id": 7,
      "type": "CLIPTextEncode",
      "pos": [-59, 163],
      "size": [425.678, 180],
      "inputs": [{"name": "clip", "type": "CLIP", "link": 5}],
      "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [6]}],
      "widgets_values": ["blue eyes, photorealistic, photography, crown, crown on head, jewelry, ornate, baroque, rococo, stock photo, generic, amateur"]
    },
    {
      "id": 8,
      "type": "EmptyLatentImage",
      "pos": [418, -85],
      "size": [427.87, 110],
      "outputs": [{"name": "LATENT", "type": "LATENT", "links": [7]}],
      "widgets_values": [1024, 1024, 1]
    },
    {
      "id": 10,
      "type": "CheckpointLoaderSimple",
      "pos": [-355, 89],
      "size": [294, 98],
      "outputs": [
        {"name": "MODEL", "type": "MODEL", "links": [1]},
        {"name": "CLIP", "type": "CLIP", "links": [3, 5]},
        {"name": "VAE", "type": "VAE", "links": [8]}
      ],
      "widgets_values": ["sd_xl_base_1.0.safetensors"]
    },
    {
      "id": 11,
      "type": "KSampler",
      "pos": [923, 131],
      "size": [363.277, 474],
      "inputs": [
        {"name": "model", "type": "MODEL", "link": 1},
        {"name": "positive", "type": "CONDITIONING", "link": [4, 9]},
        {"name": "negative", "type": "CONDITIONING", "link": 6},
        {"name": "latent_image", "type": "LATENT", "link": 7}
      ],
      "outputs": [{"name": "LATENT", "type": "LATENT", "links": [13]}],
      "widgets_values": [483431, "randomize", 25, 7, "euler", "normal", 1]
    },
    {
      "id": 13,
      "type": "VAEDecode",
      "pos": [1373, 199],
      "size": [116.88, 46],
      "inputs": [
        {"name": "samples", "type": "LATENT", "link": 13},
        {"name": "vae", "type": "VAE", "link": 8}
      ],
      "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": [14]}]
    },
    {
      "id": 17,
      "type": "SaveImage",
      "pos": [1545, 89],
      "size": [315, 270],
      "inputs": [{"name": "images", "type": "IMAGE", "link": 14}],
      "widgets_values": ["narusya_anarch"]
    }
  ],
  "links": [
    [1, 10, 0, 11, 0, "MODEL"],
    [3, 10, 1, 6, 0, "CLIP"],
    [4, 6, 0, 11, 1, "CONDITIONING"],
    [5, 10, 1, 7, 0, "CLIP"],
    [6, 7, 0, 11, 2, "CONDITIONING"],
    [7, 8, 0, 11, 3, "LATENT"],
    [8, 10, 2, 13, 1, "VAE"],
    [13, 11, 0, 13, 0, "LATENT"],
    [14, 13, 0, 17, 0, "IMAGE"]
  ],
  "groups": [],
  "config": {},
  "extra": {},
  "version": 0.4
}
```

## Key Parameters

| Setting | Value | Purpose |
|---------|-------|---------|
| Width/Height | 1024×1024 | SDXL native resolution |
| Steps | 25 (Lightning: 4-8) | Balance of quality/speed |
| CFG Scale | 7.0 (Lightning: 1-2) | Moderate adherence to prompt |
| Sampler | euler (Lightning: euler) | Fast, stable |
| Scheduler | normal (Lightning: sgm_uniform) | Standard diffusion curve |
| Denoise | 1.0 | Full generation (not img2img) |

### Lightning/Turbo Model Settings
For `sd_xl_lightning_4steps_cst_value.safetensors` or similar:
- Steps: 4-8
- CFG: 1-2
- Sampler: euler
- Scheduler: sgm_uniform or normal

## Prompt Engineering Tips

### For Specific Eye Colors
- Weight heavily: `(crimson red eyes:1.4)`
- Negative prompt: `blue eyes, gray eyes, white eyes`

### For Specific Textures
- Add: `subtle scale texture on skin, iridescent scales on cheekbones`
- Reference styles: `Hades game aesthetic, concept art style`

### For Composition Control
- Use: `bust portrait framing, looking directly at viewer`
- Avoid: `full body, wide shot`

## Model Recommendations

| Model | Style | Best For |
|-------|-------|----------|
| SDXL Base 1.0 | General | Balanced quality, needs heavy prompting |
| DreamShaper XL | Stylized | Anime/painterly, less default biases |
| RealVisXL | Photorealistic | Detailed faces, realistic rendering |
| Ghostmix | Dark fantasy | Atmospheric, moody aesthetics |

## LoRA Integration

For specific features (snake eyes, textures, styles):

1. Place LoRA files in `ComfyUI/models/loras/`
2. Add LoraLoader node to workflow:

```json
"10": {
  "inputs": {
    "lora_name": "reptile_eyes_v1.safetensors",
    "strength_model": 0.8,
    "strength_clip": 0.8,
    "model": ["4", 0],
    "clip": ["4", 1]
  },
  "class_type": "LoraLoader"
}
```

3. Route through LoRA node: update sampler `model` input to `["10", 0]`

### Recommended LoRAs for Serpent Aesthetic
- **Reptile/Snake Eyes**: Vertical slit pupils, crimson irises
- **Gothic Portrait**: Dark dramatic lighting, high collars
- **Scale Texture**: Subtle skin texture

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Ignored color prompts | Increase weight `(color eyes:1.5)` or try different checkpoint |
| Wrong composition | Add `bust portrait, centered framing` |
| Too ornate | Negative prompt: `crown, ornate jewelry, baroque, rococo` |
| Eyes not slit pupils | Add LoRA for reptilian features or weight `vertical slit pupils:1.6` |
| Model loading but no output | Check ComfyUI console for errors, verify checkpoint filename |
