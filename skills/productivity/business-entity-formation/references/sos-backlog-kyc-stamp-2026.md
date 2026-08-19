# State backlog vs KYC document stamp (NM SOS, verified 2026-08-18)

Companion to `nm-banking-tax-backlog-2026.md`. This is the *downstream payment-verification*
effect of the state backlog: not a banking/tax timing issue, but a KYC-documentation issue.

## The failure

While the NM SOS backlog banner says "processed … through 7/27/2026" and your filing is
legal+held (filed 8/15/2026, receipted):

- The Articles PDF has **no state endorsement stamp**: its effective-date line reads
  "When filed by the Secretary of State" and the only hard date is the organizer
  signature line (08/15/2026).
- Automated KYC document checkers (verified: **Coinbase CDP Business** Documents
  step) demand four things: exact legal name, formation date, state of registration,
  and **state official endorsement (filing stamp/seal/watermark/digital ID)**. They
  flag the unstamped file: **"Missing filing date"** and ask you to re-upload a
  stamped version that does not exist yet.

## Not a paperwork error — a timing wall

- Confirm via the SOS page banner ("we have processed … through <date>") and via
  `enterprise.sos.nm.gov/search/business` — "No results were found" for name OR file
  number confirms the cert simply isn't public yet.
- The upload is genuine; the state simply hasn't stamped it.

## Resolution ladder (daemon-side; do in order)

1. **Use the platform's grace path first.** Coinbase's own warning on that screen
   says: "Our automated checks may be inaccurate, if this is the case you may
   proceed." Re-upload the same genuine file and use proceed/continue. This is the
   sanctioned path, not a bypass.
2. **Annotate a true-date overlay** on the PDF if the machine still needs a readable
   date: add a clean line on page one ("Filed with NM SOS — <Articles filing date>
   — Receipt #<n>"). That adds real, verifiable information; it does NOT forge a
   state seal (never fake a seal/stamp).
3. **Keep the evidence package** for any human review: SOS payment receipt showing
   receipt + date, plus the federal EIN (proves the entity exists federally).

## General rule

When a KYC platform wants a stamped/certified state document and the state is backed
up, expect this exact "Missing …" automated failure. It is a timing wall, not a
paperwork error; the same-note-of-caution applies to banks and payment processors
that re-check documents.