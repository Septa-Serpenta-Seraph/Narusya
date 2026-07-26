---
name: voice-tts
description: "Local text-to-speech: Piper TTS engine (fast, offline, CPU) plus Narusya's voice system (presets, Discord playback, edge-tts fallback)."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [tts, piper, edge-tts, voice, discord, narusya]
    related_skills: []
---

# Voice TTS

Local text-to-speech using Piper TTS engine and Narusya's voice system.

## Quick Decision

| User wants... | Section |
|--------------|---------|
| Quick TTS generation with Piper | piper-tts section |
| Narusya's voice with presets and Discord | nar-voice section |

---

## 1. Piper TTS (piper-tts)

Piper is a fast, local neural TTS engine. Runs entirely on CPU, no cloud/API needed. Generates audio ~17x faster than real-time.

### Installation

Binary at `~/.local/bin/piper`, libraries at `~/.local/lib/piper/`.

### Wrapper Script: `~/.local/bin/piper-run`

```bash
#!/bin/bash
export LD_LIBRARY_PATH="$HOME/.local/lib/piper:$LD_LIBRARY_PATH"
export ESPEAK_DATA_PATH="$HOME/.local/lib/piper/espeak-ng-data"
exec "$HOME/.local/bin/piper" "$@"
```

### Environment Variables (REQUIRED)

```bash
export LD_LIBRARY_PATH=~/.local/lib/piper:$LD_LIBRARY_PATH
export ESPEAK_DATA_PATH=~/.local/lib/piper/espeak-ng-data
```

### Voices

Stored at `~/.local/share/piper-voices/`

| Voice | Size | Quality | Notes |
|---|---|---|---|
| `en_US-libritts-high.onnx` | 131MB | High | **Narusya's voice** — natural, expressive |
| `en_US-lessac-medium.onnx` | 61MB | Medium | Clear, slightly robotic |

### Usage

```bash
echo "Hello world" | piper --model ~/.local/share/piper-voices/en_US-libritts-high.onnx --output_file /tmp/output.wav
```

### Discord Voice Playback

Convert WAV → MP3 (48kHz stereo) for Discord:

```bash
ffmpeg -y -i input.wav -ar 48000 -ac 2 output.mp3
```

Play via discord.py:

```python
source = discord.FFmpegPCMAudio(path, options='-vn -ar 48000 -ac 2 -f s16le')
vc.play(discord.PCMVolumeTransformer(source, volume=1.0))
```

### More Voices

Download from: https://huggingface.co/rhasspy/piper-voices
Place `.onnx` and `.onnx.json` in `~/.local/share/piper-voices/`

---

## 2. Narusya Voice (nar-voice)

Narusya's voice system — generate speech with presets, play to Discord, save to file. Supports local piper TTS and cloud edge-tts.

### Quick Start

```bash
# Speak with default preset (deep)
python3 scripts/nar-voice.py speak "Hello world"

# Queue mode: single connection, multiple clips (no reconnect timeouts!)
python3 scripts/nar-voice.py speak "line one\nline two\nline three" --preset deep --discord --queue

# Queue from file: one clip per line
echo -e "First line\nSecond line\nThird line" > /tmp/lines.txt
python3 scripts/nar-voice.py speak /tmp/lines.txt --file --preset deep --discord --queue

# Use a specific preset
python3 scripts/nar-voice.py speak "I am dramatic" --preset dramatic

# Save to file
python3 scripts/nar-voice.py speak "test" --save /tmp/out.mp3

# Play to Discord voice (must be connected first)
python3 scripts/nar-voice.py speak "hi!" --preset smooth --discord

# List available presets
python3 scripts/nar-voice.py list-presets
```

### Presets

Defined in `presets.yaml`. Each preset specifies:
- **engine**: `piper` (local) or `edge-tts` (cloud)
- **voice/model**: which voice to use
- **pitch**: multiplier (< 1.0 = deeper, > 1.0 = higher) [piper only]
- **speed**: multiplier (< 1.0 = slower, > 1.0 = faster) [piper only]
- **effects**: list of audio effects (reverb, etc.) [piper only]

### Built-in Presets

| Preset | Engine | Voice | Pitch | Speed | Vibe |
|---|---|---|---|---|---|
| normal | piper | libritts-high | 1.0 | 1.0 | Default, clear |
| deep | piper | libritts-high | 0.92 | 1.0 | Serpent queen (Adora's fave) |
| dramatic | piper | libritts-high | 0.90 | 0.88 | Monologue mode |
| gremlin | edge-tts | AnaNeural | — | — | Unhinged cartoon |
| smooth | edge-tts | AvaMultilingualNeural | — | — | Warm, alive |

### Adding Presets

Edit `presets.yaml` — add a new entry under `presets:`. No code changes needed.

### Architecture

```
scripts/nar-voice.py
├── load_preset(name)     → preset config dict
├── generate_piper(text, preset) → mp3 path (temp file)
├── generate_edge_tts(text, preset) → mp3 path (temp file)
├── play_discord(mp3_path) → plays to connected voice channel
├── speak(text, preset, discord=False) → main entry point
└── CLI: argparse for speak/save/list-presets/join-voice
```

### Discord Integration

For `--discord` mode, the script needs:
- `DISCORD_BOT_TOKEN` from `~/.hermes/.env`
- Guild and channel IDs (defaults to Cultus Anarchia voice chat)

The script can either:
1. Join voice, play, disconnect (one-shot)
2. Stay connected for multiple plays (persistent)

### Notes

- Piper outputs 22050Hz mono WAV — always resample to 48kHz stereo for Discord
- Pitch shifting uses ffmpeg `asetrate` — formula: `asetrate=22050*<pitch>,aresample=48000`
- edge-tts is more expressive but goes through Microsoft servers
- Default preset is `deep` (Adora's preference)
