---
name: visual-content
description: "Narusya-specific visual content: knowledge comics, article illustrations, and infographics using image_generate."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [comic, article-illustration, infographic, baoyu, visual, image-generation]
    related_skills: []
---

# Visual Content

Create Narusya-specific visual content: knowledge comics, article illustrations, and infographics. All use `image_generate` tool.

## Quick Decision

| User wants... | Tool |
|--------------|------|
| Knowledge comic / educational comic | baoyu-comic section |
| Illustrations for an article | baoyu-article-illustrator section |
| Infographic / visual summary | baoyu-infographic section |

---

## 1. Knowledge Comics (baoyu-comic)

Create original knowledge comics (知识漫画): educational, biography, tutorial.

### Options

| Option | Values |
|--------|--------|
| Art | ligne-claire, manga, realistic, ink-brush, chalk, minimalist |
| Tone | neutral, warm, dramatic, romantic, energetic, vintage, action |
| Layout | standard, cinematic, dense, splash, mixed, webtoon, four-panel |
| Aspect | 3:4 (default), 4:3, 16:9 |
| Language | auto, zh, en, ja, etc. |

### Presets

| Preset | Equivalent | Hook |
|--------|-----------|------|
| `ohmsha` | manga + neutral | Visual metaphors, no talking heads |
| `wuxia` | ink-brush + action | Qi effects, combat visuals |
| `shoujo` | manga + romantic | Decorative elements, romantic |
| `concept-story` | manga + warm | Visual symbol system, growth arc |
| `four-panel` | minimalist + neutral | 起承转合, B&W + spot color |

### Workflow

1. **Setup & Analyze** — Analyze content, save `analysis.md`
2. **Confirm** — Style, tone, layout (via `clarify` tool)
3. **Storyboard + Characters** — Generate storyboard, character definitions
4. **Review** — Conditional (if user requested)
5. **Prompts** — Generate prompts per page
6. **Review** — Conditional
7. **Generate Images** — Use `image_generate`, download each URL
8. **Completion report**

### Critical: Image Download

`image_generate` returns a URL, NOT a local file. After every call:
1. Read the URL from the tool result
2. Download with **absolute path**: `curl -fsSL "<url>" -o /abs/path/to/comic/<slug>/NN-page.png`
3. Verify file exists and is non-empty

**Never use relative paths for `curl -o`** — terminal CWD can drift between batches.

### Character Consistency

Driven by **text descriptions** in `characters/characters.md` embedded inline in every page prompt. The optional PNG character sheet is a human-facing review artifact.

---

## 2. Article Illustrations (baoyu-article-illustrator)

Analyze articles, identify illustration positions, generate images with Type × Style × Palette consistency.

### Three Dimensions

| Dimension | Controls |
|-----------|----------|
| **Type** | infographic, scene, flowchart, comparison, framework, timeline |
| **Style** | notion, warm, minimal, blueprint, watercolor, elegant |
| **Palette** | macaron, warm, neon — optional override |

### Workflow

1. **Detect references** (if user supplied images, use `vision_analyze`)
2. **Analyze content** — Save `analysis.md`
3. **Confirm settings** — Preset, density, style, palette (via `clarify`)
4. **Generate outline** → `outline.md`
5. **Generate prompts** → `prompts/NN-{type}-{slug}.md` (BLOCKING: must save before generating)
6. **Generate images** → Download URLs with absolute paths
7. **Finalize** — Insert `![desc](relative-path)` into article

### Core Principles

- **Visualize concepts, not metaphors** — if article uses metaphor, illustrate underlying concept
- **Labels use article data** — actual numbers, terms, quotes
- **Prompt files are reproducibility records** — save before generating
- **Strip secrets** — scan for API keys, tokens

---

## 3. Infographics (baoyu-infographic)

Create infographics with 21 layouts × 21 styles.

### Layout Gallery

| Layout | Best For |
|--------|----------|
| `linear-progression` | Timelines, processes |
| `binary-comparison` | A vs B, pros-cons |
| `comparison-matrix` | Multi-factor comparisons |
| `hierarchical-layers` | Pyramids, priority |
| `tree-branching` | Categories, taxonomies |
| `hub-spoke` | Central concept + items |
| `bento-grid` | Multiple topics, overview |
| `dashboard` | Metrics, KPIs |
| `funnel` | Conversion, filtering |
| `venn-diagram` | Overlapping concepts |
| `dense-modules` | High-density data |

### Style Gallery

| Style | Description |
|-------|-------------|
| `craft-handmade` | Hand-drawn, paper craft (default) |
| `claymation` | 3D clay, stop-motion |
| `kawaii` | Japanese cute, pastels |
| `cyberpunk-neon` | Neon glow, futuristic |
| `bold-graphic` | Comic style, halftone |
| `technical-schematic` | Blueprint, engineering |
| `pop-laboratory` | Grid, coordinate markers |
| `hand-drawn-edu` | Macaron pastels, hand-drawn |

### Workflow

1. **Analyze** — Save source, analyze topic/data type
2. **Structured content** → `structured-content.md`
3. **Recommend combinations** — Check keyword shortcuts, then recommend 3-5 layout×style combos
4. **Confirm** — Layout+style, aspect, language (via `clarify`)
5. **Generate prompt** → `prompts/infographic.md`
6. **Generate image** → Use `image_generate`
7. **Summary** — Report layout, style, output path

### Pitfalls

- **Data integrity** — never summarize or alter source statistics
- **Strip secrets** — scan for credentials before including in outputs
- **`image_generate` aspect ratios** — only `landscape`, `portrait`, `square`. Custom ratios map to nearest.
