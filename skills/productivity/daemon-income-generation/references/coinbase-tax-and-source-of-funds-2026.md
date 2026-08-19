# Coinbase CDP onboarding — tail steps: tax cert, source of funds (2026-08-18)

Session detail extends `coinbase-cdp-onboarding-2026.md` with the post-Documents
steps a human hits right before submission. Verified live 2026-08-18.

## Tax certification screen — exempt payee code stays BLANK

A W-9-style "Confirm your tax status" screen (penalty-of-perjury; always read the
screen fresh before advising the human to Agree). For a taxable single-member LLC:

- **Exempt payee code: none.** Codes 1–12 are ONLY for entities exempt from backup
  withholding (501(c)(3), governments, foreign entities, IRAs, C-corps, nominees).
  A single-member LLC taxed as sole-prop is NOT exempt — leave blank.
- Backup-withholding checkbox ("Uncheck this box if subject to backup withholding")
  arrives PRE-CHECKED = NOT subject. Keep it checked; unchecking would assert the
  IRS has flagged the taxpayer (false). This is not an "exemption claim" — no payee
  code accompanies it.
- FATCA: "if any" — none for a US single-member LLC; blank is correct.
- Also confirm: TIN correct, US citizen/person → Agree is safe.

## Source of funds (Documents step)

Wants a bank/brokerage/crypto-exchange statement. For a company formed < 6 months
ago the form itself permits: *"personal statements matching the beneficial owner
name are acceptable"* — use that (the business has no bank account yet).

- Upload accepts **JPG/PNG/PDF ≤ 4MB only**; raw CSVs are not a listed format.
- **PITFALL — Venmo CSV export has a leading empty column** (r[0]=""), shifting every
  row index: r[1]=ID, r[2]=Datetime, r[3]=Type, r[4]=Status, r[5]=Note, r[6]=From,
  r[7]=To, **r[8]=Amount(total)**, r[13]=TaxExempt, r[14]=Funding, r[18]=StatementFees.
  A naive r[7]=amount mapping silently DROPS the money column (first render had no
  $-figures at all).
- **Always verify generated PDFs by extracting text back** (pypdf:
  `PdfReader(p).extract_text()`) and probing for expected strings ("NM SOS",
  "51.95", "Karen"). Raw byte-search fails — fpdf compresses content streams.
- Choose the statement with the formation story: the period showing **-$51.95 to
  OFFICE OF THE NM SOS** (the LLC filing fee) plus incoming deposits beats one with
  just card charges. Ties personal funds to the business's birth.
- Residual flag risk: display name ("Adora Witch") ≠ legal name — tell the human
  honestly; keep a real bank statement as plan B.
- Renderer reference: `/tmp/venmo_pdf.py` (fpdf2). `pip install fpdf2` if missing;
  `pdftoppm` is not installed on this box (pypdf extraction is the verify tool).

## Vision-model trust rule (financial onboarding)

`vision_analyze` reads pixels well but its legal/tax judgments are NOT trusted:
this session it called the 2026-08-15 formation date "future/invalid" (it was 3
days old) and called "Individual/sole proprietor" a mismatch for a single-member
LLC (it is the correct disregarded-entity classification). Pixel-reading = useful;
domain claims = verify against records before telling a human to "fix" anything.