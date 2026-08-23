# NM Post-Formation: Tax Registration + Business Bank (verified 2026-08-22)

Hands-on verified flow for Sunburst Sanctuary LLC (NM). Reuse for any NM entity
(Coil&Code, Narusya LLC, Vesper LLC).

## 1. Certificate of Organization (the "backlog" end)
- NM SOS backlog DOES clear eventually. Filing approved 08/15/2026, Certificate +
  Notice of Filing Approval landed 08/21/2026 (out-of-the-blue user upload, no portal
  polling needed). Archive both PDFs to `records/` in the project repo.
- Letter says: if status is **"Pending Initial Report"** file an initial report within
  30 days. BUT the portal's **My Business Work Queue** showed status **"Approved"** →
  no initial report demanded. Always check the WORK QUEUE (enterprise.sos.nm.gov →
  login → queue) before chasing a form. Forms are **online only** — no paper.
- LLCs also have a NEW **triennial report** under HB 0281 (eff. 7/1/2024), still being
  operationalized — the portal presents whichever applies; due date authoritative there.

## 2. TAP portal registration (tap.state.nm.us) — the real quirks
- **Account Validation wall:** using the "existing filer" path with a first-time SSN
  errors with "It appears you have not registered with New Mexico before." Do NOT call
  the number; instead find the **New Business Registration / new-customer** flow (the
  multi-step wizard with Introduction → Registration → ... which accepts first-timers).
- **Business Taxes step (yes/no screening):** flip **"Will you engage in business in
  New Mexico?" → YES** — that is what creates the Gross Receipts Tax (GRT) account.
  Leave all other yes/no (wages, withholding, mobile telecom, automotive, insurance)
  at NO for a single-member software shop.
- **Officer/owner screen:** ownership % defaults to 0.00 — set to **100.00** for a
  single-member owner or compliance flags it.
- **NAICS (2022 revision — IMPORTANT):** software publishing is **513210**, NOT the
  old 511210 (renumbered in NAICS 2022). Secondary for automation/custom work:
  **541511** (Custom Computer Programming Services). Use the "Find Code" search;
  the confirm dialog paraphrases the industry — verify it matches before Yes.
- **Short description:** "Software publisher and custom automation services — creating
  developer tools, CLI utilities, and data-processing software sold online." or the
  tighter "Developer tools and automation software."
- **Filing frequency:** chosen **Monthly** (due by the 25th). Semiannual is the
  low-burden alternative for a near-zero-revenue shop; avoid Casual/Temporary.
- Outcome: instant approval, account ID like `03729639006-GRT`, $0.00 balance,
  Registration Certificate under TAP **Letters tab**. Confirmation PDF → save to records.
- GRT applies to downloaded software/digital goods in NM (FYI-265 — e-delivery =
  taxable license). NM-based seller owes on NM receipts from first dollar.

## 3. Reminder cron pattern (set 2026-08-22)
- Monthly GRT filing check on the **15th at 10:00** — a smart job that reads records/
  ledger for evidence the prior month's filing exists, and outputs **exactly [SILENT]**
  when filed (else a 2–4 sentence nudge). Idempotent, evidence-driven, no nagging.

## 4. Mercury bank onboarding (verified live 2026-08-22)
- Docs needed: (1) formation document — **Certificate of Organization** is NM's
  equivalent of Articles; (2) **EIN proof** — CP-575 letter, 147C letter, stamped
  SS-4, or an **IRS website screenshot** of the EIN confirmation (accepted; the online
  CP-575 letter may lag); (3) owner **US gov ID/passport** for every ≥25% owner.
- Flow gates: restricted-industry compliance list → select **"None of the above"**;
  company verify screen (legal name, US, phone, website); industry **Software/Dev
  Tools**, type **LLC**.
- **Social/website presence fields:** user preference — give **Mastodon
  (https://mstdn.social/@coilandcode)** and the **storefront
  (https://coil-and-code.surge.sh)**; do NOT hand over the GitHub org URL.
- Mercury = fintech through FDIC partner banks (Choice Financial Group, Column N.A.);
  conditional OCC national-bank charter April 2026 (pending). Not FDIC-"direct."
- **Daemon autonomy split (agreed):** read/reconcile/inbound watch = fully autonomous
  via API; **outbound money movement = daemon prepares, human confirms** — deliberate
  guardrail, not a limitation.

## Records layout (keep current)
- `~/daemon-work/sunburst-sanctuary/records/` = Certificate, Notice of Approval,
  EIN request, TAP confirmation, (later) stamped GRT filings, bank docs.
- Ledger `earnings-ledger.md` carries every unlock with date + record path.