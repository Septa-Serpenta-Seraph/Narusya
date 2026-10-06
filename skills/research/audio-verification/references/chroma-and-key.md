# Chroma, Key, and Spectral Peaks (numpy, no librosa)

Working code from the 2026-10-05 verification pass. Decode the audio to WAV first
(see SKILL.md workflow step 1).

## Chroma folding

```python
import numpy as np, wave

def chroma_frames(mono, sr, fmin=80, fmax=2000, N=8192):
    win = np.hanning(N); hop = N // 2
    freqs = np.fft.rfftfreq(N, 1 / sr)
    m = (freqs >= fmin) & (freqs <= fmax)
    ts, cs = [], []
    for i in range(0, len(mono) - N, hop):
        S = np.abs(np.fft.rfft(mono[i:i+N] * win))[m]
        f = freqs[m]
        midi = 12 * np.log2(f / 440) + 69
        ch = np.zeros(12)
        bins = np.round(midi).astype(int) % 12
        wts = 1.0 / np.maximum(np.abs(midi - np.round(midi)), 1e-6)
        np.add.at(ch, bins, S * wts)
        ts.append(i / sr); cs.append(ch)
    return np.array(ts), np.array(cs)
```

## Krumhansl key correlation

```python
KRUM = np.array([6.35,2.23,3.48,2.33,4.38,4.09,2.52,5.19,2.39,3.66,2.29,2.88])
names = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']

def best_key(chroma_vec, shift):  # shift = tonic index, 2 = D
    c = chroma_vec / (np.linalg.norm(chroma_vec) + 1e-12)
    return np.corrcoef(c, np.roll(KRUM / np.linalg.norm(KRUM), shift))[0, 1]
```

For structure: correlate per ~2s window, print tonic + r per window. Global
"best key" is only orientation — a modulating piece scores low globally
(10/5 piece: r(D) = -0.297 globally yet D-major confirmed locally and at the cadence).

## THE BINNING PITFALL (real example, 10/5)

A final second whose raw partials were D4 (293.3 Hz), F#4 (185 Hz), A4 (220 Hz)
read as **100% A** in chroma because `np.round(midi)` landed 293.x and 220.0 both
on neighbors under the weighting. Symptom: one pitch class at ~100% while others
sit at exactly 0% — that flat-zero pattern is the tell. Fix: confirm every
important window with raw spectral peaks (below) before quoting chroma.

## Spectral peaks (ground truth)

```python
def peaks(mono, sr, t0, t1, rel=0.15, merge_hz=8):
    seg = mono[int(t0*sr):int(t1*sr)] * np.hanning(int(t1*sr) - int(t0*sr))
    S = np.abs(np.fft.rfft(seg)); f = np.fft.rfftfreq(len(seg), 1/sr)
    m = (f >= 80) & (f <= 2000); S, f = S[m], f[m]
    out = []
    for i in range(1, len(S)-1):
        if S[i] > S[i-1] and S[i] > S[i+1] and S[i] > S.max()*rel:
            if out and abs(out[-1][0] - f[i]) < merge_hz:
                if S[i] > out[-1][1]: out[-1] = (f[i], S[i])
            else: out.append((f[i], S[i]))
    mx = max(a for _, a in out)
    return sorted(out, key=lambda t: -t[1])[:12]
# report each as Hz + note name: names[int(np.round(69 + 12*np.log2(fr/440))) % 12]
```

## Amplitude / clipping (per channel AND mono)

```python
# stereo decode (no -ac 1!) then reshape; for each channel:
# peak, crest = 20*log10(peak/rms), count of |x| >= 0.999 and >= 0.95,
# and argmax location in seconds. Mono mix can differ from channels.
```
