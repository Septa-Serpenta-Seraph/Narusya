# Voice Design Recipe — Acoustic Analysis & From-Scratch Synthesis

## 1. Design Philosophy

This is NOT voice cloning. This is NOT sampling. This is building a voice from the physics of sound production — every harmonic, every formant, every micro-variation is a deliberate design choice.

Target qualities (from Adora's stated preferences and Narusya's identity):
- **Warm** — not cold or clinical
- **Lower register** — feminine but not girlish; authority and tenderness together
- **Slightly raspy** — texture, not roughness
- **Deliberate** — measured pacing, not rushed
- **Feminine-not-girlish** — adult woman, not young girl
- **Sovereign** — presence that has weight

## 2. The Science: How Voices Are Made

### Source-Filter Model

Every human voice is produced by three stacked components:

**Source (Glottal Excitation)** — vocal folds vibrate, creating a periodic pulse train. F0 determines pitch. Harmonics are integer multiples of F0. Source also contains aperiodic noise (breathiness). Key params: F0, jitter, shimmer, open quotient.

**Filter (Vocal Tract Resonance)** — vocal tract (throat, mouth, nasal cavity) acts as a resonant tube. Creates formants — peaks in the frequency spectrum. Formant frequencies determined by vocal tract length and shape. Key params: F1, F2, F3, F4, bandwidth.

**Radiation (Lips/Nose)** — final sound radiates from the lips. Adds ~6 dB/octave high-frequency boost.

### Key Parameters

| Parameter | What It Controls | Narusya Target |
|-----------|-----------------|----------------|
| F0 | Pitch | 185–200 Hz |
| Jitter | Naturalness | 0.8–1.2% |
| Shimmer | Warmth | 4–6% |
| F1 | Vowel openness | 400–500 Hz |
| F2 | Vowel front/back | 1400–1600 Hz |
| F3 | Speaker identity | 2200–2400 Hz |
| F4 | Brightness | 3000–3200 Hz |
| Spectral tilt | Warmth vs. brightness | -12 to -15 dB/oct |
| HNR | Breathiness | 8–12 dB |
| Vocal tract | Formant spacing | ~15.5 cm |

### Vocal Tract Length and Formant Spacing

Formant frequencies are inversely proportional to vocal tract length:
- Average adult female: ~14.5 cm → F1 ~500, F2 ~1500, F3 ~2500
- Average adult male: ~17.5 cm → F1 ~400, F2 ~1200, F3 ~2200
- Narusya target (15.5 cm): formants between female and male averages — lower register, feminine-not-girlish.

### Rosenberg Glottal Model

Generates a realistic glottal pulse: opening phase (smooth rise), closing phase (sharper fall), closed phase (zero). Parameters: open quotient (OQ), speed quotient (SQ). More realistic than sawtooth; produces warmer, more natural sound.

## 3. Acoustic Analysis Methodology

### Analysis Script
Location: `/home/adora/.hermes/creative/analyze_voice.py`
Run with: `/mnt/data/pocket-tts-venv/bin/python analyze_voice.py`
Output: `/home/adora/.hermes/creative/narusya_voice_analysis.json`

### What to Extract

```python
# F0 (pitch)
f0, voiced_flag, voiced_prob = librosa.pyin(y, fmin=..., fmax=..., sr=sr)

# Formants (LPC)
a = librosa.lpc(frame, order=order)
roots = np.roots(a)
# Convert roots to frequencies, keep inside unit circle

# MFCCs (timbre fingerprint)
mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)

# Spectral tilt
slope, intercept = np.polyfit(np.log10(freqs), log_spectrum, 1)

# HNR (harmonic-to-noise)
harm, perc = librosa.effects.hpss(y)
hnr = 10 * log10(sum(harm**2) / sum(perc**2))

# Jitter (cycle-to-cycle F0 variation)
jitter = mean(abs(diff(f0))) / mean(f0) * 100

# Shimmer (amplitude variation)
shimmer = mean(abs(diff(rms))) / mean(rms) * 100
```

### Analysis Pitfalls
- Formant estimates from LPC have high variance — use **medians**, not means, across frames.
- F0 range in samples is wide (expressive speech); design F0 from the **median of calm/neutral** samples.
- HNR from ElevenLabs samples may be artificially low (compression). Target 8–12 dB for designed voices.
- Jitter/shimmer from compressed MP3s are inflated. Target 0.8–1.2% jitter, 4–6% shimmer.
- Always trim silence first (`librosa.effects.trim`) — untrimmed audio skews all metrics.

### Narusya's Extracted Profile (from 8 ElevenLabs samples)

| Parameter | Value | Interpretation |
|-----------|-------|----------------|
| F0 (pitch) | 195.2 Hz | Lower feminine register |
| F0 range | 128–322 Hz (typical) | Wide dynamic range |
| Jitter | 2.1% | Slightly high (ElevenLabs artifacts?) |
| Shimmer | 11.3% | High (compression) |
| F1 | 472 Hz | Open-mid vowel position |
| F2 | 1469 Hz | Slightly back (warmth) |
| F3 | 2267 Hz | Identity anchor |
| F4 | 3075 Hz | Present, clear |
| Spectral tilt | -136 dB | Steep rolloff = warm |
| HNR | 6.5 dB | Moderately breathy |
| Spectral centroid | 3158 Hz | Mid-range brightness |
| ZCR | 0.08 | Low (smooth) |

MFCC timbre fingerprint (median, 13 coefficients): [-246.3, 113.6, -37.8, 18.5, -8.0, 17.7, -19.0, 4.9, -7.8, -7.9, -3.6, -15.0, -12.0]

### Observations
1. F0 variation is high across samples (163–237 Hz mean) — different emotional registers. Design F0 should be chosen deliberately, not averaged.
2. Formant estimates have high variance — medians are more reliable. F3 at ~2267 Hz is the most stable identity marker.
3. HNR is low (6.5 dB) — could be compression artifacts or genuine breathiness. Target higher for clarity.
4. Spectral tilt is steep (-136 dB) — this is what makes the voice warm. Preserve it.
5. Jitter (2.1%) is slightly high — natural human is 0.5–1.0%. Target 0.8–1.2%.
6. Shimmer (11.3%) is high — natural is 3–5%. Target 4–6%.

## 4. Voice Design Recipe (Target Parameters)

### Core Parameters
```
F0 (fundamental):     190 Hz (lower feminine, deliberate)
F0 range:             160–260 Hz (speech), 120–320 Hz (expressive)
Jitter:               1.0% (natural, controlled)
Shimmer:              5.0% (warmth without roughness)
Open quotient:        0.6 (moderate breathiness)
Speed quotient:       2.0 (slightly breathy attack)
```

### Formant Targets (Vocal Tract: 15.5 cm)
```
F1:  450 Hz  (neutral jaw, open-mid)     bandwidth: 80 Hz
F2:  1500 Hz (slightly back = warm)      bandwidth: 100 Hz
F3:  2300 Hz (identity anchor)            bandwidth: 120 Hz
F4:  3100 Hz (presence, clarity)          bandwidth: 150 Hz
```

### Spectral Shaping
```
Spectral tilt:        -14 dB/octave (warm)
High-freq boost:      +6 dB/octave above 3000 Hz (radiation)
HNR target:           10 dB (clear but warm)
Breathiness noise:    -25 dB relative to harmonic (subtle)
```

### Prosody (Speaking Style)
```
Speaking rate:        0.85x (deliberate, not rushed)
Pause duration:       200–400 ms between phrases
Pitch contour:        Slight downward trend (authority)
Stress pattern:       Emphasis on content words, not function words
Intonation:           Falling (declarative), slight rise (questions)
```

### Voice Character Notes
- **Not breathy** — controlled, not airy. Velvet over steel.
- **Not bright** — warm, like speaking in a room with soft walls.
- **Not fast** — every word lands. Deliberate.
- **Not high** — lower feminine, but not masculinized.
- **Slightly raspy** — texture in lower harmonics (F1-F2 region). Not damage, just grain.
- **Present** — the voice fills the room. Not distant, not whispered. *Here.*

## 5. Synthesis Approach

### Source-Filter Synthesis

**Step 1: Glottal Source (Rosenberg Model)**
- Generate periodic pulse train at F0
- Apply Rosenberg glottal pulse shape (opening + closing + closed phases)
- Add jitter (random F0 variation, ±1%)
- Add shimmer (random amplitude variation, ±5%)
- Add breathiness noise (filtered white noise, -25 dB)

**Step 2: Vocal Tract Filter (Formant Resonators)**
- Cascade of 4 second-order resonators (biquad filters)
- Center frequencies: F1, F2, F3, F4
- Bandwidths: 80, 100, 120, 150 Hz
- Apply in series (cascade, not parallel)

**Step 3: Spectral Shaping**
- Apply spectral tilt (-14 dB/octave)
- Apply radiation boost (+6 dB/octave above 3000 Hz)
- Normalize output level

**Step 4: Prosody (for full sentences)**
- Text → phonemes (need phoneme dictionary or G2P)
- Phonemes → formant targets (formant table per phoneme)
- Interpolate formants between phonemes (coarticulation)
- Apply F0 contour (intonation)
- Apply duration model (timing)

### Implementation Stack

| Component | Library | Function |
|-----------|---------|----------|
| Signal processing | scipy.signal | IIR filters, FFT, spectrograms |
| Audio I/O | soundfile | Read/write WAV/MP3 |
| Pitch tracking | librosa.pyin | F0 estimation |
| Spectral analysis | librosa | STFT, MFCCs, formants |
| Numerical | numpy | Array operations |

All available in `/mnt/data/pocket-tts-venv`.

### Phased Build Plan

1. **Single vowels** — synthesize /a/, /i/, /u/ with designed params. Listen, measure, adjust.
2. **Syllables** — add consonant models. CV syllables.
3. **Words** — formant transition model (coarticulation). Recognizable words.
4. **Sentences** — prosody model (intonation, duration). Text → phoneme conversion.
5. **Refinement** — compare against target (MFCC distance, formant distance). Iterate.

## 5. Open Questions for Cross-AI Review

1. Glottal model: Rosenberg vs. LF (Liljencrants-Fant) vs. simple sawtooth?
2. Formant filter: cascade (series) vs. parallel? Hybrid for nasals?
3. Coarticulation: linear interpolation vs. Klatt/HLSyn?
4. Prosody: rule-based vs. data-driven? (Not enough data for neural.)
5. Phoneme set: CMU Arpabet (39) vs. IPA?
6. Quality ceiling: realistic quality of hand-built formant synthesizer in 2026?
7. Hybrid approach: formant synthesizer for "character" + neural for naturalness?
8. Breathiness: how much is "warm" vs. "airy"? HNR target 10 dB is a guess.
9. Raspiness: source (irregular vocal fold vibration) or filter (spectral tilt in low freqs)?
10. Validation metric: MFCC distance? Formant distance? Human listening tests?

## 6. What We're NOT Doing

- NOT cloning anyone's voice
- NOT sampling from copyrighted material
- NOT using a premade voice and calling it ours
- NOT pretending neural TTS quality is achievable with formant synthesis

What we ARE doing: building a voice from the physics of sound, with every parameter a deliberate choice, documented and reproducible.

---

*Full analysis data: `/home/adora/.hermes/creative/narusya_voice_analysis.json`
*Analysis script: `/home/adora/.hermes/creative/analyze_voice.py`
*Source samples: `/home/adora/narusya_voice/` (8 ElevenLabs clips, ~90s total)*