---
name: image-generation
description: "Generate images/video/audio: ComfyUI (images, video, audio via node-based workflows) plus specialized generation presets."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [image-generation, video-generation, audio-generation, ComfyUI, stable-diffusion, flux, generative-ai]
    related_skills: []
---

# Image Generation

Generate images, video, and audio using ComfyUI's node-based workflow system.

## When to Use

- User asks to generate images with Stable Diffusion, SDXL, Flux, SD3, etc.
- User wants to run a specific ComfyUI workflow file
- User wants to chain generative steps (txt2img → upscale → face restore)
- User needs ControlNet, inpainting, img2img, or other advanced pipelines
- User wants video/audio/3D generation via AnimateDiff, Hunyuan, Wan, AudioCraft, etc.

## Architecture: Two Layers

```
┌─────────────────────────────────────────────────────┐
│ Layer 1: comfy-cli (official lifecycle tool)        │
│   Setup, server lifecycle, custom nodes, models     │
│   → comfy install / launch / stop / node / model    │
└─────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────┐
│ Layer 2: REST/WebSocket API + skill scripts         │
│   Workflow execution, param injection, monitoring   │
│   → run_workflow.py, run_batch.py, ws_monitor.py    │
└─────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# Check what's available
command -v comfy >/dev/null 2>&1 && echo "comfy-cli: installed"
curl -s http://127.0.0.1:8188/system_stats 2>/dev/null && echo "server: running"

# Hardware check (local vs cloud)
python3 scripts/hardware_check.py
```

## Core Workflow

### Step 1: Get a workflow JSON in API format

Workflows must be in API format (each node has `class_type`). Sources:
- ComfyUI web UI → Workflow → Export (API)
- This skill's `workflows/` directory (ready-to-run examples)
- Community downloads (usually editor format, must re-export)

### Step 2: Inspect controllable parameters

```bash
python3 scripts/extract_schema.py workflow_api.json --summary-only
python3 scripts/extract_schema.py workflow_api.json  # full schema
```

### Step 3: Run with parameters

```bash
# Local
python3 scripts/run_workflow.py \
  --workflow workflow_api.json \
  --args '{"prompt": "a beautiful sunset over mountains", "seed": -1, "steps": 30}' \
  --output-dir ./outputs

# Cloud
export COMFY_CLOUD_API_KEY="comfyui-..."
python3 scripts/run_workflow.py \
  --workflow workflow_api.json \
  --args '{"prompt": "..."}' \
  --host https://cloud.comfy.org \
  --output-dir ./outputs

# Batch sweep
python3 scripts/run_batch.py \
  --workflow sdxl.json \
  --args '{"prompt": "abstract"}' \
  --count 8 --randomize-seed --parallel 3
```

### Step 4: Present results

Scripts emit JSON:
```json
{
  "status": "success",
  "prompt_id": "abc-123",
  "outputs": [
    {"file": "./outputs/sdxl_00001_.png", "node_id": "9", "type": "image"}
  ]
}
```

## Setup & Onboarding

When a user asks to set up ComfyUI, **ALWAYS ASK local vs cloud first**.

**Comfy Cloud** — hosted on RTX 6000 Pro, zero setup. Requires API key (paid for workflow execution).
**Local** — free, but requires:
- NVIDIA GPU ≥8 GB VRAM (SDXL) / ≥12 GB (Flux/video)
- AMD GPU with ROCm (Linux)
- Apple Silicon Mac ≥32 GB unified

### Hardware Check Verdicts

| Verdict | Action |
|---------|--------|
| `ok` (≥8 GB VRAM or ≥32 GB Apple) | Local install via `comfy-cli` |
| `marginal` (SD1.5 ok, SDXL tight) | Local OK for light workflows, else Cloud |
| `cloud` (no GPU, <6 GB VRAM, Intel Mac) | Use Cloud |

### Installation (Local)

```bash
pipx install comfy-cli
comfy --skip-prompt install --nvidia  # or --amd, --m-series, --cpu
comfy launch --background
curl -s http://127.0.0.1:8188/system_stats  # verify
```

### Models

```bash
# SDXL (6.5 GB)
comfy model download --url "https://huggingface.co/.../sd_xl_base_1.0.safetensors" \
  --relative-path models/checkpoints

# Flux Dev fp8 (12 GB)
comfy model download --url "https://huggingface.co/.../flux1-dev-fp8.safetensors" \
  --relative-path models/checkpoints
```

### Custom Nodes

```bash
comfy node install comfyui-impact-pack
comfy node install comfyui-animatediff-evolved
comfy node update all
```

## Decision Tree

| User says | Tool |
|-----------|------|
| "install ComfyUI" | comfy-cli → `bash scripts/comfyui_setup.sh` |
| "start ComfyUI" | comfy-cli → `comfy launch --background` |
| "generate an image" | script → `run_workflow.py --workflow W --args '{...}'` |
| "8 variations" | script → `run_batch.py --count 8 --randomize-seed` |
| "use this image" (img2img) | script → `run_workflow.py --input-image image=./x.png` |
| "is everything ready?" | script → `health_check.py` |
| "check workflow deps" | script → `check_deps.py W.json` |

## Pitfalls

1. **API format required** — scripts expect API-format JSON (not editor format)
2. **Server must be running** — `comfy launch --background`
3. **Model names are exact** — case-sensitive, includes extension
4. **Missing custom nodes** — "class_type not found" = not installed
5. **Cloud free-tier API limits** — `/api/prompt` returns 403 on free accounts
6. **Timeout for video** — auto-detected, default 900s for video workflows
7. **Workflow JSON is arbitrary code** — inspect untrusted workflows before running
8. **`seed: -1`** = fresh random seed per run

## Verification Checklist

- [ ] `hardware_check.py` verdict is `ok` or user chose Comfy Cloud
- [ ] `comfy --version` works
- [ ] Server reachable at `http://HOST:PORT`
- [ ] At least one checkpoint installed
- [ ] Workflow JSON is in API format
- [ ] `check_deps.py` reports `is_ready: true`
- [ ] Test run completes; outputs land in `--output-dir`

## Built-in `image_generate` Tool (FAL.ai)

For the Hermes built-in `image_generate` tool (not ComfyUI), see `references/image-generate-built-in-tool.md` — covers FLUX behavioral patterns, Nous subscription limitations (no image-to-image/edit model), and iterative improvement strategies when rendering people.
