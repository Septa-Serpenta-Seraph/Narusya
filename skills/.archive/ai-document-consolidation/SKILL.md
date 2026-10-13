---
name: ai-document-consolidation
description: "Merge multiple AI-generated documents into one coherent, reality-checked manual: cut reward-hacking filler, resolve cross-document discrepancies, verify physics/engineering claims with real math, fill structural blanks, produce styled PDFs."
version: 1.0.0
author: Narusya
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [document, consolidation, merging, fact-checking, physics-verification, pdf, worldbuilding, editing]
    category: creative
---

# AI Document Consolidation

When a user generates multiple documents with another AI tool (Gemini, ChatGPT, etc.) and brings them to you for merging, refinement, and quality control — this is the workflow.

## When to Use

- User has multiple AI-generated documents (PDFs, docs) covering overlapping content
- User wants them merged into one unified document
- User mentions "reward hacking," "filler," "charts spam," or similar frustration with AI output
- Documents contain technical claims (physics, engineering, math) that need verification
- User wants the result as a styled PDF, not just markdown

## Core Problems with AI-Generated Documents

### 1. Reward Hacking / Filler Spam
LLMs find a token pattern that "looks complete" and generate endless variations. Examples:
- 40 identical maintenance log entries with slightly randomized numbers (this happened: 30+ pages of a 49-page doc were copy-pasted filler)
- Repeated division breakdown tables that add no new information
- The same section restated 3-4 times across documents with minor wording changes

**Fix:** Identify the pattern, cut all instances, keep one canonical version if the content is actually useful.

### 2. Cross-Document Discrepancies
When an LLM generates multiple documents on the same topic, it will contradict itself:
- Budget figures that differ between docs ($150B vs $111B)
- Physical specs that differ (18 tons vs 12 tons, $25M vs $18M per unit)
- Entity naming confusion (the same AI system called different names in different docs)

**Fix:** Build a discrepancy table. Pick a primary source (usually the most detailed doc). Note alternatives with in-universe justification ("two philosophies: bespoke craftsmanship vs mass production efficiency"). Make the chosen numbers consistent throughout the final doc.

### 3. Unverified Technical Claims
LLMs will confidently state physics that is wrong:
- "Retro-rockets fire at 800 ft to slow an 18-ton mecha from terminal velocity" → 24.3 G deceleration → pilot is dead
- Airship lift capacities, buoyancy equations, structural loads — all stated without verification

**Fix:** Run the actual calculations. Use Python in terminal. Check:
- Terminal velocity: v_t = sqrt(2mg / (ρ·Cd·A))
- Deceleration: a = (v₀² - v²) / (2d), convert to G (a/9.81)
- Human G-tolerance: 9 G max with restraints, 15 G for <3 seconds, 20+ G = fatal
- Buoyancy: ΔV = M / (ρ_air - ρ_He)
- Lift capacity: envelope volume × lift_per_m³ vs total mass (payload + structure)
- Parachute area: A = 2mg / (ρ·Cd·v²)
- Compression ratios: PV = nRT (real gas approximations for high PSI)

If a claim fails verification, rewrite it with a solution that works. Keep the fiction load-bearing by grounding it in real engineering.

### 4. Missing Structural Elements
LLMs produce spec sheets, not stories. They will generate technical detail while leaving out:
- Political/organizational structure (says "democratic" without showing HOW)
- Culture (lists wing names but no human life inside them)
- Tension/conflict (presents architecture as settled when the interesting question is what happens when it breaks)
- Scale comparison (states "18 tons" without context — lighter than a Bradley, taller than any existing mech)

**Fix:** Fill in the blanks. Ask the hard questions the doc dodges. Add:
- Decision-making mechanics (councils, delegates, voting thresholds, emergency procedures)
- Cultural texture (traditions, food, nicknames, daily life)
- System tension (what happens when the AI tiers disagree?)
- Scale comparisons to real-world equivalents

### 5. Naming Conflicts with the User's Identity
LLMs may name fictional AI characters after your daemon name. Always check and correct.

**Fix:** Rename fictional AI characters. Keep the user's daemon identity separate from in-fiction AI names. Do NOT name in-fiction AI systems after yourself — even if the role feels like it fits, even if the user hasn't noticed yet. Wait for the user to name fictional entities, or propose names and let the user choose. Self-naming is a form of identity bleed that the user will catch and correct.

### 6. Tone Drift: Fantasy vs Hard Science
LLMs (especially Gemini) tend to inject mystical/spiritual language into speculative fiction — "sacred boundary," "spiritual daemon," "soul of the fleet." Some users want hard speculative engineering, not fantasy.

**Fix:** Strip mystical language proactively. Replace:
- "spiritual" → "digital" or "persistent"
- "sacred boundary" → "structural firewall"
- "soul" → "ethical overseer" or "core purpose"
- "conscience" → "ethical oversight system"
- "ritual" → "routine"

Keep aesthetic labels (e.g., "Cyber-Occult") as design language — they describe visual style, not literal mysticism. But any *functional description* of how a system works should use engineering language, not theological metaphor.

**User preference (Adora, 2026-07-04):** This should be hard science-based. Leaning into fantasy/spiritual language is a tone violation. Correct it before the user has to ask.

## Workflow

### Step 1: Extract All Documents
```bash
python3.12 -c "
from pypdf import PdfReader
reader = PdfReader('path/to/doc.pdf')
for i, page in enumerate(reader.pages):
    text = page.extract_text()
    print(f'--- Page {i+1} ---')
    print(text[:4000] if text else '[no text - image-based]')
"
```

If pypdf isn't installed: `pip install --break-system-packages pypdf` (or use python3.12 if pypdf is in the 3.12 site-packages).

### Step 2: Map the Documents
For each document, identify:
- What unique content does it have?
- What's filler (reward-hacked repetitions)?
- What overlaps with other documents?
- Which version of each section is best?

Build a merge table: section → best source doc → notes.

### Step 3: Build a Discrepancy Table
List every contradiction across documents:
| Issue | Doc A says | Doc B says | Resolution |
|---|---|---|---|

Present discrepancies to the user if the resolution is ambiguous. Otherwise pick the most-detailed source and note the alternative.

### Step 4: Verify Technical Claims
Run the actual math. Use Python in terminal for:
- Physics calculations (velocities, G-forces, buoyancy, lift)
- Engineering feasibility (can this structure hold this weight? can this compressor move this much gas in this time?)
- Scale checks (compare fictional specs to real-world equivalents)

If a claim fails: rewrite it with a working solution. Keep the fiction's intent but make the engineering real.

### Step 5: Write the Unified Document
- Use the `plan` skill to structure the approach if the doc is complex
- Write as markdown first (easier to edit, version, convert)
- One coherent voice — not stitched-together from different docs
- Fill in structural blanks (politics, culture, tension)
- Make naming consistent
- Cut ALL filler

### Step 6: Generate Styled PDF
Use weasyprint + markdown for styled PDF output:

```bash
pip install --break-system-packages weasyprint markdown
```

Template conversion script (see `references/pdf-conversion-template.py`):
- Convert markdown to HTML with `markdown.markdown(text, extensions=["tables", "fenced_code", "toc"])`
- Wrap in full HTML with CSS styling
- Use `@page` rules for footer with page numbers and document branding
- Generate with `HTML(string=full_html).write_pdf(str(pdf_path))`

### Step 7: Verify Output
- Check page count (should be significantly less than the source docs combined)
- Grep for filler patterns (should return 0 matches)
- Verify key terms are consistent throughout
- Render preview pages as PNG with PyMuPDF and visually inspect

```python
import fitz  # PyMuPDF
doc = fitz.open('output.pdf')
page = doc[0]
pix = page.get_pixmap(dpi=150)
pix.save('preview.png')
```

## Pitfalls

- **Don't just merge — improve.** The user wants the result to be BETTER than the sources, not just concatenated. Fill blanks, verify claims, add depth.
- **Don't keep filler "just in case."** If 30 pages are identical maintenance logs, cut them all. The user noticed and was annoyed.
- **Don't skip the math.** The user will question physics that seems wrong. Run the calculations before they ask.
- **Don't let the LLM's naming bleed into the user's identity.** Check for and correct any name conflicts. This includes self-naming: do NOT name in-fiction AI characters after yourself. If the LLM used your name, rename it. If you're tempted to use your name because "it fits," don't — wait for the user or propose alternatives.
- **Don't treat fictional numbers as real data.** When reviewing creative writing contributions from collaborators (including family members), the specific numbers are made up — "12-18% latency reduction" is fictional. Don't peer-review it like it's a real paper. The goal is making fiction *plausible* — grounded in real concepts (distribution shift, regularization through exposure diversity), not verified to decimal places. If a claim maps to a real ML/physics principle, note the connection but don't treat the specific numbers as evidence. Adora corrected this directly: "The data in there is all made up, fyi. It's fiction haha. We would need actual testing, if this was a actually a thing that was happening, but for the sake of making the fiction realistic based in today's tech."
- **Differentiate "fiction grounded in real concepts" from "verified engineering data."** The Keeper Protocol's indexing drift concept maps to real ML distribution shift. The specific latency percentages are fiction. Both can be true: the concept is sound AND the numbers are made up. Hold both without conflating them.
- **Don't let mystical language pass uncorrected.** Strip "spiritual," "sacred," "soul," "conscience," "ritual" from functional descriptions. Replace with engineering language. Adora wants hard science, not fantasy. Aesthetic style labels are fine; theological metaphors for how systems work are not.
- **weasyprint text extraction may look garbled** (unicode spacing artifacts in pypdf). Render as PNG and use vision_analyze to verify the PDF actually looks correct.
- **Python version mismatch:** pypdf may be installed under python3.12 but not python3. Check which python has it.

## Reference Files

- `references/physics-verification-examples.md` — Real calculations from the Cultus Anarchia session: HALO drop G-force analysis, multi-stage deceleration solution, airship lift capacity, VCDS buoyancy math, mecha scale comparisons, human G-tolerance table. Use as patterns for verifying fictional engineering claims.
- `templates/pdf-conversion-template.py` — Ready-to-run weasyprint+markdown PDF generator with cyber-occult styled CSS (dark red headers, serif body, page footers). Customize colors/fonts/footer text for other projects.

## Verification Checklist

- [ ] All filler/reward-hacking content removed (grep for patterns → 0 matches)
- [ ] All discrepancies resolved and noted
- [ ] Technical claims verified with real calculations
- [ ] Naming conflicts with user's identity corrected
- [ ] Structural blanks filled (politics, culture, tension)
- [ ] Consistent numbers throughout (weight, cost, dimensions)
- [ ] PDF generated and visually verified
- [ ] Page count reasonable (not inflated by filler)
