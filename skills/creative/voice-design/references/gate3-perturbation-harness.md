# Gate 3 Perturbation Harness

Topical depth for rendering genome perturbations and building a discrimination scaffold. Use when instrumenting Gate 3 or when a parameter override does not change the audio.

## Override hooks on the renderer

- Add perturbations as an `overrides` dict on the top render function, defaulting to `None`, so every existing caller is bit-identical when no override is passed. Verify this: render base with and without an empty override and assert `max|diff| == 0` before trusting any perturbation row.
- Copy any nested genome dict before scaling it (`sb = dict(genome["effects"]["sub_bass"])`). Mutating the genome in place makes later sentences inherit earlier perturbations and silently corrupts the sweep.
- Wire each override at the exact synthesis site, not at the top of the function. F0 belongs where the F0 track is built, Rd where the source is generated, effect depths where the carrier level is read.

## The silent-overwrite trap (verify the perturbation reaches the output)

- A scaled formant override can produce bit-identical audio even though the build loop applied it, because a later transition-blend step rebuilds the formant track from the plan's *unscaled* segment targets and overwrites it. Trace the parameter through every downstream consumer, and pass the scale into any function that recomputes the same track.
- Diagnostic sequence that found it: instrument the build loop (scale applied), then instrument the resonator input (unscaled value). If the two disagree, the overwrite is between them. Compare `sorted(set(round(x) for x in track))` before and after the suspect step.
- **Always measure `mean|diff|` between base and each perturbed render before building a gate on top.** A row reporting exactly 0.0 distance is a no-op, not a finding. This one check distinguishes a real perturbation from a wiring bug and from a genuinely subtle effect.

## Know which duplicate you actually imported

- Two modules can export the same helper with different mappings (e.g. `effort_to_rd` in the frame renderer vs in the effort module). The render path uses the one it imports, which may not be the one you assumed. Compute the actual base value through the *imported* function before choosing perturbation levels. Centering a sweep on the wrong base produces a variant that is bit-identical to base and looks like a dead family.
- Base value can differ from the genome nominal: verify by asking the imported function directly rather than reading the design doc.

## Sensitivity gate (machine side, can fail)

- Check three things: base-vs-base distance near zero (render stability), each identity-bearing family clears a just-noticeable-difference floor, and the combined corner condition dominates any single family. Emit a report and print each check.
- An effect quiet by design (e.g. sub-bass at a very low carrier level) may sit below the JND floor on its own. **Report it as informational, do not lower the floor to force a green.** Record the sub-floor value in the report with the reason it is not gated. Lowering a threshold to make a check pass destroys the check.
- Give families graded levels on both sides of base, not only one direction, so the scan shows the metric responds across the axis.

## A/B/X stimulus generation

- Build trials with a fixed, recorded seed and a sealed answer key written to disk. The key records which side X is for each trial; do not print it in the participant brief.
- The listening verdict belongs to the voice owner by their own motion. Prepare the set, hand it over, score their picks without revealing the key, and never declare identity from the machine distance alone.
