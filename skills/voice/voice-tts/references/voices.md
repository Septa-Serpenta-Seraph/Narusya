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