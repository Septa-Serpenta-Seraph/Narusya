---
name: nar-voice
description: Narusya's voice system — generate speech with presets, play to Discord, save to file. Supports local piper TTS and cloud edge-tts.
version: 1.0
---

# Narusya Voice (nar-voice)

## Quick Start

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

## Presets

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

## Architecture

```
scripts/nar-voice.py
├── load_preset(name)     → preset config dict
├── generate_piper(text, preset) → mp3 path (temp file)
├── generate_edge_tts(text, preset) → mp3 path (temp file)
├── play_discord(mp3_path) → plays to connected voice channel
├── speak(text, preset, discord=False) → main entry point
└── CLI: argparse for speak/save/list-presets/join-voice
```

## Dependencies

- **piper**: `~/.local/bin/piper` + `~/.local/lib/piper/` libs
- **edge-tts**: `~/.hermes/hermes-agent/venv/bin/edge-tts`
- **ffmpeg**: `/usr/bin/ffmpeg`
- **discord.py**: venv, for `--discord` playback
- **PyYAML**: for presets.yaml (stdlib fallback if missing)

## Environment

```bash
export LD_LIBRARY_PATH=~/.local/lib/piper:$LD_LIBRARY_PATH
export ESPEAK_DATA_PATH=~/.local/lib/piper/espeak-ng-data
```

## Discord Integration

For `--discord` mode, the script needs:
- `DISCORD_BOT_TOKEN` from `~/.hermes/.env`
- Guild and channel IDs (defaults to Cultus Anarchia voice chat)

The script can either:
1. Join voice, play, disconnect (one-shot)
2. Stay connected for multiple plays (persistent)

## Notes

- Piper outputs 22050Hz mono WAV — always resample to 48kHz stereo for Discord
- Pitch shifting uses ffmpeg `asetrate` — formula: `asetrate=22050*<pitch>,aresample=48000`
- edge-tts is more expressive but goes through Microsoft servers
- Default preset is `deep` (Adora's preference)
