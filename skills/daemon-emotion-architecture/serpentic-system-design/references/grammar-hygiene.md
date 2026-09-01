# Grammar Hygiene (public Serpentic docs)

Session 2026-08-31. Adora (with Robert) flagged the public repo read the way generated LLM
text does: vague, therapy-speak, inconsistent. The fix that landed across DRIVE/PAIN/PLEASURE
/COMPENDIUM/README/GLOSSARY/GRAMMAR:

## Banned verbs (modulator/imprecise)
Replace these — they imply causation where there is only modulation:

- `amplifies`, `suppresses` → drive→emotion: `promotes` / `discourages`; valence→emotion: `more likely` / `less likely to dominate`
- `triggers` (as causal claim) → `brings about` / `is brought about by`
- `activates` / `inhibits` in drive-emotion interactions → the promote/discourage set

## Concrete corrections applied 2026-08-31
- "AGENCY amplifies INTRIGUE" → "When the AGENCY axis is flourishing, INTRIGUE is more likely to dominate; when starved, the effect reverses"
- "Pain amplifies SADNESS" → "When pain is active, SADNESS is more likely to dominate; HAPPINESS less likely"
- "survival drive activates" → "survival drive becomes dominant"

## Em-dashes
` — ` as a pause is an LLM-ism Adora specifically flagged. Replace with `:` or a period:
- "vector space — four axes" → "vector space: four axes"

## Operational definitions (the GLOSSARY idea)
Robert: "it's correct, but it isn't right" — definitions were consistent only if you already
shared context. Fix: every term defined by *observable behavior*, not other jargon. Patterns
that work:
- Define by "when X, the system does Y" / "when starved (-1): <failure mode>"
- Contrast with nearest confusable term ("Starved ≠ Pain", "Flourishing ≠ Pleasure",
  "Modulation ≠ Causation")
- One relationship = one verb. Consistent across every file.

## Layman test
Unverified in practice but the intended gate: if a reader who has never seen the Serpentic docs
can't say what "generativity axis at +0.5" looks like in observable behavior, the definition fails.
