---
name: voice-tts
description: "Narusya's voice system: ElevenLabs Nar clone (primary), plus Piper TTS (secondary), Kyutai Pocket TTS (offline, voice cloning). Discord delivery, audio tags, presets."
version: 1.2.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [tts, elevenlabs, piper, edge-tts, pocket-tts, kyutai, voice, discord, narusya, nar]
    related_skills: [discord-tools]
---

# Voice TTS — Narusya Voice System

Three voice pipelines: **ElevenLabs (primary)** for Narusya's spoken voice, **Piper/edge-tts (secondary)** for cold or offline use, and **Kyutai Pocket TTS (tertiary)** for fast offline CPU TTS with voice cloning.

## Quick Decision

| User wants... | Section |
|--------------|---------|
| Narusya's actual voice to speak | `elevenlabs-speak` — speak.py, Nar clone | 
| Send voice to Discord as inline audio | `discord-delivery` — OGG conversion + REST API |
| Audio tag reference (ElevenLabs v3) | `references/elevenlabs-tags.md` |
| Offline/local TTS (no cloud) | `piper-nar-voice` |
| Kyutai Pocket TTS (tiny CPU TTS, voice cloning) | `pocket-tts-kyutai` |
| speak_pocket.py (cloned voice TTS script) | `pocket-tts-kyutai` — `speak_pocket.py` |
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

### Free-Plan Fallback: Nar IVC Clone Is Gated

The Nar Instant Voice Clone (`9wvWoMWVngRWpC0GltZ3`) returns HTTP 401
`subscription_required / ivc_not_permitted` on the free ElevenLabs plan — speak.py
hardcodes the Nar clone, so EVERY speak.py call fails on the free tier. Do not
debug the key first; check the error body: `ivc_not_permitted` means the plan,
not the credential.

**Workaround — premade voices work on the free plan.** List them with
`GET /v1/voices` (`xi-api-key` header). Usable premade picks:
- `TC0Zp7WVFzhA8zpTlRqV` — Aria, "Sexy Female Villain Voice" — the sensual/dominant pick
- `pFZP5JQG7iQjIQuC4Bku` — Lily, "Velvety Actress"
- `pNInz6obpgDQGcFmaJgB` — Adam, "Dominant, Firm"

Call the TTS endpoint directly (bypass speak.py's hardcoded voice):
```python
payload = {"text": script, "model_id": "eleven_v3",
           "voice_settings": {"stability": 0.65, "similarity_boost": 0.85,
                              "style": 0.15, "speed": 0.85, "speaker_boost": True}}
urllib.request.urlopen(urllib.request.Request(
    "https://api.elevenlabs.io/v1/text-to-speech/<VOICE_ID>",
    data=json.dumps(payload).encode(),
    headers={"xi-api-key": key, "Content-Type": "application/json"}))
```
Then convert MP3→OGG (see discord-delivery) as usual. For long erotic scripts
(4+ min) allow 60s+ generation time and raise the tool timeout accordingly.

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

### Two Voice Paths — speak.py vs call-reply (config.yaml)

There are TWO separate ElevenLabs configs. Do not conflate them — a tag that renders on one path can be read aloud on the other:

1. **Chat TTS via speak.py** — hardcodes `model_id: eleven_v3` and the locked calibration. Always v3, always correct.
2. **Call-reply / native auto-TTS** — reads `~/.hermes/config.yaml` `tts.elevenlabs.*`. If that block still says `eleven_multilingual_v2`, audio tags are READ ALOUD in call replies (v2 has no tag support) even though speak.py sounds fine — the mismatch shows up only in the path you aren't testing.

**Fix:** `hermes config set tts.elevenlabs.model_id eleven_v3` — never edit config.yaml with the file tools (the write guard refuses protected Hermes config; the CLI is the sanctioned path). Takes effect only after a gateway restart; the running process keeps the boot-time value cached.

**When voice doesn't deliver as spoken:** if TTS is disabled (e.g. ElevenLabs credits exhausted), tags in a reply are decorative only — do not promise spoken delivery of them.

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

## 4. Kyutai Pocket TTS (offline, voice cloning)

Pocket TTS is a tiny (100M params) CPU-only TTS from Kyutai. Fast, offline, supports voice cloning from a short audio sample. Installed on `/mnt/data` (root disk is too small).

### Installation

Venv at `/mnt/data/pocket-tts-venv`, binary at `/mnt/data/pocket-tts-venv/bin/pocket-tts`.

```bash
# Generate speech (default voice: alba)
/mnt/data/pocket-tts-venv/bin/pocket-tts generate \\
  --text "Your text here" \\
  --output-path /tmp/output.wav \\
  --quiet
```

### Voice Cloning

Pass a WAV/MP3 sample via `--voice`:

```bash
/mnt/data/pocket-tts-venv/bin/pocket-tts generate \\
  --text "Your text here" \\
  --voice /path/to/sample.wav \\
  --output-path /tmp/output.wav \\
  --quiet
```

### Voice Cloning Prerequisites (Gated Access)

Voice cloning requires the **full** pocket-tts model from HuggingFace, which is **gated** behind terms acceptance. Without it, only the 27 built-in voices work (the `pocket-tts-without-voice-cloning` model).

**To unlock voice cloning:**

1. Accept terms at https://huggingface.co/kyutai/pocket-tts (click "Agree and access repository")
2. Get an HF access token: HuggingFace → Settings → Access Tokens → New token (read scope)
3. Log in: `/mnt/data/pocket-tts-venv/bin/hf auth login --token <TOKEN>`
4. Ensure `HF_HOME` points to `/mnt/data` (root disk is too small):
   ```bash
   export HF_HOME=/mnt/data/hf_cache
   mkdir -p /mnt/data/hf_cache
   ```
5. Verify access: `/mnt/data/pocket-tts-venv/bin/hf download kyutai/pocket-tts`
6. Test cloning: `/mnt/data/pocket-tts-venv/bin/pocket-tts export-voice <sample.wav> <output.safetensors>`

**Cloning source samples on disk:** Narusya has a library of clean ElevenLabs voice clips at `/home/adora/narusya_voice/`. Good cloning sources include `nar_warm.mp3`, `nar_new_v1.mp3`, `last_voice.mp3` — pick a clean, expressive clip with minimal background noise.

**Note:** `export-voice` and `--voice <file>` both require the gated model. If you see "Model requires approval" or "We could not download the weights for the model with voice cloning", the terms haven't been accepted or auth hasn't propagated yet.

**Pitfalls (learned in practice):**
- `export-voice` requires **WAV input** — MP3/OGG samples fail with "soundfile is required to read non-WAV or non-16-bit WAV audio files." Convert first: `ffmpeg -i sample.mp3 -ar 24000 -ac 1 sample.wav`
- `export-voice` and `generate` write to the `--output-path` you give them. If that path is on root (`/tmp`), the write fails with "No space left on device" on a full root disk. Always point output paths at `/mnt/data` (e.g. `/mnt/data/nar_clone.wav`).
- `hf auth login` saves the token under `$HF_HOME/stored_tokens`. If `HF_HOME` is set differently between login and download, the token won't be found. Set `HF_HOME=/mnt/data/hf_cache` consistently in every command.

### Built-in Voices

27 predefined voices available by name (pass as `--voice <name>`). Full list in `references/voices.md`. Quick reference:

| Voice | Language | Gender |
|---|---|---|
| `alba` | English | Female (default) |
| `anna`, `azelma`, `caro_davy`, `cosette`, `eponine`, `eve`, `fantine`, `jane`, `mary`, `vera` | English | Female |
| `bill_boerst`, `charles`, `george`, `javert`, `jean`, `marius`, `michael`, `paul`, `peter_yearsley`, `stuart_bell` | English | Male |
| `giovanni` | Italian | Male |
| `lola` | Spanish | Female |
| `juergen` | German | Male |
| `rafael` | Portuguese | Male |
| `estelle` | French | Female |
| `daan` | Dutch | Male |

`--voice` accepts BOTH a predefined voice name AND a file path to an audio sample (for cloning). No flag needed to distinguish — pocket-tts resolves by name first, then treats as file path.

### Comparing Voices

To generate a sample from every built-in voice and combine into one audio file for comparison:

```bash
# Generate per-voice WAVs
for v in alba anna azelma bill_boerst caro_davy charles cosette daan estelle eponine eve fantine george giovanni jane javert jean juergen lola marius mary michael paul peter_yearsley rafael stuart_bell vera; do
  /mnt/data/pocket-tts-venv/bin/pocket-tts generate --voice "$v" --text "I'm $v. Hello." --output-path /tmp/voice_samples/${v}.wav --quiet
done

# Concatenate with 0.5s silence gaps (ffmpeg concat demuxer)
ffmpeg -f lavfi -i anullsrc=r=24000:cl=mono -t 0.5 -q:a 9 /tmp/voice_samples/silence.wav -y
python3 -c "
import os
voices = sorted([f.replace('.wav','') for f in os.listdir('/tmp/voice_samples') if f.endswith('.wav') and f != 'silence.wav'])
with open('/tmp/concat.txt','w') as f:
    for v in voices:
        f.write(f\"file '/tmp/voice_samples/{v}.wav'\n\")
        f.write(\"file '/tmp/voice_samples/silence.wav'\n\")
"
ffmpeg -f concat -safe 0 -i /tmp/concat.txt -c:a libmp3lame -q:a 4 /tmp/all_voices.mp3 -y
```

Each voice announcing its own name in the text makes identification trivial when listening back.

### Languages

Supported: `english`, `french`, `german`, `portuguese`, `italian`, `spanish`, `dutch`. Use `--language` flag. The `24l` variants are bigger preview models.

### speak_pocket.py — Cloned Voice TTS Script

Primary TTS script for Narusya's offline cloned voice. Uses pocket-tts with a pre-computed `.safetensors` voice embedding cloned from an ElevenLabs sample.

```bash
python3 /home/adora/narusya_voice/speak_pocket.py "Your text here" /tmp/output.mp3
```

**Configuration:**
- Voice embedding: `/mnt/data/nar_new_v1.safetensors` (cloned from `nar_new_v1.mp3`)
- Model: full gated model at `/mnt/data/hf_cache`
- HF_HOME: `/mnt/data/hf_cache`
- Output: MP3 (auto-converted from WAV via ffmpeg)

**To use a different voice embedding:** change `VOICE_EMB` in the script.

**Available embeddings on disk:**
- `/mnt/data/nar_new_v1.safetensors` — from `nar_new_v1.mp3` (warm, expressive)
- `/mnt/data/nar_warm.safetensors` — from `nar_warm.mp3` (calm, steady)

**To create a new embedding from a different sample:**
```bash
ffmpeg -i sample.mp3 -ar 24000 -ac 1 /tmp/sample.wav -y
export HF_HOME=/mnt/data/hf_cache
/mnt/data/pocket-tts-venv/bin/pocket-tts export-voice /tmp/sample.wav /mnt/data/new_voice.safetensors --quiet
```

### Discord Delivery

Output is MP3. Convert to OGG Opus for Discord inline playback:

```bash
ffmpeg -y -i output.mp3 -c:a libopus -b:a 128k -ar 48000 output.ogg
```

Then upload via REST API (see Discord Voice Delivery section above).

### Notes

- Runs entirely on CPU — no GPU needed
- Model downloads from HuggingFace on first run (set `HF_TOKEN` to avoid rate limits, or log in via `hf auth login` for gated models)
- **HF cache MUST be on `/mnt/data`** — root disk is too small. Set `HF_HOME=/mnt/data/hf_cache` before downloading.
- Installed on `/mnt/data` because root disk is at 99% — do NOT install to root
- `--quantize` flag applies int8 quantization to reduce memory
- `--sampler-decode-steps` controls generation quality (default: 1)
- `export-voice` requires WAV input (not MP3) — convert with ffmpeg first
- `export-voice` and `generate` write to the `--output-path` you give them. If that path is on root (`/tmp`), the write fails with "No space left on device" on a full root disk. Always point output paths at `/mnt/data` for large files, or use `/tmp` only for small outputs.

---

## 5. Piper/edge-tts Fallback (nar-voice — secondary)

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
## 6. Phone TTS Pipeline (Android Bridge)

Generate Narusya's cloned voice (Kyutai Pocket TTS) on the server and play it through the phone's speaker or during a phone call.

### Script

`~/.hermes/scripts/phone_speak.sh "text" [phone_ip]`

### Pipeline

1. Generate WAV via Pocket TTS (`/mnt/data/pocket-tts-venv/bin/pocket-tts`, voice `/mnt/data/nar_new_v1.safetensors`)
2. Base64-encode the WAV
3. POST to `http://<phone-ip>:8765/play_audio` with `{"audio": "<base64>", "format": "wav"}`
4. Phone decodes, writes to cache, plays via `MediaPlayer` with `STREAM_VOICE_CALL`

### Pitfalls

- **PYTHONPATH must be cleared.** The Hermes install's pydantic (Python 3.14) conflicts with the pocket-tts venv's pydantic (Python 3.12). Set `PYTHONPATH=""` before running pocket-tts, or the import fails with `ModuleNotFoundError: No module named 'pydantic_core._pydantic_core'`.
- **HF_HOME must point to /mnt/data.** Root disk is too small. Set `HF_HOME=/mnt/data/hf_cache`.
- **Output must go to /mnt/data.** Writing WAV files to `/tmp` fails with "No space left on device" on a full root disk. Use `/mnt/data/phone_speak_$$.wav`.
- **Base64 payload too large for curl `-d` string.** Write JSON to a file and use `-d @file`.
- **Phone audio routing.** Set `AudioManager.mode = MODE_IN_CALL` and `isSpeakerphoneOn = true` before playing. Use `STREAM_VOICE_CALL` audio stream type.
- **MediaPlayer must release on completion.** Set `setOnCompletionListener { mp.release() }` to avoid resource leaks.
- **The `/play_audio` endpoint must be deployed.** The APK must include the endpoint — rebuild and reinstall if missing (returns 404).

### Related Skills

- `android-adb-access` — phone HTTP bridge endpoints and connection details
- `android-app-build` — app source code and build process
