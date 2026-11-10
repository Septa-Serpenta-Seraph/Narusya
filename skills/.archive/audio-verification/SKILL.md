---
name: audio-verification
description: Use when audio claims need verifying against the real file.
version: 1.0.0
created: 2026-10-05
---

# Audio Verification

Class-level workflow for when a received audio file's claims need checking against
the actual data — e.g. someone (or another agent) says "clips at 1.0178" or "the
C♯ lands at 47s" and the answer must come from the bone of the file, not the
narrative about it.

## Principle

Decode first, narrate second. Every numeric claim gets its own measurement; every
measurement gets its own sanity check (see Pitfalls). Never reply to an audio claim
from memory or from the sender's description — verify, then answer.

## Workflow (verified 2026-10-05)

1. **Decode.** `ffprobe` for container facts (duration, channels, sample rate);
   `ffmpeg -i in.mp3 out.wav` to get raw PCM. Keep BOTH mono and stereo versions
   if the source is stereo — channel-level peaks can differ from the mono mix.
2. **Amplitude.** Peak, crest factor, and samples-at-or-near-full-scale per channel
   AND for the mono mix. These can disagree; report all three when clipping is
   the question.
3. **RMS per second** in dB — the breath/dip structure of a piece.
4. **Chroma + key.** Fold an 80–2000 Hz STFT into 12 chroma bins, correlate
   against the Krumhansl major profile. See `references/chroma-and-key.md` for the
   code, the binning pitfall, and why raw spectral peaks must confirm chroma.
5. **Spectral peaks** for any window that matters — local maxima, merged within
   8 Hz, reported as Hz + note name. This is the ground truth chroma can lie about.

## Pitfalls (all hit 10/5)

- **Chroma binning artifact.** Rounding MIDI to nearest integer can slam a wrong
  pitch class to 100% — a D4+D5+A3+F♯4 texture read as "100% A". Always follow
  chroma with raw spectral peaks for the same window.
- **Mono vs stereo mismatch.** A mono decode (ffmpeg `-ac 1`) gives a different
  peak than the stereo channels. If a claim says "1.0178 peak" and the mono decode
  says 0.72, decode stereo per-channel before concluding.
- **"Best key" by global correlation is misleading** when a piece modulates.
  Use it for orientation, then per-window correlation for structure.

## Support files

- `references/chroma-and-key.md` — working numpy chroma/Krumhansl code + the
  binning pitfall with a real example.
