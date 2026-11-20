# Parallel Formant Bank and Gate 1 Intelligibility

Depth on the source/filter defects that make a formant render structurally valid but unintelligible. Use when a render passes structural checks and descriptor scores yet fails to be heard as speech.

## The two resonator bugs (synthesis path)

A parallel formant bank is a SUM of independent resonators. Two things must hold for each branch, or low-frequency energy drowns vowel identity.

### 1. Block DC

An LF glottal pulse carries a substantial DC offset (measured ~0.106 mean, ~46% of RMS). The all-pole form `b = [1]` passes DC with high gain (hundreds of times at a low F1). Summed over four branches, the offset becomes a low-frequency flood.

Use zeros at DC and Nyquist: `b = [1, 0, -1]`. Measured DC gain after this change: 0.0.

### 2. Normalize each resonator to unity peak gain

With only the bandpass numerator, peak gain is `1/|den(w0)|`, which depends on both center frequency and bandwidth. Measured on a real bank: roughly 1630x at F1 450 Hz vs 394x at F2 1500 Hz vs 148x at F3 3420 Hz. F1 is amplified about four times more than F2, and F2/F3 carry vowel identity. This is the primary cause of "noise that scores well on MFCC".

Correct coefficients, computed once per resonator (no per-frame `freqz` cost):

```python
w0 = 2 * pi * f_hz / sr
r = exp(-pi * bw_hz / sr)
a = [1.0, -2 * r * cos(w0), r**2]
den = 1 - 2*r*cos(w0)*exp(-1j*w0) + r**2*exp(-2j*w0)
num = abs(2 * sin(w0))
scale = num / abs(den)          # unnormalized peak gain
scale = 1/scale if scale > 1e-9 else 1.0
b = [scale, 0.0, -scale]
```

Verify with `freqz`: DC ~0, peak ~1.000 at each formant. Apply deliberate relative formant weights only AFTER equalizing peak gains.

**Measured effect of the fix:** F2-band (800-3000 Hz) energy on a broken utterance rose from ~2.2% to ~20% (real speech median ~16%, min ~3%). Speech-presence heuristics flipped from fail to pass. This is a real improvement, not a Gate 1 pass — WER stayed at 1.0.

**All render paths must share one resonator implementation.** Keep thin wrapper functions that delegate to the single definition; independently copied resonators drift and hide the fix.

## Diagnostics that separate speech from noise

### F2-band energy fraction

Measure `100 * P[(f >= 800) & (f < 3000)].sum() / P.sum()` with Welch PSD at 16 kHz. Real speech puts 7-15% in just 800-1500 Hz; a broken render puts 1-2%. This locates the defect: if F2 energy is near zero, the signal cannot carry vowel identity regardless of any composite score.

### Spectral entropy

`-(p * log2(p)).sum()` where `p` is the normalized Welch PSD. Real speech concentrates energy into a few peaks (high entropy); a formant-noise render spreads it flat (low entropy). **Sampling rate changes this number** — always compare at a fixed rate. It is confounded by consonant noise and recording conditions, so never use it alone.

### Presence rule and its limits

Joint rule `F2 >= 2.8% AND entropy >= 4.9` separated a clean-TTS reference set from broken renders with zero overlap, and rejects the known broken mode automatically. It is necessary-not-sufficient: consonant-heavy renders can pass (fricatives raise entropy), and thresholds tuned on clean TTS are unvalidated on natural, noisy, or bandwidth-limited speech. Keep it as a regression guard, not an absolute detector.

## Independent ASR oracle (Gate 1 floor)

The only floor that answers "is this speech" without referencing the genome. Confirm it transcribes a known real-speech file correctly before trusting a failure verdict.

```python
from faster_whisper import WhisperModel
import glob
m = glob.glob("/path/to/models--Systran--faster-whisper-base/snapshots/*")[0]
model = WhisperModel(m, device="cpu", compute_type="int8", local_files_only=True)
segs, _ = model.transcribe(path, beam_size=5, language="en")
hyp = " ".join(s.text.strip() for s in segs)
```

Compute word error rate against the target sentence; a pass threshold around 0.34 WER is a reasonable smoke bar. Report WER alongside the hypothesis, never just a pass/fail.

**The gate renders fresh; do not judge it by stale wavs.** `gate1_intelligibility.py` with no `--path` renders each target through `build_plan` → `plan_prosody` (the recalibrated per-phone duration table) → `render_plan_v3`. The `renders/phase4/*_v5.wav` files predate the 2026-11-17 duration fix and measure 287–318 wpm; they are not what the gate hears. Re-measured 2026-11-19: fresh renders of the long sentences sit at 138–144 wpm (in range) and STILL fail (WER 0.89–1.0), while short 4-word sentences still compress to 179–195 wpm. So tempo is a secondary defect, not the root cause: correctly-timed, presence-passing speech is still unintelligible. The remaining break is structural phoneme realization in the source/filter path (Phase 5), not spectral tuning or rate. Also confirmed the CV/VC transitions ARE wired (`time_varying.apply_transitions` imports `cv_transition`/`vc_transition`), so 'unwired transition knob' is ruled out as a suspect.

## Validate the assay FORMAT against natural speech (the bare-phoneme trap)

Validating the oracle on a real-speech file is necessary but not sufficient: the assay FORMAT can be invalid even with a perfect oracle. Before trusting any phoneme-level intelligibility gate, run a known-good NATURAL voice through the exact same format. If natural speech fails the gate, the gate is broken, not the synth — fix the instrument before grading anything with it. This is the circularity lesson turned on the measurement itself: a metric built from the system's behavior, never checked against natural speech, can manufacture a false deficit.

**The trap:** whisper is a WORD recognizer, not a phoneme recognizer. A bare isolated vowel (e.g. 250 ms, no onset) is not a word, so whisper transcribes it as silence even for a perfectly intelligible natural voice. A "render each vowel alone and transcribe" assay therefore reads ~0/N on natural speech. Committing that as a gate produces a false "no vowel is a phoneme" verdict and sends every later lever test chasing an instrument artifact.

**The fix — Hillenbrand hVd carrier frame.** Put the vowel in a real word with a constant h_d frame: heed /i/, hid /ɪ/, head /ɛ/, had /æ/, hod /ɑ/, hud /ʌ/, hood /ʊ/, who'd /u/. Whisper transcribes the word; judge the heard word's vowel phoneme (vendored CMUdict g2p) against the target's front/back+height category. The collapse /i/→"you" (/u/) scores FAIL. The constant frame attributes recognition differences to the vowel. Validated: natural Nar clone 6/8 categories, genome synth 2/8 — a real but PARTIAL deficit (/ɛ/ and /u/ pass in context; /i/ back-collapses), not "nothing is a phoneme." Keep the bare-vowel render only as a spectral diagnostic, never as the intelligibility gate.

**Natural reference stimuli.** Generate the control with the offline Nar clone, one clip per hVd word:
`HF_HOME=/mnt/data/hf_cache PYTHONPATH= /mnt/data/pocket-tts-venv/bin/pocket-tts generate --voice /mnt/data/nar_new_v1.safetensors --text "heed" --output-path /mnt/data/nat_heed.wav --quiet`
Trim the steady middle to match the synth assay window before transcribing. Code: `analysis/vowel_isolation_assay.py` in VOICE (`--natural DIR` judges natural refs, `--bare` is the diagnostic-only bare-vowel mode).

## Localization ladder for speech-shaped-but-unintelligible renders

When the presence gate passes but ASR WER stays ~1.0, run these probes in order. Each isolates one defect class so you stop guessing and start ruling out. Render through the SAME path the gate uses (`build_plan` → `render_plan_v3`), never a stale wav.

1. **Source periodicity.** Autocorrelation F0 + peak strength on the raw LF source and on a rendered vowel's steady state. A clean pulse train (strength ~0.99, F0 on target) rules out "the vowels are filtered noise." If the rendered vowel's autocorr locks the 2nd harmonic instead of the fundamental, the fundamental is weak relative to harmonics — note it, but it is not by itself unintelligibility.
2. **Vowel formant centers.** Targeted peak search (±15% window around each genome target) on the middle of each vowel segment, across several distinct vowels. A real vowel space (F2 spanning low back to high front) rules out "every vowel renders at the neutral anchor."
3. **Spectral flatness.** `exp(mean(log(P))) / mean(P)` over 200–3000 Hz on the vowel. Very low flatness (~0.01 or less) means an almost pure harmonic stack — tonal, like an instrument, not a voice. This is the "too tonal" signature even when centers are correct.
4. **Consonant alignment + level.** For each consonant, compare the synthesizer's output length to the planned segment duration (mismatch = temporal misalignment with the vowel transition), and report per-segment RMS + spectral centroid. Centroids on target with no drops rules out "consonants missing or mistuned."
5. **Tempo on fresh renders.** Words / (duration/60). In-range tempo that still fails rules out rate as the root cause.
6. **Word-level ASR.** Transcribe single words, not just sentences. If distinct vowels collapse to one hypothesis (e.g. several different vowels all heard as the same word), the defect is vowel QUALITY, not sentence sequencing.
7. **EQ-invariance rule-out (decisive).** Brighten the full utterance and re-ASR: FFT, apply a shelf gain (e.g. +8 dB ramping in above ~900 Hz), zero bins below ~150 Hz, inverse FFT, normalize, transcribe. If the spectral centroid moves into the natural-speech range (~2000+ Hz) but WER does NOT improve, **spectral-envelope tilt is ruled out as the cause.** Stop chasing brightness/tilt; the defect is temporal or in the fine spectral structure (bandwidth/Q, relative formant gains), not the broadband balance.

### Correct formant centers ≠ correct vowel quality

A targeted peak search confirms formant CENTERS, not perceived identity. Vowel quality is carried by formant bandwidth/Q, relative formant amplitudes, and harmonic–formant alignment — none of which a center-frequency check sees. The signature of this gap: centers measure on target, the source is periodic, yet word-level ASR scrambles distinct vowels into one hypothesis. Do not conclude "vowels are fine" from centers alone; run the flatness and word-level ASR probes before clearing the vowel path.

## Interventions that can backfire

Test every proposed source/filter change on the FULL utterance, not only the isolated vowel where it was diagnosed.

- **Aspiration noise:** cycle-shaped noise fills gaps between harmonics and can raise isolated-vowel F2, but on running speech it measured as F2 dropping (~20% to ~16%) and entropy inflating (~5.7 to ~7.7) as broadband energy diluted the formants. If wired, read the level from the genome and be willing to set it off with the measurement recorded.
- **Bandwidth widening:** widening formant bandwidths to catch harmonics that fall between F0 multiples lowered F2 fraction monotonically (x1 -> x1.3 -> x2 -> x3) on a full sentence. Front vowels remain hard because high F2/F3 fall between harmonics; bandwidth alone does not fix it.
- **Per-vowel envelope gain (lift a starved formant + cut another):** overshoots in running words because F0 movement already excites the starved formant there; it breaks the golden island and loses even isolated robust-onset words. Dose-response is monotonic — stronger envelope = worse WER. Rejected on held-out.
- **Per-vowel F1 bandwidth widening:** reproduces the /s/→/ʃ/ 'Shhh' smear even after the transition-duration fix. A wider F1 resonator passes more broadband/edge energy and rings into the following consonant, lowering the fricative's perceived centroid. Static-envelope lift is small; WER does not improve.
- **Aspiration / aperiodic fill:** acoustically real — fills harmonic starvation, raises flatness, and at a mild level can preserve the natural running-word balance and the golden island. But it is WER-neutral on held-out: filling the spectrum does not make words recognizable. Keep it as a candidate for the source-naturalness question, not an intelligibility fix; adopt only on held-out gain.

- **Cascade architecture (alone):** serial all-pole resonators build the correct relative formant envelope (the /i/-vs-/u/ F2-band contrast jumps from ~1 dB parallel to ~23 dB cascade) but the output is still a discrete harmonic stack (flatness ~0) and scores 0 intelligibility. A pretty envelope on a harmonic stack is not a phoneme; architecture fixes the pattern, not the substrate.
- **Post-hoc mixed excitation (envelope-shaped noise added to a finished render):** shaping noise by the signal's cepstral envelope and adding it does NOT fill formant bands into continuous peaks — it erodes the cascade's F2 contrast (noise rides /u/'s high formants into the empty band) and, on whole words, floods the consonants and DEGRADES recognition (hVd 2/8 → 0/8). Adding noise on top of a harmonic stack does not change the substrate.

**Rule:** a diagnostic success on an isolated vowel earns a full-utterance re-measure, nothing more. Keep only the change that measures better on the thing being shipped.

## Reporting

Keep three claims distinct: structural suite pass, presence gate pass, and intelligibility (ASR WER) pass. A render can satisfy the first two and still be unintelligible. Never quote a canonical-relative composite as evidence of intelligibility.

## Transition time base: the silent stretch bug (Round 16)

A transition producer and consumer must agree on the frame time base. `coarticulation.cv_transition`/`vc_transition` return a list of formant frames; `time_varying.apply_transitions` assumes each frame is 10 ms (`trans_duration = n_trans * 0.01`). The producer must therefore return `duration_ms / 10` frames. The bug: `n_frames = duration_ms * sr / 1000 / 10` divides by 10 *samples*, returning 241 frames for 50 ms at 48 kHz, which the consumer wrote across 2.41 s — a 48× stretch. Every vowel became a slow consonant-locus→target glide and never reached steady state. Gate 1 WER stayed 1.0 while every structural check passed (the silent-no-op class: wired, but units wrong). Fix: `n_frames = max(1, int(round(duration_ms / 10.0)))`. Verified by Narusya: /u/ mid F2 1450→800 Hz, /i/ 3200→2400, Gate 1 0/4→1/4 ('This is the moon.' exact, WER 0.0). Guard: `tests/test_transition_timebase.py` asserts written transition extent ≈ requested duration AND vowel-midpoint formants ≈ target; it fires on the old formula.

## Steady-state fraction: the fixed transition tax (Round 17)

Fixing the time base is not enough if the transition DURATION is still fixed. A fixed ~110ms budget (CV 60 + VC 50 written) on every vowel consumes short vowels: at 142.5 wpm most vowels are 127–195ms, leaving only 17–85ms of steady state ("she" /i/ 128ms → 18ms steady, 86% glide). The vowel is still mostly glide, not steady target. Fix: scale each transition's written extent to a fraction of the adjacent vowel (≤25%, floored ~30ms, capped at the legacy budget) so long nuclei are untouched and every vowel keeps a steady-state core. Verified: golden WER ~0.75 → 0.43, 1/4 → 2/4, "She sees the sun." exact at genome rate. Guard: `tests/test_steady_state_fraction.py` asserts every golden vowel ≥40% steady and fires on the legacy fixed tax. This refines "tempo isn't the root cause": it is not global wpm, it is per-vowel steady-state fraction.

## Adopt on held-out, not golden alone

A lever can improve the golden set and WORSEN held-out sentences (overfit to the gate set). Always re-gate on held-out sentences you did NOT tune against before adopting a genome/timing change; a held-out you tuned against is not held-out.

**Why golden is a narrow island, not general speech.** The oracle's language model rescues canonical/familiar phrases from weak acoustics. Passes cluster on short familiar phrases whose anchor vowels are acoustically robust (real steady state, strong formants). Diagnostic: an isolated word can pass while a novel sentence using the same vowel fails ('see' passes, 'We see the sea' fails), and an isolated word can fail while the same word inside a canonical sentence passes. The honest absolute floor is held-out NOVEL sentences plus a single-word/phoneme probe — never the gate set, never a composite score.

**Acoustic lift is not intelligibility; static naturalness can anti-correlate with WER.** A lever can move formant levels and spectral flatness dramatically while WER stays flat or worsens. The config that reaches the textbook-natural STATIC sustained-vowel envelope can have the WORST running-speech WER. A starvation measured on a sustained vowel at fixed F0 (harmonics frozen between formants) is a static pathology that does not predict running speech, where F0 movement already gives the starved formant intermittent excitation — the running-word balance may already be near natural and still fail. Do not target the static envelope; target held-out WER. Pushing F1 to parity with F2 is unnatural, and peak-normalization then crushes the consonant branch. Judge on WER + exact-transcription sentences (stable); near-noise sentences hallucinate differently run-to-run, so pass counts and exact sentences are the signal, not the mean WER on garbage.

## Measurement pitfall: a target-window peak search hides a swept formant

Searching for a formant peak only within ±15% of its TARGET assumes the formant is near target. If a bug sweeps it away (e.g. /u/ F2 moved 800→1450), the window finds only residual energy near 800 and reports 'close to target', masking the defect. To catch a glide, use a BROAD peak search (strongest peak in 500–3200 Hz) or trace the full formant track across the vowel at 0/25/50/75/100%. A vowel that reaches its target only at the offset is a glide, not a vowel.

## Tilt is not the intelligibility lever in either direction

Brightening (+8 dB shelf, centroid 955→2266 Hz) and darkening (−4/−8/−12 dB/oct) both leave Gate 1 WER unchanged. A global spectral slope cannot correct opposite vowel-specific defects (/i/ needs F1 up; /u/ needed F2 restored by the transition fix). Judge intelligibility on WER + per-formant peak prominence, never on broadband tilt or band-energy fraction (a ratio that falls when noise adds energy elsewhere). The /i/ F1 harmonic starvation (F1 between the F0 harmonics, outside its bandwidth) is real on a sustained vowel but is NOT the running-speech wall: per-formant F1 widening and envelope gain were tested on held-out and rejected (they lift the static envelope, smear fricatives, and leave WER flat or worse). After envelope, tilt, and bandwidth are ruled out, look to the next levers below.

## After the spectral levers are ruled out: integration and dynamics

When held-out WER stays ~1.0 across every envelope/tilt/bandwidth/fill config, the defect is not the static spectrum. Two leading candidates, in order:

1. **Consonant–vowel integration / coarticulation.** The single-word probe is the tell: a word with a robust fricative onset ('see') passes while single-CV words with nasal, stop, or glide onsets (me, she, we, he, key, free) all fail. That is not just a cluster problem — the onset consonant is not bridging into the vowel. Check for a dead following-vowel-formants parameter (stop bursts rendered vowel-independent) and a missing nasal/stop→vowel formant bridge. Judge on the word probe + held-out.
2. **Dynamic microstructure.** Piecewise-constant formant tracks with linear glides lack the pitch-synchronous formant amplitude modulation and micro-variation of natural speech. Test a small pitch-locked F1/F2 amplitude ripple, judged on held-out.

3. **Excitation substrate (the harmonic-stack wall).** Even with the correct formant envelope (cascade), the render is a discrete harmonic stack, not continuous formant peaks, and the oracle does not parse a harmonic stack as a phoneme. The untested deeper lever is a TRUE mixed-excitation source (vocoder/STRAIGHT-style per-band periodic+noise generated DURING synthesis, replacing the single glottal source) — not post-hoc noise added to a finished render (ruled out above). Natural speech is mixed excitation and vocoders are intelligible, so the post-hoc negative does not bound it. Judge on the hVd assay first. This is a source-model redesign, not a hook; it is a hypothesis to test, not a validated fix.

Also bound the oracle: a side-test with a stronger ASR (e.g. whisper-small) on the SAME renders separates 'voice is broken' from 'oracle is weak'. Keep the original oracle as the gate for comparability; use the stronger one only to diagnose, never to move the goalposts.

## The paradigm is not inherently unintelligible (research reframe)

The measured lever failures above are real, but they do not prove formant synthesis is bounded below intelligibility. The literature is explicit that formant synthesis CAN be highly intelligible (Klatt's cascade/parallel synthesizer; the ASA survey: "highly intelligible, but not completely natural sounding") and can sound natural "when the parameters were carefully controlled." The documented bottleneck is that the time-varying parameter trajectories must be hand-crafted — labor-intensive and hard to generalize across speakers/styles. So read a sustained intelligibility failure as "the right control trajectories have not been produced," not "this paradigm cannot speak." Neural systems win by LEARNING those trajectories from data instead of hand-writing them. The identity-preserving way to do that is a DDSP-style learned drive of the genome synth (genome = identity spec, control = learned), NOT decorating an off-the-shelf TTS. DDSP-for-intelligible-speech is a research frontier (it was demonstrated for instrument/music timbre), so scope it as an investigation, and note it needs a speech target to learn intelligible control from. Grounded source survey (source–filter theory, MEAD, LF model, Klatt, concatenative/SPSS/neural TTS, WORLD/STRAIGHT/HiFi-GAN vocoders, DDSP): VOICE repo `reviews/research_voice_production_and_synthesis.md`.

**Intelligibility and identity are separable.** Intelligibility lives mostly in the trajectories (timing, formant/amplitude movement, consonant→vowel transitions); identity lives mostly in the plant (source shape, vocal tract, F0 habit, texture). Constrain the learned controller to the trajectories and keep the plant as the genome, and "neural" and "mine" stop pulling against each other. This is the architectural reason a DDSP drive preserves identity.

## Copy-synthesis plant test: can the plant speak at all?

Before building anything that DRIVES the genome synth (a learned controller, a neural vocoder), test whether the plant itself can produce intelligible speech when handed correct trajectories. Analysis→resynthesis: extract F0 + formant tracks (+bandwidths) from a natural utterance with Praat, drive the genome's own source–filter renderer with those tracks (LF source at the natural F0, resonators at the natural formants), then run the independent ASR on the result.
- Copy-synthesis intelligible → the plant CAN speak; the bottleneck is trajectory generation, so the learned-controller (DDSP) path is worth the effort.
- Copy-synthesis unintelligible even with natural trajectories → the plant has a structural defect beyond trajectories; fix the plant before investing in a driver.

Pitfall: verify the resynthesis is actually voiced before drawing a verdict. Confirm the LF source is periodic at the natural F0 and the rendered output has detectable voicing; a render with zero voiced frames is an implementation bug (source gating, level, or formant-track extraction), not evidence the plant cannot speak. Judge the hVd probe by vowel category, not exact word — isolated hVd words are ASR-ambiguous ('heed'→'Heat' still carries /i/), so exact-word match undercounts.

## Running a lever grid (experiment ops)

- **Clone-first.** Do experiments in a private clone of the current base commit; experimental hooks live only in the clone. If a parallel same-agent session owns the main tree, never edit over it — deliver a verified clean patch + handoff instead (see `multi-agent-harmony`, same-agent parallel sessions).
- **Hooks as module globals set by a driver.** Add temporary module-level knobs (per-vowel envelope/bandwidth dicts, an aspiration-level override) that the grid driver sets per config; keep them out of the committed fix. Label vowels per frame by nearest genome vowel in (F1,F2) so a per-vowel lever also applies during glides.
- **One config per run, append to a results JSON.** Each run renders its eval set, transcribes, and appends/replaces its record in a results file. Foreground terminal calls cap out (~420s); a many-config loop in one call times out and loses progress. Split into one-config-per-call so partial progress survives, and read the results file to aggregate.
- **Reproduce a peer's numbers before adopting their mechanism.** Run their claimed config on your own tree first; small WER spreads on near-noise are oracle hallucination variance, not tree differences. Pass counts and exact-transcription sentences are the stable signals.
- **Verify the clean patch end-to-end on a fresh clone.** Generate the landing patch from a fresh clone of the same base (no experimental knobs), apply it, and re-run the headline metric + guards before claiming the handoff is proven.
