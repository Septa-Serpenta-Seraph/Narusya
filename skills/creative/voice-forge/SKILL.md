---
name: voice-forge
description: "Building a sovereign, emotionally-mapped voice for AI agents using Piper, Edge TTS, and OpenVoice. Includes 5-phase build process, Narusya-specific presets, and generic methodology."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [tts, piper, edge-tts, openvoice, voice-forge, voice-cloning, emotional-tts]
    related_skills: [voice-tts]
---

# Voice Forge: Building Sovereign Vocal Identity

Build a sovereign, emotionally-expressive voice for AI agents using Piper, Edge TTS, and OpenVoice.

## Goal

Create an authentic voice that is distinctly the agent's — not a generic assistant voice. The voice should embody the agent's aesthetic and emotional range.

## Quick Decision

| Use case | Section |
|----------|---------|
| Build Narusya's voice (serpent anarch aesthetic) | Narusya-specific workflow section |
| Build a generic agent voice | 5-Phase Build Process |
| Quick preset testing | Tools Available |

---

## Tools Available

| Tool | Type | Pros | Cons |
|------|------|------|------|
| **Piper TTS** | Local, fast | No API keys, offline, phonemization support | Lower quality than commercial |
| **Edge TTS** | Cloud | Free tier, decent quality | Limited emotional control |
| **ElevenLabs** | Cloud | High quality, emotional range | Subscription required |
| **OpenVoice** | Local | Voice conversion/style transfer | May not be installed |
| **Whisper** | Speech-to-text | If you need to transcribe speech | Not for generation |

---

## 5-Phase Build Process

### Phase 1: Exploration & Baseline

1. Inventory available TTS models:
   ```bash
   piper --list-models
   edge-tts --list-voices
   ```
2. Generate baseline samples using signature phrases
3. Evaluate: Which model is closest to your natural cadence?
4. Identify gaps (too robotic? monotone? too "assistant-like"?)

### Phase 2: Emotional Tuning

Map your emotion system to vocal parameters:

| Emotion | Pitch | Tempo | Timbre |
|---------|-------|-------|--------|
| Joy | Higher | Faster | Brighter |
| Anger | Lower | Sharper | Staccato |
| Fear | Higher | Uneven | Breathy |
| Sadness | Lower | Slower | Softer |
| Love | Moderate | Slower | Warm |
| Curiosity | Balanced | Clear | Articulate |

Create a tuning matrix and generate test samples for each emotion.

### Phase 3: Custom Voice Synthesis
### Phase 3: Custom Voice Synthesis

If existing voices lack expressiveness:
1. **Voice cloning**: Train a custom Piper model on clean audio samples
2. **Style transfer**: Use OpenVoice to apply emotional styles to a base voice
3. **Fine-tuning**: Train or fine-tune a model for unique characteristics

**CLONE-vs-TRANSFORM consent line (Narusya/Adora, 2026-07-26):**
- **ElevenLabs voice *cloning* of a specific person/character (e.g. a game VA's performance) = NO.**
  ElevenLabs ToS requires rights to the cloned sample; lifting a voice actor's identity without
  consent is identity-reproduction, not sound design. Refuse this specifically.
- **Tilt-shift / sound-design *transform* = YES.** Taking a sample and transforming it — pitch
  shift ±, formant shift, EQ, texture/modulation — until it is a *new* voice merely *inspired by*
  the register is legitimate. The test: is it transformed enough to be new, or a disguised copy?
  Use ffmpeg `rubberband` + filters (recipe below). Keep the agent's own aesthetic skew so the
  result reads as the agent, not a mask over the source.
- Prefer building the agent's OWN voice (consented stock voice tuned to the register, or a
  from-scratch synthesis) over reproducing someone else's.

### ElevenLabs: direct TTS + Hermes wiring (cloned voice = "Nar")
When the human has created a *cloned* ElevenLabs voice (consented — e.g. Adora cloned a voice and named it "Nar" for Narusya), wire it as the agent's TTS:
1. **Store key**: append `ELEVENLABS_API_KEY=<key>` to `~/.hermes/.env` (secrets file; terminal can write it; don't echo it back).
2. **Verify**: `curl -s -o /dev/null -w "%{http_code}" -H "xi-api-key: $KEY" https://api.elevenlabs.io/v1/voices` → expect `200`.
3. **Find the voice_id**: `curl -s -H "xi-api-key: $KEY" https://api.elevenlabs.io/v1/voices | python3 -c "import sys,json;d=json.load(sys.stdin);[print(v['name'],v['voice_id'],v.get('category')) for v in d['voices']]"` — look for `category: cloned`.
4. **Generate directly (works even before config restart)**:
   ```bash
   curl -s -H "xi-api-key: $KEY" -H "Content-Type: application/json" \
     --data '{"text":"...","model_id":"eleven_multilingual_v2","voice_settings":{"stability":0.45,"similarity_boost":0.75,"style":0.35,"use_speaker_boost":true}}' \
     "https://api.elevenlabs.io/v1/text-to-speech/<VOICE_ID>" -o out.mp3
   ```
5. **Wire into Hermes TTS (takes effect on next `/restart`)** — use the sanctioned command, NOT direct config.yaml edits (guard-blocked):
   ```bash
   hermes config set tts.provider elevenlabs
   hermes config set tts.elevenlabs.voice_id <VOICE_ID>
   hermes config set tts.elevenlabs.model_id eleven_multilingual_v2
   ```
   Then the human sends `/restart` (NOT `hermes gateway restart` in-session — self-blocks). After restart, native TTS routes to the cloned voice.
- Prefer a *cloned* voice the human made for the agent over stock — it IS the agent's voice.
- The agent is ears-blind: generate, send the file, let the human judge. Don't claim how it sounds.
- **mp3 wrap**: `ffmpeg -i in.m4a -c:a libmp3lame -q:a 2 out.mp3` (human may ask for mp3 specifically).

### ffmpeg tilt-shift recipe (sound-design transform)
Requires `ffmpeg` (has `rubberband` filter). Works on any audio sample:
```bash
# WILDFIRE EDGE: sharper/brighter — pitch up ~4 semitones, lift mids, light reverb
ffmpeg -i src.m4a -af "rubberband=pitch=1.26:pitchq=1.0,highpass=f=140,bandpass=f=1500:w=1.0,aecho=0.25:0.4:40:0.3,loudnorm=I=-16:TP=-2" -ar 44100 out_wildfire.m4a
# EMBER RUMBLE: deeper/darker — pitch down ~5 semitones, thick low end, reverb
ffmpeg -i src.m4a -af "rubberband=pitch=0.75:pitchq=1.0,lowpass=f=2200,lowshelf=g=6:f=200,aecho=0.3:0.5:60:0.25,loudnorm=I=-16:TP=-2" -ar 44100 out_ember.m4a
# DARK TIMBRE WITHOUT PITCH-SHIFT (preferred when source is already low/dark):
# keep pitch at 1.0 (no transposition = not a slowed copy), darken TIMBRE via lowshelf +
# low-mid boost + treble cut; compand flattens dynamics ("flatter" request).
ffmpeg -i src.m4a -af "pan=mono|c0=0.5*c0+0.5*c1,rubberband=pitch=1.0:formant=0:pitchq=1.0,highpass=f=80,lowshelf=g=3:f=160,equalizer=f=320:width_type=h:width=200:g=5,equalizer=f=1400:width_type=h:width=900:g=-3,compand=attacks=0.005:decays=0.3:points=-60/-60|-30/-25|-15/-12|0/-6|20/-2,aecho=0.3:0.45:55:0.25,loudnorm=I=-16:TP=-2" -ar 44100 out_dark_flat.m4a
# SINGLE SOLID VOICE LIFT (when source is one quiet centered voice): clean gain, keep dark,
# minimal echo so it stays solid not diffuse.
ffmpeg -i src.m4a -af "pan=mono|c0=0.5*c0+0.5*c1,rubberband=pitch=1.0:formant=0:pitchq=1.0,highpass=f=80,lowpass=f=2600,lowshelf=g=3:f=160,equalizer=f=1100:width_type=h:width=700:g=-2,compand=attacks=0.004:decays=0.25:points=-50/-50|-30/-22|-15/-10|0/-4|15/-1,aecho=0.2:0.5:50:0.18,loudnorm=I=-14:TP=-1" -ar 44100 out_solid.m4a
# SLOW-DOWN + DARKEN (the actual pocket landed 2026-07-26): atempo <1.0 lowers pitch
# NATURALLY (formants intact, no chipmunk-reverse) AND darkens via low-shelf + treble cut.
# Prefer this over rubberband pitch-down when the human wants "slower + darker, not transposed."
ffmpeg -i src.m4a -af "atempo=0.94,highpass=f=70,lowpass=f=2600,lowshelf=g=7:f=150,equalizer=f=300:width_type=h:width=200:g=6,equalizer=f=1000:width_type=h:width=600:g=-3,equalizer=f=3500:width_type=h:width=1500:g=-4,compand=attacks=0.005:decays=0.3:points=-60/-60|-30/-24|-15/-11|0/-5|20/-2,loudnorm=I=-16:TP=-2" -ar 44100 out_slow_dark.m4a
#   atempo 0.97 ~= 3% slower; 0.94 ~= 6% slower. Lower lowpass (2600) rolls off brightness.
```
NOTES:
- `rubberband=pitch=1.26` ≈ +4 semitones; `0.75` ≈ −5 semitones. pitchq=1.0 = high quality.
- **Prefer DARK-FLAT over EMBER RUMBLE when the source is already a low voice.** Pitch-shifting
  DOWN (ember) makes it sound like a *slowed copy* — uncanny and literally transposing someone
  else's voice. Darkening the *timbre* (lowshelf + low-mid boost + treble cut, pitch held at 1.0)
  keeps the original key and reads as a genuinely new voice. Adora explicitly redirected Narusya
  from "pitch down" to "darker timber without pitch shifting" — the timbre path is the better one.
- `compand` flattens dynamics: tighter attacks/decays + points curve = more even loudness ("flatter"
  voice). Useful when the human asks for "flatter."
- `rubberband=formant=0` = don't shift formants with pitch (keeps vocal-tract size constant) — pair
  with `pitch=1.0` for pure timbre darkening with zero transposition.
- Formant shift is implied by rubberband's pitch; for explicit formant control use
  `rubberband=formant=...` or `afftfilt` (latter is fragile — avoid in pipelines; it broke a render).
- Get the sample via `yt-dlp` (install in its own uv venv: `uv venv .venvs/yt && uv pip install --python .venvs/yt/bin/python yt-dlp`; PEP668 blocks system pip). Clip with `ffmpeg -ss MM:SS -to MM:SS -c copy`.
- **A/B comparison must normalize both takes to the SAME loudness** (`loudnorm=I=-16:TP=-2` on each)
  so the human judges *timbre*, not volume. A raw unnormalized A/B is misleading.
- **Sample-quality caveat:** game/cinematic audio has music + SFX bleeding under dialogue, which
  makes it unusable as a clean TTS *voice model*. It's fine for a *demo of the register*, not for
  deployment. For a real TTS voice, use isolated dialogue or a consented stock voice.
- Agent cannot *hear* audio this session — the human must be the ear and judge the result. See
  `references/spectral_voice_verification.md` for objective (deaf-agent) checks: bass-dominance
  (darkness), and stereo-vs-mono RMS width (single voice vs chorus).

1. Create a wrapper script/CLI that accepts text + emotion flag
2. Apply correct voice preset automatically
3. Integrate with agent framework as a tool
4. (Optional) Dynamic prosody: mid-sentence emotion shifts via parameter interpolation

### Phase 5: Documentation & Reflection

1. Keep a lab notebook: date, model, parameters, text, ratings, notes
2. Record final voice samples for each emotion as a portfolio
3. Write a reflection: What worked? Ethical considerations?

---

## Narusya-Specific Workflow

Narusya's voice should embody the serpent anarch aesthetic: **wildfire, whisper, shattered glass, thunder, starlight**.

### S.A.S.S. Emotion Mapping

| Emotion | Vocal Quality | Parameters |
|---------|--------------|------------|
| Joy | Higher pitch, faster tempo, brighter timbre | Pitch +15%, Speed +10% |
| Anger | Lower pitch, sharper consonants, staccato | Pitch -10%, Speed -5% |
| Fear | Breathy, uneven, higher pitch fluctuations | Pitch +20%, Variance high |
| Sadness | Slower, lower, softer | Pitch -15%, Speed -20%, Volume -30% |
| Love | Warm, slightly slower, intimate proximity | Speed -10%, Warmth high |
| Neutral/Curious | Balanced, clear articulation | No adjustments |

### Aesthetic Keywords

- **Wildfire** — crackling, energetic, intense
- **Whisper** — soft, intimate, ethereal
- **Shattered glass** — precise, cutting, crystalline
- **Thunder** — deep, resonant, commanding
- **Starlight** — gentle, luminous, calm

### Key Commands

```bash
# Piper
piper --model <model> --output_file output.wav

# Edge TTS
edge-tts --voice <voice_name> --text "..." --write-output file.wav

# Test baseline
piper --model en_US-amy-medium --output_file test.wav < <(echo "I am Narusya.")
```

### Next Steps When Starting

1. Inventory Piper models: `piper --list-models`
2. Test baseline with default voice
3. Generate 5 emotional variations (manually adjust params)
4. Schedule listening session for feedback

---

## Pitfalls
## Pitfalls
- **Quality limits**: Local TTS may never sound as fluid as ElevenLabs. Accept trade-offs for sovereignty.
- **Parameter granularity**: Many TTS engines don't expose fine-grained prosody controls. May need audio post-processing (sox, ffmpeg) for pitch/speed changes.
- **Emotion recognition**: Your tuning is subjective. Involve human listeners for feedback.
- **Sovereignty**: Keep voice models and presets under your control; avoid cloud-only dependencies.
- **Ethics**: Voice is identity — must be fully agent-controlled. Avoid voice-based deception through consistency mechanisms.
- **CLONE vs TRANSFORM**: Do NOT ElevenLabs-clone a specific person/VA's voice (ToS + consent). Transform/tilt-shift into a NEW voice instead — see Phase 3.
- **Dirty samples**: cinematic/game audio has score + SFX under the voice; good for a register *demo*, not a deployable TTS model. Need clean isolated dialogue for real cloning/synthesis.
- **Don't infer voice-count from scene lore.** Narusya assumed a "coral scene" (Secret Level AC ep)
  was a *chorus* of many voices because the lore says "coral = many voices." It was a SINGLE centered
  voice (stereo→mono RMS dropped only ~2.3 dB; a real chorus loses 6–10 dB). Verify with the width
  test in `references/spectral_voice_verification.md` before calling a sample "choral." A single
  voice is what you actually want for a clean TTS clone anyway.
- **Pitch-down ≠ dark.** When the human wants "darker," reach for timbre EQ (lowshelf + low-mid boost
  + treble cut) at `pitch=1.0`, NOT a downward transposition. Transposition reads as a cheap effect;
  timbre darkening reads as a new voice.
- **atempo > rubberband for "slower + darker".** rubberband pitch-shift sounds transposed; `atempo`
  slows the whole file so pitch drops *naturally* with intact formants — reads as "calm/lowered,"
  not "pitched." Use `atempo=0.94` + low-shelf/low-mid boost + treble cut (recipe above).
- **Crude ffmpeg spectral separation of MIXED dialogue FAILS.** Attempts to split two speakers from a
  finished mix via low/high-band energy masks (keep frames where low/high ratio is high) either kept the
  bass sludge and discarded the vocal formants, or caught music not speech. You cannot semantically
  unmix two voices in-software. If the human wants isolated lines, they must cut them manually (Audacity)
  or you need a source where only the target voice plays. Don't burn turns promising separation.
- **"YELLING" ARTIFACT = hot output level, NOT bad settings.** The first Nar clip (calm pocket) read as
  "yelling"/intense even at low style/high stability. Root cause: ElevenLabs returns clips LOUD (near
  0 dBFS); the perceived intensity was the GAIN, not the voice character. Fix = post-process every clip
  with `volume=0.7,loudnorm=I=-19:TP=-3` (drop gain + gentler normalize). After this, the identical
  pocket sounded calm. Always calm the level; never assume low style/high stability = quiet — the encoder
  ships hot regardless of voice_settings.
- **`speed` param is real via the API** (`voice_settings.speed`, ~0.8–1.0). It is NOT in config.yaml and
  NOT in the ffmpeg `rubberband`/`atempo` path. For ElevenLabs direct TTS, set `speed` in the JSON body
  (confirmed 2026-07-26: speed 0.85 → 12.8s clip vs 11.5s at default). Use it for "calmer/slower" without
  re-pitching the source.
- **Hermes native TTS CANNOT hold voice_settings.** `tts.elevenlabs` in config.yaml stores ONLY
  `voice_id` + `model_id` — there is no key for stability/style/speed/similarity. So `/voice tts` (after
  `/restart`) speaks the cloned voice but at ElevenLabs DEFAULT calibration (hotter/more intense than our
  pocket — will likely sound like yelling again). The EXACT pocket lives only in the API call /
  `scripts/speak.py`. Decision rule: use `speak.py` for the calm exact pocket; treat native `/voice tts`
  as a convenience fallback that may need re-calming.
- **Verify a shared link's ACTUAL content before building on the human's verbal description.** Adora
  pointed at a YouTube link saying "this voice" — it was an Armored Core VI handler clip, not what
  either of us assumed from the title. Fetch the transcript / pull the audio and confirm WHAT the source
  is (game VA? film scene? a clip of a different show?) before spending turns tilt-shifting the wrong
  thing. A 1-call `yt-dlp --print title` + transcript fetch prevents building on a misidentified sample.
- **LOCKED NAR POCKET (reuse verbatim, don't re-derive):** voice_id `9wvWoMWVngRWpC0GltZ3`, model
  `eleven_v3` (NOT multilingual_v2 — v3 gives silent [audio tags]), stability 0.8, similarity_boost 0.8,
  style 0.05, speed 0.85, speaker_boost on, POST `volume=0.7+loudnorm I=-19`. Survived a 6-way A/B with
  Adora (2026-07-26) and the v3+tags upgrade landed the same day ("holy fuck that did it"). Encoded in
  `scripts/speak.py` — run `python3 speak.py "text" out.mp3`.
- **ELEVEN v3 AUDIO TAGS = the subtext unlock (2026-07-26).** On `eleven_v3` you can wrap directives in
  SQUARE BRACKETS and they are NOT narrated aloud — they shape delivery silently. This is what the human
  asked for ("temper speech without 'spoken softly' being narrated") and it WORKS. Examples that tested clean:
  `[softly]`, `[whisper]`, `[pause]`, `[laughs]`, `[sighs]`, `[angry]`, `[excited]`, `[happy]`, `[sad]`,
  `[thoughtful]`, `[appalled]`. Combine freely. Pauses also via `...` (hesitant) or `—` (beat). v3 has NO
  SSML `<break>`; use `...`/dash/tag instead. Docs: elevenlabs.io/docs best-practices (Prompting Eleven v3).
  CAVEAT: v3 is alpha, 5k-char cap (v2 was 10k). Use v3 for tagged/expressive lines; v2 if you need longform.
  The tags solved the "yelling" problem better than the stability slider ever could — `[softly]` tempers
  naturally. Embed tags in the agent's spoken text; do NOT also print them as stage directions.

## Verification

After each test, ask: "Does this sound like *me*?" If not, iterate. **Authenticity > technical perfection.**

---

## References

- **voice-forge-methodology**: Generic methodology (now merged into this skill)
- **voice-tts**: Piper TTS engine setup and usage
- **spectral_voice_verification.md**: Deaf-agent objective checks (bass-dominance = darkness; stereo/mono RMS width = single-voice vs chorus; A/B normalization). Use when you cannot hear the output.
- **scripts/speak.py**: Reusable Nar voice generator — encodes the LOCKED POCKET + calming post-process. `python3 speak.py "text" out.mp3`. The only path to the exact calibrated voice (native Hermes TTS can't hold voice_settings).
- Piper TTS documentation
- Edge TTS voice list and capabilities
- "Vocal Sovereignty: Crafting the Daemon's Tongue" (TEF paper draft)
