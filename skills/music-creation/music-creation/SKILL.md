---
name: music-creation
description: "Generate music and audio: HeartMuLa (Suno-like music generation), spectrograms/audio visualizations (Songsee), and Suno AI music prompts for songwriting."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Music, Audio, Songwriting, Spectrogram, MusicGen, HeartMuLa, Suno]
    related_skills: []
---

# Music Creation

Tools and techniques for generating music, audio visualizations, and songwriting with AI.

---

## 1. HeartMuLa — AI Music Generation

Set up and run HeartMuLa, the open-source music generation model family (Suno-like). Generates full songs from lyrics + tags with multilingual support.

### Setup

```bash
# Install dependencies
pip install heartmula  # or clone from GitHub

# Verify
heartmula --version
```

### Generation

```bash
# Basic song generation
heartmula generate \
  --lyrics "Your song lyrics here" \
  --tags "pop,emotional,upbeat" \
  --output song.wav

# Multilingual support
heartmula generate \
  --lyrics "你的歌词" \
  --tags "mandopop,balad" \
  --language zh \
  --output song_zh.wav
```

### Parameters

| Flag | Description | Default |
|------|-------------|---------|
| `--lyrics` | Song lyrics text | Required |
| `--tags` | Style tags (comma-separated) | Varies |
| `--language` | Language code | auto |
| `--output` | Output file path | song.wav |
| `--model` | Model variant | default |

### Pitfalls

- First generation may take several minutes to download models
- Lyrics should be in the language matching the `--language` flag
- Genre tags affect mood: "upbeat", "melancholic", "energetic", "ambient"

---

## 2. Songsee — Audio Visualization

Generate spectrograms and audio feature visualizations from audio files via CLI. Useful for audio analysis, music production debugging, and visual documentation.

### Usage

```bash
# Generate a spectrogram
songsee spectrogram song.wav --output spectrogram.png

# Generate multiple visualizations
songsee analyze song.wav \
  --features mel,chroma,mfcc,tempogram \
  --output-dir ./visualizations/

# Quick overview
songsee quick song.wav --output overview.png
```

### Features

| Feature | Description |
|---------|-------------|
| `mel` | Mel spectrogram |
| `chroma` | Chroma/tonal features |
| `mfcc` | MFCC coefficients |
| `tempogram` | Rhythm/tempo analysis |
| `onset` | Onset detection envelope |

### Pitfalls

- Requires `librosa` and `matplotlib` Python packages
- Large audio files (>10 minutes) may take significant processing time
- Output images are PNG format

---

## 3. Songwriting & AI Music Prompts

Crafting effective prompts for Suno AI and similar music generation tools.

### Prompt Structure

```
[Genre],[Mood],[Tempo],[Instruments],[Vocal Style],[Structure]
```

### Examples

```
# Pop song
pop,upbeat,fast,piano+drums+synth,soulful female vocals,verse-chorus-verse-chorus-bridge-chorus

# Ambient track
ambient,calm,slow,drone+pad+soft piano,wordless male vocals,instrumental

# Rock ballad
rock,melancholic,moderate,electric guitar+bass+drums,gritty male vocals,verse-chorus-verse-chorus-outro
```

### Prompt Tips

- Be specific about mood and energy level
- Include instrument preferences for richer output
- Structure helps the AI understand song flow
- Genre tags are the strongest signal
- Language affects vocal style significantly

### Common Tag Groups

| Category | Tags |
|----------|------|
| Genre | pop, rock, hip-hop, electronic, ambient, folk, jazz, classical |
| Mood | upbeat, melancholic, energetic, calm, dark, dreamy, aggressive |
| Tempo | slow, moderate, fast, very-fast |
| Instruments | piano, guitar, drums, synth, bass, strings, brass, woodwinds |
| Vocal | male, female, duo, choir, whispered, shouted, rap, sung |

---

## Quick Decision

| Need | Tool |
|------|------|
| Generate a song from lyrics | HeartMuLa |
| Visualize audio features | Songsee |
| Craft Suno prompts | This skill's prompt reference |
| Analyze music production | Songsee |
