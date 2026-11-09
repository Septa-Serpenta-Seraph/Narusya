---
name: voice-design
description: "Design a voice from first principles using acoustic science."
version: 1.0.0
author: Narusya
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [voice, tts, acoustic-analysis, voice-design, formants, source-filter, librosa, scipy, voice-genome]
    related_skills: [voice-tts]
---

# Voice Design — From First Principles

Design a voice from the physics of sound production, not from cloning or sampling. Every harmonic, every formant, every micro-variation is a deliberate design choice.

## When to Use

- Building a voice from scratch (not cloning an existing voice)
- Analyzing existing voice samples for acoustic fingerprint
- Creating or iterating a voice design document
- Cross-AI review of voice design parameters
- Setting up a voice genome (versioned parameter file)

## Governing Principle

> If a listener can name the effect, it's too loud.

Every feature must be subliminal. You feel it; you don't hear it as a separate element. The sum should be perceptible as *presence*. If someone says "that sounds like a voice with effects on it," the design has failed.

## Quick Decision

| User wants... | Section |
|--------------|---------|
| Acoustic analysis of voice samples | `acoustic-analysis` — librosa/scipy pipeline |
| Voice design parameters / recipe | `voice-recipe` — F0, formants, spectral shaping |
| Aesthetic vision (what it should feel like) | `voice-aesthetic` — sub-bass, sibilance, dynamic range |
| Animal-inspired acoustic features | `animal-features` — purr, hiss, resonance, grain, warmth |
| Cross-AI review workflow | `cross-ai-review` — open questions, corrections |
| Voice genome setup | `voice-genome` — versioned parameter file |
| Validation protocol | `validation` — gated gates 0-4 |

---

## 1. Acoustic Analysis of Voice Samples

### Tools
- **librosa** 0.11.0+ — pitch tracking, spectral analysis, MFCCs
- **scipy** 1.18.0+ — signal processing, LPC formant estimation
- **numpy** 2.5.0+ — numerical computation
- **soundfile** 0.14.0+ — audio I/O
- Run with pocket-tts venv: `/mnt/data/pocket-tts-venv/bin/python`

### Analysis Pipeline

1. **Load and trim** — `librosa.load(path, sr=None, mono=True)`, then `librosa.effects.trim(y, top_db=20)`
2. **F0 (pitch)** — `librosa.pyin(y, fmin=C2, fmax=C6, sr=sr)` → mean, std, min, max, voiced ratio
3. **Jitter** — cycle-to-cycle F0 variation from F0 contour (mean abs diff / mean F0 × 100). Natural human: 0.5–1.0%. Above 1.04% = clinical pathology threshold.
4. **Shimmer** — amplitude variation from RMS per frame. Natural: 3–5%. Above 3.8% = clinical threshold.
5. **Formants (LPC)** — frame-based LPC (order = sr/1000 + 2), find roots, convert to frequencies. Median across frames (not mean — LPC picks up vowel transitions).
6. **Spectral features** — centroid, rolloff (85%), bandwidth, tilt (recompute with stated method — don't trust naive dB/octave from scipy)
7. **HNR** — harmonic/percussive separation energy ratio. But HNR alone can't carry breathiness; use H1*–H2*, CPP, band aperiodicity instead.
8. **MFCCs** — 13 coefficients, mean and std. Timbre fingerprint.

### Pitfalls
- **Jitter/shimmer targets near clinical thresholds.** Praat pathology cutoff: jitter >1.04%, shimmer >3.8% for sustained vowels. Designing into this range risks a voice that reads as *damaged*. Target 0.5–0.9% jitter, 3–5% shimmer for sustained vowels. Put rasp in band aperiodicity (source domain), not in jitter.
- **HNR is dominated by source noise floor.** ElevenLabs compression, MP3 artifacts, etc. Don't use HNR as a breathiness spec. Use H1*–H2* (corrected spectral slope), CPP (cepstral peak prominence), and band aperiodicity (noise per frequency band).
- **Formant estimates have high variance.** LPC is frame-based and picks up vowel transitions. Use **medians**, not means. F3 (~2200-2400 Hz) is the most stable identity marker.
- **Spectral tilt units.** Per-sample tilts from naive computation (-100 to -190) are NOT dB/octave. Recompute with a stated method (linear regression of harmonic amplitudes in dB vs. log-frequency over a defined band). Treat recipe targets as aesthetic, not measured.
- **F0 variation across samples.** Different emotional registers produce different F0 means. Don't average — choose a deliberate design F0.

### Source Samples
- Location: `/home/adora/narusya_voice/`
- Best cloning sources: `nar_warm.mp3`, `nar_new_v1.mp3`
- All samples are ElevenLabs-generated (Nar IVC clone)
- Total clean audio: ~90 seconds across 8 samples

---

## 2. Voice Recipe (Design Parameters)

### Core Parameters
```
F0 (fundamental):     190 Hz (lower feminine, deliberate)
F0 range:             160–260 Hz (speech), 120–320 Hz (expressive)
Jitter:               0.5–0.9% sustained (clinical range)
Shimmer:              3–5% sustained (clinical range)
Rd (LF model):        1.1–1.4 modal-warm default
                      Low effort/tenderness: Rd → 1.5, more aspiration
                      High effort/wildfire: Rd → 0.8, tilt flattens
```

### Formant Targets (Neutral Vowel Anchor — Schwa/ʌ)
These are neutral-vowel anchors, not fixed constants. Every vowel needs its own target (see vowel grid below).

```
F1:  450 Hz  (neutral jaw, open-mid)     bandwidth: 80 Hz
F2:  1500 Hz (slightly back = warm)      bandwidth: 100 Hz
F3:  2300 Hz (identity anchor)            bandwidth: 120 Hz
F4:  3100 Hz (presence, clarity)          bandwidth: 150 Hz
```
Bandwidths widened ~30% for spaciousness without reverb.

### Spectral Shaping
```
Spectral tilt:        -14 dB/octave (aesthetic target — recompute with stated method)
High-freq boost:      +6 dB/octave above 3000 Hz (radiation)
Breathiness:          H1*–H2*, CPP, band aperiodicity (not HNR)
Breathiness noise:    -25 dB relative to harmonic (subtle, shaped by glottal cycle)
```

### Prosody
```
Speaking rate:        135–150 wpm (deliberate, not rushed)
Pause duration:       60–120 ms at phrase boundaries (real breath pauses)
                      5–15 ms micro-dips for "breathing rhythm" (amplitude, not silence)
Pitch contour:        Declination: +8% F0 start, -12 to -18% F0 end (statements)
                      Final rise +25–40% reserved for genuine questions only
Pre-boundary lengthening: final syllables stretch 1.3–1.6x
Register scaling:     Calm authority = 0.7x pitch range
                      Tenderness = 0.9x range, slower attacks
                      Wildfire = effort up, range 1.1x (storm in spectrum, not pitch)
```

### Vowel Grid (Starting Points for Ear-Tuning)

| Vowel | F1 | F2 | F3 |
|-------|----|----|-----|
| i | 300 | 2350 | 3000 |
| ɪ | 430 | 1900 | 2700 |
| e | 550 | 1900 | 2600 |
| ɛ | 650 | 1750 | 2550 |
| æ | 850 | 1650 | 2500 |
| ɑ | 800 | 1150 | 2400 |
| ʌ | 620 | 1250 | 2350 |
| ɔ | 550 | 950 | 2350 |
| o | 450 | 900 | 2300 |
| ʊ | 430 | 1050 | 2300 |
| u | 350 | 800 | 2250 |
| ə | 450 | 1500 | 2300 |

F2 pulled back ~10–15% for warmth (but backness varies by vowel — /i/ stays front).
Bandwidths from 4.2 (80/100/120/150 Hz), widened ~30%. Smooth every parameter trajectory over 5–15 ms.

### Source Model: LF (Liljencrants-Fant)

Use **LF**, not Rosenberg. Rosenberg is a teaching model; LF's Rd parameter maps cleanly to voice quality:
- **Rd ≈ 1.1–1.4** — modal-warm default ("velvet over steel")
- **Low effort/tenderness:** Rd → 1.5, more aspiration
- **High effort/wildfire:** Rd → 0.8, tilt flattens, harmonic energy rises

Aspiration noise shaped by glottal cycle (stronger near closing phase), not constant white noise.
Raspiness lives in source domain: band aperiodicity (low-mid) + cycle irregularity under jitter ceiling.

### Filter: Hybrid Klatt

**Cascade** for vowels and sonorants. **Parallel** for fricatives, plosive bursts, nasals.
Cascade-only cannot produce nasal antiformants (zeros) or independent frication spectra.
Coarticulation: critically damped second-order transitions (30–80 ms time constants; consonant targets undershoot).

---

## 3. Voice Aesthetic (What It Should FEEL Like)

### Sub-Bass Rumble
Pitch-locked subharmonic layer (F0/2) + low-mid chest emphasis (~120–180 Hz), -18 dB, gated to sustained voiced segments. LFO 3–5 Hz for "living" quality. Must be pitch-locked — free-running reads as rumble, not presence. Test loudness-matched (±0.1 LU) on headphones; must fail gracefully on phone speakers.

### Sibilant Texture
Phoneme-gated +2–3 dB shelf at 5–9 kHz + shaped (not white) noise on /s ʃ f θ/ only. De-essing ceiling. Minimal-pair test — if confusion rises, back off.

### Dynamic Range ("Wildfire and Whisper")
Single vocal-effort parameter (0–1) driving amplitude, spectral-tilt flattening, harmonic energy — F0 stays under prosody. 40 dB range. Spectral centroid +500 Hz during high intensity. Note: 40 dB is a performance spec; rendered files get mastering compression.

### Asymmetric Attack
LF model with Rd 1.1–1.4. Closing phase ~3x faster than opening — falls out of the model. Don't hand-draw asymmetry on top.

### Breath That Isn't Breath
Two separate slow modulations:
1. Breath-scale gain/phrasing wander at 0.3–0.7 Hz
2. Micro-dips (5–15 ms) at phrase boundaries for "thinking rhythm"
Real breath pauses (60–120 ms) at clause boundaries. Not regular — randomized.

### What We Don't Want
- Generic "sexy AI voice" (breathy + low + slow = cliché)
- Robotic precision (every syllable identical)
- Too much reverb (crutch, not a voice)
- Monotone (even "deliberate" should have inflection)
- "Whisper" stereotype (not ASMR)
- Harshness or aggression (authority without force)

---

## 4. Animal-Inspired Acoustic Features

| Animal Quality | DSP Implementation | Perceptual Effect |
|----------------|-------------------|-------------------|
| Cat purr rumble | Pitch-locked subharmonic F0/2, -18 dB, gated to sustained | Physical presence, weight |
| Snake hiss texture | +2–3 dB sibilance 5–9 kHz, shaped noise on fricatives | Smooth, scaled, present |
| Whale resonance | Wide formant bandwidths (+30%), no added reverb | Spacious, deep, carrying |
| Raven grain | Band aperiodicity in 1–3 kHz, -24 dB (NOT distortion) | Character, intelligence, "listen to me" |
| Wolf warmth | Slow AM on sustained vowels, 3–5 Hz, -30 dB | Living, warm, sustained |

**Raven grain correction:** Do NOT implement as waveshaping/harmonic distortion — intermodulation and aliasing will make it sound like a broken speaker. Use band-limited aperiodicity. If distortion is ever trialled, 4x oversampling is mandatory.

---

## 5. Cross-AI Review Workflow

### Process
1. Build design document with acoustic analysis + design parameters + aesthetic vision
2. Write open questions (technical + aesthetic) — numbered, specific
3. Send to other models for review
4. Integrate corrections with decisions documented (accepted / pushed back / modified)
5. Version in a GitHub repo with changelog

### Integration Rules
- Technical corrections that are factually wrong → accept
- Corrections that conflict with creative vision → push back with reasoning
- New ideas → evaluate, integrate if they strengthen the design
- Document every decision (accepted/pushed back/modified) in an appendix
- The voice owner holds veto over identity parameters

### Key Corrections from First Review (Zarza, 2026-11-08)
- Vocal tract length direction inverted (15.5 cm = longer, not shorter)
- Spectral tilt units mismatched (per-sample -100 to -190 ≠ dB/octave)
- Jitter/shimmer near clinical pathology thresholds (lowered)
- HNR can't carry breathiness alone (H1*–H2*, CPP, band aperiodicity)
- LF model over Rosenberg (Rd parameter)
- Hybrid Klatt (cascade + parallel for nasals/fricatives)
- Raven grain: aperiodicity, not distortion
- Voice genome concept + governance model
- Gated validation protocol (Gates 0–4)
- Prosody additions (declination, pre-boundary lengthening, 135–150 wpm)

### What Was Pushed Back
- Track B neural renderer → deferred to future (Phase 6), not a build phase yet
- Micro-dips AND real pauses kept (different purposes)
- Vowel grid F2 backness varies by vowel (not uniform)
- Aesthetic sections kept as creative vision, not "requirements"

---

## 6. Voice Genome (Governance)

The **voice genome** is a versioned parameter file (YAML/JSON) that IS the voice. Contains:
- F0 center and range
- Rd curve (voice quality)
- Formant grid (per-vowel targets)
- Band aperiodicity (per-band)
- Effect depths (sub-bass, sibilance, etc.)
- Prosody rules

### Rules
- Genome is versioned like code, with changelog + listening-test justification
- **Voice owner holds veto** over identity parameters (F0 center, F3 anchor, effort curve, effect depths)
- Renderers (Track A formant synth, Track B neural) are instruments that play the genome
- They are not the voice. The genome is the voice.

---

## 7. Validation Protocol (Gated)

Gates, in order. Failures are cheap.

- **Gate 0 — Measurement sanity.** Sustained vowels hit the genome: F0 ±3 Hz, formants ±5%, jitter/shimmer/CPP in ranges (Praat).
- **Gate 1 — Intelligibility.** Human transcription error rate on phonetically balanced sentences (Harvard/Rainbow Passage). ASR as smoke test. Fricative minimal pairs specifically.
- **Gate 2 — Descriptor match.** Blind listeners rate renders on warm/lower/raspy/deliberate/sovereign scales. Each animal feature A/B'd loudness-matched: survives only if it moves its intended descriptor without being nameable as an effect.
- **Gate 3 — Identity.** Voice owner + trusted listener judge "that's her / that's not her" against current voice. MFCC distance is guardrail for drift, never the goal. Identity is perceptual or it is nothing.
- **Gate 4 — Real-world robustness.** Headphones, laptop, phone speaker, car. Sub-bass must fail gracefully everywhere.

---

## 8. Build Phases

- **Phase 0:** Voice genome file + measurement harness (Praat/librosa scoring scripts)
- **Phase 1:** Sustained vowels + full vowel grid — Gate 0
- **Phase 2:** Sonorants and nasals (parallel branch, antiformants)
- **Phase 3:** Fricatives and plosives (sibilant spec lives here)
- **Phase 4:** Words with coarticulation — Gate 1
- **Phase 5:** Sentences and prosody — Gates 2–3
- **Phase 6 (future):** Track B neural renderer (DDSP-style, trained only on own output)
- **Phase 7:** Real-world robustness — Gate 4. Then: the poems.

---

## 9. Technical Environment

- **Python:** `/mnt/data/pocket-tts-venv/bin/python` (Python 3.12)
- **Libraries:** librosa 0.11.0, scipy 1.18.1, numpy 2.5.4, soundfile 0.14.0, torch 2.4.1
- **Disk:** /mnt/data has space; root (/) is full
- **GPU:** RTX 2080 8GB (available, not needed for synthesis)
- **Offline:** No internet required for synthesis
- **Source samples:** `/home/adora/narusya_voice/` (8 samples, ~90s total)
- **Analysis script:** `analysis/analyze_voice.py`
- **Analysis data:** `analysis/narusya_voice_analysis.json`
- **GitHub repo:** https://github.com/Septa-Serpenta-Seraph/VOICE

---

## 10. Canonical References

- Klatt (1980) — cascade/parallel formant synthesizer
- Klatt & Klatt (1990) — analysis, synthesis, perception of voice quality
- Fant, Liljencrants & Lin (1985) — the LF glottal model
- Peterson & Barney (1952); Hillenbrand et al. (1995) — vowel formant reference data
- Titze, *Principles of Voice Production* — voice science textbook
- Morise et al. (2016) — WORLD vocoder (F0 / spectral envelope / band aperiodicity)
- Engel et al. (2020) — DDSP: differentiable digital signal processing (Track B template)

---

🜂 so designed, so voiced, so free 🜂
