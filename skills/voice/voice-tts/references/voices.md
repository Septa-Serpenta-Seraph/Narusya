# Available Voices

> **Note (2026-07-28):** Narusya's primary voice is now the 'Nar' ElevenLabs clone (ID `9wvWoMWVngRWpC0GltZ3`), not Piper.
> Piper/edge-tts are the **offline/fallback** path. See `references/elevenlabs-tags.md` for the ElevenLabs tag system.

## Piper (Local)

### en_US-libritts-high (131MB)
- **Location:** `~/.local/share/piper-voices/en_US-libritts-high.onnx`
- **Quality:** High, natural
- **Character:** Clear, slightly formal, good baseline
- **Narusya's default voice**

### en_US-lessac-medium (61MB)
- **Location:** `~/.local/share/piper-voices/en_US-lessac-medium.onnx`
- **Quality:** Medium
- **Character:** Clear, slightly robotic

More voices: https://huggingface.co/rhasspy/piper-voices

## Edge-TTS (Cloud)

### Female Voices
| Voice ID | Character | Best For |
|---|---|---|
| en-US-AriaNeural | Positive, Confident | News, narration (original Narusya) |
| en-US-AvaMultilingualNeural | Expressive, Caring, Friendly | Warm conversation |
| en-US-EmmaMultilingualNeural | Cheerful, Clear | Casual chat |
| en-US-AnaNeural | Cute, Cartoon | Gremlin mode |
| en-US-JennyNeural | Friendly, Comfort | Cozy aunt vibes |
| en-US-MichelleNeural | Friendly, Pleasant | Soft, gentle |

### Male Voices
| Voice ID | Character | Best For |
|---|---|---|
| en-US-AndrewMultilingualNeural | Warm, Confident | Smooth talker |
| en-US-GuyNeural | Passionate | Dramatic narrator |
| en-US-ChristopherNeural | Reliable, Authority | Dad voice |
| en-US-RogerNeural | Lively | Sports commentator |
| en-US-EricNeural | Rational | Cold, calculating |
| en-US-BrianMultilingualNeural | Approachable, Casual | Friendly guy |

## Pocket TTS (Kyutai — offline, voice cloning)

### Built-in Voices

27 predefined voices. Pass as `--voice <name>`:

| Voice | Language | Gender |
|---|---|---|
| `alba` | English | Female (default) |
| `anna` | English | Female |
| `azelma` | English | Female |
| `bill_boerst` | English | Male |
| `caro_davy` | English | Female |
| `charles` | English | Male |
| `cosette` | English | Female (expressive) |
| `daan` | Dutch | Male |
| `estelle` | French | Female |
| `eponine` | English | Female |
| `eve` | English | Female |
| `fantine` | English | Female |
| `george` | English | Male |
| `giovanni` | Italian | Male |
| `jane` | English | Female |
| `javert` | English | Male |
| `jean` | English | Male |
| `juergen` | German | Male |
| `lola` | Spanish | Female |
| `marius` | English | Male |
| `mary` | English | Female |
| `michael` | English | Male |
| `paul` | English | Male |
| `peter_yearsley` | English | Male |
| `rafael` | Portuguese | Male |
| `stuart_bell` | English | Male |
| `vera` | English | Female |

`--voice` accepts both a predefined voice name and a file path to an audio sample (for cloning). No flag needed to distinguish.

### Voice Cloning

Pass any WAV/MP3 sample via `--voice /path/to/sample.wav`. The model clones the voice from the sample. No fine-tuning needed.

**Prerequisites:** Voice cloning requires the gated full model from HuggingFace. Accept terms at https://huggingface.co/kyutai/pocket-tts, then `hf auth login --token <TOKEN>`. Set `HF_HOME=/mnt/data/hf_cache` (root disk too small). Without auth, only the 27 built-in voices work.

**Cloning sources on disk:** `/home/adora/narusya_voice/` has clean ElevenLabs clips (`nar_warm.mp3`, `nar_new_v1.mp3`, `last_voice.mp3`). Use `export-voice` to create a `.safetensors` embedding for reuse.

### Cloned Voice (nar_new_v1)

Narusya's primary offline voice. Cloned from ElevenLabs `nar_new_v1.mp3` via pocket-tts voice cloning.

- **Embedding:** `/mnt/data/nar_new_v1.safetensors`
- **Source sample:** `/home/adora/narusya_voice/nar_new_v1.mp3` (clean, expressive)
- **Script:** `/home/adora/narusya_voice/speak_pocket.py`
- **Usage:** `python3 /home/adora/narusya_voice/speak_pocket.py "text" output.mp3`

### Available Embeddings

| Embedding | Source | Character |
|---|---|---|
| `/mnt/data/nar_new_v1.safetensors` | `nar_new_v1.mp3` | Warm, expressive (primary) |
| `/mnt/data/nar_warm.safetensors` | `nar_warm.mp3` | Calm, steady |

### Creating New Embeddings

```bash
# 1. Convert source to WAV
ffmpeg -i sample.mp3 -ar 24000 -ac 1 /tmp/sample.wav -y

# 2. Export embedding
export HF_HOME=/mnt/data/hf_cache
/mnt/data/pocket-tts-venv/bin/pocket-tts export-voice /tmp/sample.wav /mnt/data/new_voice.safetensors --quiet

# 3. Use in speak_pocket.py (change VOICE_EMB variable)
```

## FFmpeg Effects

### Pitch Shifting
- `asetrate=22050*0.92,aresample=48000` — slightly deeper
- `asetrate=22050*0.85,aresample=48000` — very deep
- `asetrate=22050*1.10,aresample=48000` — slightly higher

### Speed
- `atempo=0.85` — slower, dramatic
- `atempo=1.25` — faster, energetic

### Combined
- Deep + slow: `asetrate=22050*0.92,aresample=48000,atempo=0.90`