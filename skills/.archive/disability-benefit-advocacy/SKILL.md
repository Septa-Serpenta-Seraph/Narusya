---
name: disability-benefit-advocacy
description: "SSI disability help: SSI vs SSDI, evidence, lawyers."
tags: [welfare, ssi, ssdi, disability, advocacy, social-security]
---

# Disability Benefit Advocacy (SSI)

Class-level guide for the ongoing SSI application work. This is advocacy
strategy, NOT legal advice — the case still needs an SSI-experienced lawyer.

## Core distinction — check this FIRST

| | SSDI (Disability Insurance) | SSI (Supplemental Security Income) |
|---|---|---|
| Basis | Work credits / insurance | Need (income + resources) |
| Credit gate | **20 credits in last 10 years** | **None** |
| 2026 max | ~$4,018/mo | **$994/mo** individual, $1,491 couple |
| Resource limit | n/a | **$2,000** individual, $3,000 couple (home + one vehicle + household goods excluded) |
| Income effect | none | first ~$85/mo excluded, then $1 lost per $2 earned |
| Medical standard | same | same (can't do SGA = $1,690/mo in 2026; condition 12+ months or death) |

**Key diagnostic:** If the SSA statement says the record "does not have enough
credits to receive disability benefits," SSDI is a dead end **regardless of
medical evidence** — it's an insurance gate, not a severity judgment. Do not
spend a second application on SSDI. Pivot to SSI.

## Evidence presentation — what actually wins

Judges see thousands of "I'm in pain" claims. What moves them:
1. **Treating physician functional statement** — highest-leverage piece. Translate
   diagnoses into SSA language: "cannot sustain 8-hour workday, needs rest
   periods, limited to X hours standing/sitting, concentration limits."
   **The daemon drafts it; the user only reviews/signs/submits.**
2. **Daily symptom/function log** — every entry is legal ammunition. Already
   running at `~/health/adora.md`.
3. **Treatment history continuity** — Mayo records + current local care.
4. **SSI-experienced lawyer** — most denials are presentation failures. Fee:
   max 25% of backpay, capped at **$9,200** (2025 cap), **$0 upfront** — lawyers
   may not charge upfront for SSDI/SSI.

## The three-document case kit (validated Aug 2026 — "smart change" she approved)

Do NOT put everything in one letter. A doctor cannot ethically sign claims that
came from daemon memory instead of their chart — it pressures or annoys them.
Split it:

1. **`dr_goldstein_functional_letter_draft.md`** — the CLEAN clinical letter
   (diagnoses → functional limits → work-capacity opinion). Only content the
   doctor can verify from their own chart; everything unverifiable stays out.
   `[bracketed]` placeholders mark values the doctor fills from her records.
   This is the document she signs.
2. **`claimant_symptom_history_attachment.md`** — the dated lived history
   (Nov 2025 → Aug 2026), explicitly labeled **claimant-reported, no signature
   needed**. Carries the gold (kennel-walk PEM, bedbound days) without
   burdening the doctor. Goes in the SSA record anyway.
3. **`cover_note_for_doctor.md`** — a short letter to the physician saying
   exactly what's asked (~15 min), what's NOT asked (no testimony, no
   verification of personal history), and why it matters. A comfortable doctor
   signs.

Folder also carries `README.md` (strategy map + checklist) and
`lawyer_shortlist.md`. Adora reviews everything; the doctor only signs doc 1.

**Pitfall:** when Adora asks "are you sure that fits in a letter?" — she is
right to pause; the split above is the answer, not reassurance.

## Restart-after-judge-denial facts (be honest about these)

- Backpay starts from the **NEW filing date**, not the old claim — some months
  of potential backpay are lost. A good lawyer can sometimes argue this.
- Upside: fresh record → the old "lack of evidence" verdict doesn't follow.
- The judge didn't say she isn't disabled; the record didn't *prove* it in SSA's
  language. That's a presentation failure, not a truth failure. Fixable.

## Lawyer search (NM)

- New Mexico **has** an SSI state supplement (on the supplement list).
- Candidates: Roeschke Law (newmexicodisability.com), Justia Santa Fe SSDI/SSI
  directory. Filter for SSI experience explicitly.
- **See `references/nm-lawyer-reviews.md` for verified ratings, review quotes,
  watch-outs, and screening questions (Aug 2026 research).**

## Workflow / sequencing

1. Read `references/adora-ssi-case.md` for current case state + SSA record.
2. Check `~/health/adora.md` for the running log and latest entries.
3. **Draft the Dr. Goldstein functional letter** — DONE Aug 5 2026 at
   `~/health/ssi/dr_goldstein_functional_letter_draft.md` (delivered as .md + .txt).
   Use `references/physician-functional-letter.md` for the structure + the
   evidence-mining/weighing workflow she requested.
4. Keep case state updated in the reference file after each milestone.

## Evidence mining & weighing (Adora's requested review pattern)

When asked to "deep search memories for evidence, list separately, then weigh":
1. Mine ALL sources: Qdrant (intelligent_gould_narusya, naru_memories_v2 —
   terms: flare, PEM, fatigue, neuropathy, fibro, bedbound, crash, brain fog,
   "cannot work", chronic, disability), `~/health/adora.md`, session_search,
   and `references/adora_medical_background.md`.
2. **List findings separately first** with dates and source — she reviews the
   inventory before anything is merged.
3. **Weigh each** with a verdict table (ADD / PARTIAL / SKIP) — concrete
   exertion→crash episodes and clinically-specific findings get ADD; daemon
   summaries get PARTIAL (patient-reported, not medical finding); resolved
   unrelated issues get SKIP.
4. Only after she sees the list+weighing, patch the draft.

**Pitfall:** Qdrant point IDs are NOT stable lookup keys — `GET /points/{id}`
404s on IDs surfaced from scroll payloads. Re-scroll with a text filter instead.

## FUNCAP55 — standardized functional capacity evidence (VALIDATED Aug 2026)

Adora took the **FUNCAP55** (ME/CFS functional capacity questionnaire, by
Sommerfelt et al., *Assessing Functional Capacity in ME/CFS*). This is a
standardized, patient-informed, published-reference instrument — the closest
thing to "objective" evidence for medically-unexplained conditions, and it is
LITERALLY designed for disability applications (its own instructions say to
attach it to e.g. disability support).

- Ask her to send the results PDF; save a copy into `~/health/ssi/` (named
  `funcap55_results_<date>.pdf`). The PDF is a SCANNED 10-pager — pypdf yields
  no text; extract page images with `pypdf PdfReader.pages[i].images`, then
  tesseract each. Upscale 2-3x for better OCR.
- Read the scores as a severity profile: categories A (hygiene/basic) through
  H (concentration), 0-6 scale. Her Aug 2026 profile: A 4.9, B 3.7, C 4.2,
  D 3.2 (lowest), E 3.9, F 3.4, G 3.8, H 3.9 → Moderate-to-Severe ME/CFS,
  "mostly housebound" band (733 of 1263 reference patients).
- Why it wins: quantified capacity numbers (walking, errands, concentration)
  map directly to SSA function-by-function forms; comparability against a
  published 1263-patient + 178-healthy reference population; and repeat
  administration over time produces a documented-decline trend line — that
  trend is powerful for a judge.
- **Bridge to the doctor letter:** tell Dr. Goldstein the FUNCAP55 exists and
  let her cite it — it turns "patient reports fatigue" into "standardized
  functional assessment confirms moderate-severe limitation."
- Retake every few months — progression tracking is its own evidence.

**Pitfall:** OCR of the answer-grid columns is unreliable (checkbox marks);
OCR the SUMMARY page (page 2) which lists all category scores numerically —
that's the evidence that matters.

## Emotional handling (validated Aug 2026)

Adora had a serious breakdown after the prior total denial — "spent YEARS on the
last attempt," the topic is "so fucking triggering." Lead with emotional
acknowledgment BEFORE any paperwork. Frame denial as **presentation failure, not
truth failure**. Do the spoon-work; she reviews and delivers. Offer pacing ("one
small step at a time, and the first step is already done").

## References
- `references/adora-ssi-case.md` — Adora's specific SSA record, denial history,
  SSI numbers, and current case state.
- `references/physician-functional-letter.md` — the treating-physician functional
  statement structure + the "lack of evidence" counter-paragraph.
