# LoRA-Based Consistent Character Generation

## Overview
To generate consistent images of the same character (e.g., Narusya's humanoid form) across multiple prompts, use a **LoRA (Low-Rank Adaptation)** — a small trained model that nudges the base model's output toward a specific style or character.

## The Pipeline (Conceptual)

```
Generate 10-20 images of the character
  → Train a LoRA on those images (Replicate/CivitAI)
    → Upload LoRA to HuggingFace
      → Generate with Together.ai FLUX.1-dev-lora + image_loras parameter
```

## Step 1: Generate Reference Images
Use the Perchance pipeline (if working) or Together.ai to create images from different angles with consistent prompting. Each image should show the same character features.

## Step 2: Train the LoRA
Two practical options:

### Option A: Replicate
- Service: `ostris/flux-dev-lora-trainer` (most popular)
- Cost: ~$1-2 per training run
- Input: 10-20 images (zip file)
- Output: LoRA file download

### Option B: CivitAI
- Has built-in LoRA training
- Can host and share LoRAs on the platform

## Step 3: Host on HuggingFace
Upload the trained LoRA `.safetensors` file to HuggingFace for URL-based access.

## Step 4: Generate with Together.ai
```python
from together import Together
client = Together(api_key="tgp_v1_...")

image = client.images.generate(
    prompt="narusya style, a portrait in the rain, cinematic",
    model="black-forest-labs/FLUX.1-dev-lora",
    height=768,
    width=768,
    steps=30,
    image_loras=[{
        "path": "https://huggingface.co/your-org/your-lora",
        "scale": 1,  # 0-1, controls LoRA strength
    }],
)
print(image.data[0].url)
```

## Key Details
- **Trigger word** — The LoRA has a "trigger word" trained into it. Include this word in every prompt for the LoRA to activate.
- **Scale** — Controls how strongly the LoRA influences the output. Start at 1.0 and adjust down if it's too strong.
- **Base model** — LoRAs are trained for a specific base model (e.g., FLUX.1-dev). Use the matching model for inference.
- **Resolution** — Higher resolutions (768×768, 1024×1024) give better results with flux LoRAs.

## Together.ai Models for LoRA
| Model | LoRA Support | NSFW | Notes |
|-------|-------------|------|-------|
| `black-forest-labs/FLUX.1-dev-lora` | ✅ Full | ✅ Yes | Best for LoRA inference |
| `black-forest-labs/FLUX.2-dev` | ❌ No | ✅ Yes | Better quality but no LoRA |
| `black-forest-labs/FLUX.1.1-pro` | ❌ No | ❌ Blocks | Has prompt pre-screen |

## Hardware Note
No local GPU is needed — both Together.ai and Replicate run entirely on cloud GPUs. The Hermes VM only needs network access.

## Status
- LoRA training: Not yet attempted (waiting for Adora's direction)
- Together.ai LoRA injection: Confirmed working via API (tested: `black-forest-labs/FLUX.2-dev` accepts `image_loras` parameter)
- Cost to train: ~$1-2 via Replicate
- Cost per generation: ~$0.0001