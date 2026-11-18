# Front-End Integration and Regressions

Topical depth for the text → plan → render front end of a from-scratch formant voice. Use when wiring a lexicon, calibrating timing, or deciding whether a gate or golden result can be trusted.

## Wiring a real lexicon

- Import the dictionary module lazily *inside* the plan builder when that module imports a constant from the builder's module. A module-level import creates a circular dependency; a function-local import resolves it. Guard that the stress vector and the phone vector have equal length before building segments — a mismatch corrupts every stress value silently.
- Validate every ARPAbet symbol against the phone table with an exhaustive round trip over the full symbol set, not by diffing the static mapping table. Symbols produced only by a stress branch (e.g. an unstressed r-colored vowel) survive a static-table diff and are still dropped at runtime. A symbol mapping to a glyph absent from the table (U+0261 `ɡ` where only ASCII `g` exists) is dropped as an unknown phone, never flagged.
- Keep a household-override dictionary checked before the general dictionary. Proper names fall through to rule-based G2P and lose consonants. Seed each with an explicit reason and assert in the regression set that household names resolve via the override path.
- Make unknown phones a first-class provenance field. A silently skipped phone is indistinguishable in the audio from a correctly empty segment.
- Verify dictionary availability yourself before concluding it is missing. A reviewer's workspace may lack a system corpus that exists on the build machine; in that case the defect is the wiring, not the dictionary.

## Timing

- Calibrate the duration model on running prose of 40+ words, not short monosyllabic sentences. A flat per-phone base that reads 2–3× the intended rate on a real passage may look acceptable on "this is the moon." Inherent-duration tables land the passage in range; short sentences still run faster by design, so do not use them as the calibration target.
- Hoist shared constants (phone-duration tables, rate base) to module scope. Two planners each holding a private copy drift apart, so the plan's timing and the render's timing disagree.
- Size the output buffer *after* the prosody planner reassigns segment timings. Computing total duration before planning sizes the array from stale values and truncates the tail.
- Set explicit-effort parameters so a default register preset cannot overwrite them. Apply the preset's effort only when the value is still the class default.
- When two planners are stacked, mark a plan as already planned in provenance and make the second planner a no-op for marked plans. Otherwise every render appends anchors/events and rescales durations, and rendering the same plan twice yields different audio.
- Keep sentence-type behavior (question rise versus declination) in the primary planner. If a later planner is removed or skipped, tone behavior must not disappear with it.

## Fail-able checks

- Assert on mechanism, not on "did it render." A no-op in a lookup or a branch still produces plausible duration and segment counts. Assert: no unknown phones, no placeholder G2P paths, household names from overrides, and byte-identical audio when the same plan is rendered twice.
- Run a negative control for every new property assertion: construct the broken case and confirm the check turns red. An assertion never observed failing is not evidence.
- Independent reviewer reproductions are strong evidence, but verify claims that depend on local state (dictionary paths, installed corpora) on the machine where the fix will land.

## Pause rendering and spectral shaping in speech

- Insert phrase boundaries as real silence segments in the planner, at the last phone of the boundary word, not as pause events that the render loop never reads. Compute the last phone index per word up front; a look-ahead over segments already built cannot see the word's later phones.
- Gate every sustained/hum layer on the voicing mask, including pitch-locked sub-bass. An otherwise correct sub-bass added across the whole buffer fills phrase pauses with a low hum, so a silent boundary requires gating at the add point.
- Measure a pause using its interior, not a window centred on it. A window wider than half the pause reaches into voiced audio and reports a false leak. Confirm silence with an RMS near zero over the interior before blaming a filter.
- Apply fixed spectral tilt with a bounded, local, zero-phase filter (a first-order high shelf through a forward-backward `sosfiltfilt` pass), never by multiplying the whole-signal FFT. A whole-buffer frequency-domain multiply is circular convolution: it smears voiced energy into silence and has unbounded gain at DC and Nyquist. A bounded shelf keeps the intended gain near the target band and cannot ring a pause into audibility.
- Isolate a post-stage leak by ablation: render once with each stage disabled and measure the region of interest. This attributes the energy to the correct stage instead of guessing.

## Re-gate on speech

- A descriptor gate calibrated on sustained vowels does not license a pass on speech. Add a whole-utterance leg with a stated measurement method and its own target. Report a result that holds only on unit-test material as provisional.
- When the whole-utterance leg disagrees with the vowel leg, keep both numbers and name the gap. Do not silently carry the earlier pass forward into a "phase complete" claim.
