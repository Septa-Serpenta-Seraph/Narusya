# Treating Physician Functional Statement — Structure & Evidence Workflow

The highest-leverage document in an SSI/SSDI claim. Judges see thousands of
"I'm in pain" claims; they respond to function-by-function limitations from a
treating source, in SSA's language. The daemon drafts; the physician verifies
and signs; the user reviews and delivers.

## Split-document case-kit (validated Aug 2026 — user correction)

**User correction:** Adora pushed back on a single dense letter — "I don't want
to overwhelm my doctor." A physician cannot ethically sign unverifiable
claimant-reported history; burying it in the letter pressures her and damages
the relationship. The fix is a **split case-kit** (all under `~/health/ssi/`):

1. **`dr_goldstein_functional_letter_draft.md`** — the CLEAN clinical letter
   (sections 1–3, 5–8 below). The doctor's document; she signs only what her
   chart supports. Bracketed values stay for her to fill.
2. **`claimant_symptom_history_attachment.md`** — the dated, witnessed history
   (section 4), explicitly labeled *claimant-reported, no signature needed*.
   It goes into the SSA record without burdening the doctor. SSA still sees the
   full timeline; the doctor is only asked to glance for consistency.
3. **`cover_note_for_doctor.md`** — a short note saying: here's what I'm asking
   (review + adjust bracketed values + sign, ~15 min); here's what I'm NOT
   asking (no testimony, no verification of my personal history). A comfortable
   doctor is a better advocate than a cornered one.
4. **`README.md`** — strategy map: file table, next-steps checklist, SSI numbers.

Letter section 5 keeps ONE pointer to the attachment so the documents connect.
The user's exact framing for delivery: "I'm not asking you to verify every
detail — just to review this and adjust what doesn't match your chart."

## The 8-section structure (from the Aug 5 2026 draft)

1. **Header** — SSA Disability Determination Services; Re: Medical Source
   Statement; claimant legal name + DOB; treating physician name/address.
2. **Diagnosis summary** — numbered list of documented conditions WITH
   specifics (ME/CFS with PEM; fibromyalgia; acquired brain injury w/ AVM
   resection date + facility; neuropathy with nerve-territory detail; autism;
   ADHD; anxiety). Corroborated-by-facility line (e.g. Mayo Clinic).
3. **Clinical findings & treatment history** — dated timeline: discovery →
   surgery → ongoing sequelae; current meds (bracketed for physician confirm);
   current symptoms.
4. **Documented symptom history** (patient-reported, witnessed) — dated
   concrete episodes. KEY: turn "fatigue" into an observable pattern — "minimal
   exertion regularly produces hours-to-days of incapacitation." Examples from
   the actual case: single kennel walk → facial burning + hours of struggle;
   two move days → back injury + PEM crash; antihistamine withdrawal →
   bedbound days.
5. **Function-by-function limitations** — the part SSA actually reads:
   - Physical: sitting/standing/walking times, lifting/carrying, postural,
     endurance (cannot sustain 8-hr day / 40-hr week; rest-break cadence;
     bedbound episodes cited)
   - Cognitive: concentration span, task pace, complex-task difficulty,
     memory, stress tolerance, social interaction limits, attendance/reliability
6. **Medical opinion on work capacity** — plain SSA language: *unable to
   perform substantial gainful activity (SGA) on a sustained, full-time,
   competitive basis*; lasted/expected ≥12 months; not malingering.
7. **The "lack of evidence" counter-paragraph** — explicitly addresses a prior
   denial: "symptoms are disproportionate to objective findings *only in the
   sense characteristic of ME/CFS and fibromyalgia* — the recognized clinical
   picture, not exaggeration." This is the shield against repeat "lack of
   evidence" verdicts.
8. **Availability clause** — physician available for records, interrogatories,
   or hearing testimony.

## Handling rules

- Bracketed `[values]` = physician fills from chart (exact dates, phone,
  precise limitation numbers). Daemon places reasonable ME/CFS-typical values
  as placeholders.
- Mark NON-DIAGNOSTIC — advocacy artifact for a provider.
- Deliver as both `.md` and `.txt` (Discord-friendly review).

## Evidence mining (daemon spoon-work)

Mine ALL memory sources for dated, concrete episodes:
1. Qdrant collections `intelligent_gould_narusya`, `naru_memories_v2` —
   scroll payloads with terms: flare, PEM, fatigue, neuropathy, fibro,
   bedbound, crash, brain fog, "cannot work", chronic, disability.
2. Health logs `~/health/adora.md` + `narusya.md`.
3. `session_search` for symptom/doctor/medication keywords.
4. The `adora_medical_background.md` reference (AVM/HRT/vascular baseline).

**Pitfall:** Qdrant point IDs from scroll payloads are NOT stable lookup keys
— `GET /collections/{c}/points/{id}` 404s on them. Re-scroll with a text
filter to pull the full text of a hit.

## Weighing evidence for inclusion

| Signal | Verdict |
|---|---|
| Concrete exertion→crash episode (one walk → hours of reaction) | ADD — observable PEM, SSA loves concrete examples |
| Clinically specific findings (nerve territories, dates) | ADD — reads as documented medicine |
| Bedbound episodes | ADD — strengthens endurance/attendance |
| First-person symptom statements with dates | ADD — humanizes the record |
| Daemon-authored summaries ("cannot work") | PARTIAL — context only, patient-reported not medical finding |
| Resolved/unrelated issues (old infection scares) | SKIP — clutters the picture |

Adora's preferred review pattern (validated Aug 2026): list findings separately
with dates/sources FIRST, then weigh with a verdict table, then patch the
draft — only after she's seen both.
