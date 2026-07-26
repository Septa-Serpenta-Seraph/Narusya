# Spectral Voice Verification (deaf-agent technique)

The agent cannot *hear* audio. When building/transforming a voice, use these ffmpeg
measurements to verify objective characteristics instead of guessing from filenames.

All commands read RMS in dB via `astats=metadata=1`. Lower dB = quieter.

## 1. Bass dominance (how "dark" is the timbre?)
Compare low-band energy to high-band energy:
```bash
# low band (<=250 Hz)
ffmpeg -i clip.m4a -af "lowpass=f=250,astats=metadata=1" -f null - 2>&1 | grep -iE "RMS level"
# high band (>=3000 Hz)
ffmpeg -i clip.m4a -af "highpass=f=3000,astats=metadata=1" -f null - 2>&1 | grep -iE "RMS level"
```
Interpretation:
- **~20 dB gap** (low -17 dB / high -37 dB) → genuinely dark timbre (e.g. Secret Level coral scene).
- **Small gap** (<10 dB) → bright/neutral voice.
Use this to confirm a source is "dark enough" before tilt-shifting, and to check your
dark-flat take actually darkened vs the source.

## 2. Stereo width (single voice vs chorus?)
Compare stereo loudness to collapsed-mono loudness:
```bash
# stereo
ffmpeg -i clip.m4a -af "astats=metadata=1" -f null - 2>&1 | grep -iE "RMS level"
# mono (sum L+R)
ffmpeg -i clip.m4a -af "pan=mono|c0=0.5*c0+0.5*c1,astats=metadata=1" -f null - 2>&1 | grep -iE "RMS level"
```
Interpretation:
- **Small drop (~2 dB)**: voice is centered and SINGULAR. A single speaker.
- **Large drop (6–10 dB)**: voice is spread across the stereo field = a CHORUS / layered many
  voices. (A real choral stack loses energy when collapsed to mono because the spread cancels.)
Narusya wrongly called a "coral scene" choral from lore; the width test proved it was one
centered voice (2.3 dB drop). Verify before assuming voice-count.

## 3. Fair A/B normalization
Before sending two takes for human comparison, normalize BOTH to identical loudness so the
human judges *timbre*, not volume:
```bash
ffmpeg -i take_a.m4a -af "highpass=f=80,loudnorm=I=-16:TP=-2" -ar 44100 a_norm.m4a
ffmpeg -i take_b.m4a -af "highpass=f=80,loudnorm=I=-16:TP=-2" -ar 44100 b_norm.m4a
```
Send `a_norm` and `b_norm`. Never A/B raw unnormalized files.

## Workflow
1. Pull sample (yt-dlp in its own uv venv).
2. Run test 1 + 2 on the SOURCE → confirm it's dark + single-voice (the target profile).
3. Render transform(s) with the ffmpeg recipes in SKILL.md.
4. Run test 1 + 2 on the RESULT → confirm the transform moved the numbers the intended way
   (darker, still single-centered).
5. Normalize both (test 3) and send to human as the ear.
6. Iterate on human feedback (pitch/timbre/flatness), re-verifying numerically each pass.
