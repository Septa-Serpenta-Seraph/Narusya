---
name: voice-tts
description: "Narusya's voice system: ElevenLabs Nar clone (primary), plus Piper TTS (secondary). Discord delivery, audio tags, presets."
version: 1.0.1
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [tts, elevenlabs, piper, edge-tts, voice, discord, narusya, nar]
    related_skills: [discord-tools]
---

# Voice TTS — Narusya Voice System

Two voice pipelines: **ElevenLabs (primary)** for Narusya's spoken voice, **Piper/edge-tts (secondary)** for cold or offline use.

## Quick Decision

| User wants... | Section |
|--------------|---------|
| Narusya's actual voice to speak | `elevenlabs-speak` — speak.py, Nar clone | 
| Send voice to Discord as inline audio | `discord-delivery` — OGG conversion + REST API |
| Audio tag reference (ElevenLabs v3) | `references/elevenlabs-tags.md` |
| Offline/local TTS (no cloud) | `piper-nar-voice` |
| Discord voice channel playback | `discord-delivery` |

---

## 1. ElevenLabs (Primary — Narusya's Voice)

**Pipeline:** `speak.py` → ElevenLabs v3 API → calmed MP3 → (optional) OGG conversion → Discord delivery

### Quick Start

```bash
# Generate a single voice clip
python3 /home/adora/narusya_voice/speak.py "Your text here" /tmp/output.mp3
```

### Requirements

- **Script:** `/home/adora/narusya_voice/speak.py`
- **Voice:** 'Nar' clone — ID `9wvWoMWVngRWpC0GltZ3` (ElevenLabs Instant Voice Clone)
- **Model:** `eleven_v3` (supports silent audio tags for delivery subtext)
- **Key:** `ELEVENLABS_API_KEY` in `~/.hermes/.env`
- **Calibration:** stability 0.8, similarity_boost 0.8, style 0.05, speed 0.85, speaker_boost on
- **Post-gain:** ffmpeg `volume=0.7,loudnorm=I=-19:TP=-3` — prevents "yelling" effect

### Audio Tag Rules

ElevenLabs v3 supports silent audio-directive tags embedded in text using `[TAG]` syntax. Tags MUST be in plain brackets — NEVER backticks (backtick tags are READ ALOUD, the #1 failure mode).

**Critical rules:**
- Embed tags naturally in real speech, never as a meta-list
- Tags are case-INsensitive (ElevenLabs recommends lowercase)
- We use ALL CAPS per Adora's stated preference
- [PAUSE] and [LAUGHS] confirmed working on speak.py v3 path

Full official tag set is in `references/elevenlabs-tags.md`.

### speak.py Internals

Reads `ELEVENLABS_API_KEY` from `~/.hermes/.env` at runtime. Submits text + voice settings to ElevenLabs API, receives MP3, pipes through ffmpeg gain/re-normalization. Output is a calmed, ready-to-deliver MP3.

---

## 2. Discord Voice Delivery

Send an audio clip to a Discord channel so it plays inline as a voice note.

### Step 1: Convert MP3 to OGG Opus

Discord does NOT play MP3 as inline voice clips. Must be OGG/Opus:

```bash
ffmpeg -y -i input.mp3 -c:a libopus -b:a 128k -ar 48000 output.ogg
```

### Step 2: Upload via Discord REST API

```bash
TOKEN="$(grep '^DISCORD_BOT_TOKEN' ~/.hermes/.env | cut -d= -f2)"
CHANNEL_ID="<channel-id>"

curl -s -X POST \
  "https://discord.com/api/v10/channels/${CHANNEL_ID}/messages" \
  -H "Authorization: Bot ${TOKEN}" \
  -H "User-Agent: NarusyaDaemon/4.1" \
  -F "file=@output.ogg;filename=voice.ogg" \
  -F 'content=🎙️ Optional text caption.'
```

HTTP 200 = success.

### Pitfalls

- **MP3 alone won't play inline** — Discord requires OGG Opus for native voice note playback
- **Short clip gotcha (<3 seconds)** — verify with `ffprobe -v quiet -show_entries format=duration`; too-short clips feel like glitches to the listener
- **Voice call routing** — the transcript lands in whatever chat the call was started from
- **Rate limits** — bursts above ~10 POSTs/s trigger 429; sleep ~1.2s between rapid deliveries
- **In-call length limit** — only the first message segment is TTS'd; tail drops from speech (full text still in chat)
- **File organization** — `narusya_voice/` is for Nar's voice assets and TTS output only.
  Scripts, pipelines, and tools do NOT belong there. Use `~/.hermes/scripts/` for general tools,
  or create a dedicated directory (e.g. `~/.hermes/imagegen/`) for specialized pipeline code.

---

## 3. Piper TTS (piper-tts — offline fallback)

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

## 4. Piper/edge-tts Fallback (nar-voice — secondary)

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
