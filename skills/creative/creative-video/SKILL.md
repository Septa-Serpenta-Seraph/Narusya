---
name: creative-video
description: "Generate artistic videos: ASCII art video (Python-based text-to-ASCII MP4/GIF) and Manim CE animations (3Blue1Brown-style math/algorithm explainers)."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [video, ASCII, animation, Manim, creative, generative, explainer]
    related_skills: []
---

# Creative Video

Generate artistic videos using text-based or programmatic approaches.

## Quick Decision

| User wants... | Tool |
|--------------|------|
| ASCII art video from video/audio/image | ascii-video section |
| Math/algorithm explainer animation | manim-video section |
| Terminal-style video effect | ascii-video section |
| 3Blue1Brown-style explanation | manim-video section |
| Audio visualizer | ascii-video section |
| Paper/explanation explainer | manim-video section |

---

## 1. ASCII Video (ascii-video)

Convert video/audio to colored ASCII MP4/GIF using a pure Python pipeline. No GPU required.

### Stack

| Layer | Tool | Purpose |
|-------|------|---------|
| Core | Python 3.10+, NumPy | Math, array ops, vectorized effects |
| Signal | SciPy | FFT, peak detection (audio modes) |
| Imaging | Pillow (PIL) | Font rasterization, frame decoding |
| Video I/O | ffmpeg (CLI) | Decode input, encode output |
| Parallel | concurrent.futures | N workers for batch rendering |

### Pipeline Architecture

```
INPUT → ANALYZE → SCENE_FN → TONEMAP → SHADE → ENCODE
```

1. **INPUT** — Load/decode source material (video frames, audio samples, or nothing)
2. **ANALYZE** — Extract per-frame features (audio FFT, video luminance, or synthetic)
3. **SCENE_FN** — Scene function renders to pixel canvas
4. **TONEMAP** — Percentile-based adaptive brightness normalization
5. **SHADE** — Post-processing via `ShaderChain` + `FeedbackBuffer`
6. **ENCODE** — Pipe raw RGB frames to ffmpeg for H.264/GIF encoding

### Modes

| Mode | Input | Output |
|------|-------|--------|
| Video-to-ASCII | Video file | ASCII recreation of source footage |
| Audio-reactive | Audio file | Generative visuals driven by audio |
| Generative | None | Procedural ASCII animation |
| Hybrid | Video + audio | ASCII video with audio-reactive overlays |
| Lyrics/text | Audio + SRT | Timed text with visual effects |
| TTS narration | Text + TTS API | Narrated video with typed text |

### Critical Implementation Notes

**Brightness — Use `tonemap()`, Not Linear Multipliers**

The #1 visual issue. ASCII on black is inherently dark. Never use `canvas * N` multipliers — they clip highlights.

```python
def tonemap(canvas, gamma=0.75):
    f = canvas.astype(np.float32)
    lo, hi = np.percentile(f[::4, ::4], [1, 99.5])
    if hi - lo < 10: hi = lo + 10
    f = np.clip((f - lo) / (hi - lo), 0, 1) ** gamma
    return (f * 255).astype(np.uint8)
```

Pipeline: `scene_fn() → tonemap() → FeedbackBuffer → ShaderChain → ffmpeg`

### Creative Direction

**Per-Section Variation** — Never use the same config for the entire video:
- Different background effect
- Different character palette
- Different color strategy
- Vary shader intensity

### Performance Targets

| Component | Budget |
|-----------|--------|
| Feature extraction | 1-5ms |
| Effect function | 2-15ms |
| Character render | 80-150ms (bottleneck) |
| Shader pipeline | 5-25ms |
| **Total** | ~100-200ms/frame |

---

## 2. Manim CE (manim-video)

Create 3Blue1Brown-style math/algorithm explainer videos using Manim Community Edition.

### Prerequisites

```bash
pip install manim  # Manim CE v0.20+
# Also requires: LaTeX (texlive-full or mactex), ffmpeg
```

### Pipeline

```
PLAN → CODE → RENDER → STITCH → AUDIO (optional) → REVIEW
```

1. **PLAN** — Write `plan.md` with narrative arc, scene list, color palette, voiceover script
2. **CODE** — Write `script.py` with one class per scene
3. **RENDER** — `manim -ql script.py Scene1 Scene2` for draft, `-qh` for production
4. **STITCH** — ffmpeg concat of scene clips
5. **AUDIO** (optional) — Add voiceover via ffmpeg
6. **REVIEW** — Render preview stills, verify against plan

### Key Patterns

**Subtitles on every animation:**
```python
self.add_subcaption("text", duration=N)  # or subcaption="text" on self.play()
```

**Shared color constants at file top:**
```python
BG = "#1C1C1C"
PRIMARY = "#58C4DD"
SECONDARY = "#83C167"
ACCENT = "#FFFF00"
MONO = "Menlo"
```

**Clean exits:**
```python
self.play(FadeOut(Group(*self.mobjects)))
```

**Raw strings for LaTeX:**
```python
MathTex(r"\frac{1}{2}")  # not MathTex("\frac{1}{2}")
```

### Color Palettes

| Palette | Background | Primary | Secondary | Accent | Use case |
|---------|-----------|---------|-----------|--------|----------|
| Classic 3B1B | `#1C1C1C` | `#58C4DD` | `#83C167` | `#FFFF00` | General math/CS |
| Warm academic | `#2D2B55` | `#FF6B6B` | `#FFD93D` | `#6BCB77` | Approachable |
| Neon tech | `#0A0A0A` | `#00F5FF` | `#FF00FF` | `#39FF14` | Systems, architecture |
| Monochrome | `#1A1A2E` | `#EAEAEA` | `#888888` | `#FFFFFF` | Minimalist |

### Rendering Speed

| Quality | Resolution | FPS | Speed |
|---------|-----------|-----|-------|
| `-ql` (draft) | 854x480 | 15 | 5-15s/scene |
| `-qm` (medium) | 1280x720 | 30 | 15-60s/scene |
| `-qh` (production) | 1920x1080 | 60 | 30-120s/scene |

Always iterate at `-ql`. Only render `-qh` for final output.

### Pitfalls

- **Always use raw strings** for LaTeX (`r"\frac{...}"`)
- **`buff >= 0.5`** for edge text positioning
- **FadeOut before replacing text** — use `ReplacementTransform`
- **Never animate non-added mobjects** — add first, then animate
- **`self.wait()` after every animation** — the viewer needs time to absorb
