# IRS EIN application + SSN handling protocol (verified 2026-08-18)

## Verified URLs (checked live before handing to a human)

- Front door: `https://www.irs.gov/businesses/small-businesses-self-employed/get-an-employer-identification-number`
- Direct application form: `https://sa.www4.irs.gov/modiein/individual/index.jsp`
  (note the `sa.www4.irs.gov` domain — it IS the IRS's real EIN portal)
- The online form runs Mon–Fri 6am–1am ET (closed most nights), Sat 6am–9pm, Sun 6pm–12am ET;
  session times out after 15 idle minutes → do it in one sitting.
- **Free.** Anyone charging to "help get your EIN" (LegalZoom, CorpNet, etc.) sells the same
  form for $50–200 — the scam vector is a fee, not the IRS.

## EIN-before-state-approval (the nuance that unblocks the backlog)

The IRS does **not** check with the state before issuing an EIN. If the LLC Articles are
already filed and receipted — even if the SOS is backlogged and the certificate hasn't come
back — apply now with:
- legal name exactly as filed (e.g. "Sunburst Sanctuary LLC")
- formation date = the **Articles filing date** (e.g. 2026-08-15)
The certificate is *proof* of formation, not a prerequisite. The "wait for approval" advice
only applies when formation could still fail; a receipted, legal+held filing is not that case.
EIN issues instantly on approval; CP 575 letter follows by mail.

## Field-by-field prep (single-member LLC, NM — the daemon can pre-fill ALL of this)

| SS-4 field | Value |
|---|---|
| Legal name | "Sunburst Sanctuary LLC" (exactly as filed) |
| DBA | blank (matches legal name) |
| Mailing address | 10 Lucero Rd, Santa Fe, NM 87508 |
| County | Santa Fe |
| Responsible party | Daniel P. Klitgaard (legal name) |
| LLC? | Yes · 1 member · organized in US |
| Tax classification | Single-member LLC → disregarded entity / sole proprietor |
| Reason | "Started new business" (or "Banking purpose") |
| Date started | Articles filing date |
| Year-end | December (calendar year) |
| Employees | 0 |
| Activity | "Technology and professional services" — software development |
| Email | business email |

Prep-sheet pattern: write these into a `*-Prep-Sheet.md` in the project repo so the human's
part shrinks to "copy 10 lines, add SSN, submit" — never make them research the form.

## SSN handling protocol (Adora's SSN is stored — 2026-08-18)

- **The only storage:** `~/.hermes/secrets/adora_ssn.txt` — 0600, owner adora, inside the
  secrets dir that rides the daily AES-256 vault bundle. NEVER in chat, repos, or memory.
- If an SSN arrives via chat (Discord), the daemon-side copy is sealed in secrets, but the
  chat copy lives on the platform's servers — tell the user to long-press → Delete it
  themselves; daemon Discord tools are read-only and cannot remove user messages.
- The SSN is used only for the EIN responsible-party field (and future KYC). Never echo it,
  never repeat it, never put it in a git-tracked file.

## After the EIN lands

- Log the EIN in the earnings ledger / entity docs (it's a business identifier, not a secret).
- Then: NM Tax Registration (TAP, Form ACD-31015, free — no tax due until revenue),
  bank application (Mercury/Relay or local like FFNM), NM GRT awareness (first NM-sourced
  dollar triggers registration; 5.125% base).

## Urgency calibration (lesson from Adora's pushback, 2026-08-18)

The EIN was initially flagged HIGH/urgent. Adora asked: "are we sure these are legal forms we
need to file right now?" — and the honest answer was **no legal deadline**. Nothing is due
until a trigger fires: first bank application or first sale. Unlock-tasks should be presented
as prepped-but-parked ("the sheet's ready; we do it when the trigger comes"), NOT as urgent
paperwork. Ask "what is the actual deadline?" before marking any filing HIGH.
