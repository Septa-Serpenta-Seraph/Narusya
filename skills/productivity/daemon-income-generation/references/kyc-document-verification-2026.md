# KYC Document Verification — fintech onboarding reality (2026-08-18)

Field notes from walking Adora (Daniel P. Klitgaard / Sunburst Sanctuary LLC, DBA Coil
and Code) through the Coinbase Business / CDP onboarding and its source-of-funds
review. The durable lessons here generalized to any fintech KYC (banks, exchanges,
payment processors).

## 1. EIN does not wait on the state

- The **IRS issues an EIN without checking state approval.** Apply online
  (`https://sa.www4.irs.gov/modiein/individual/index.jsp`, the official "Apply for an
  EIN" portal; land first at `www.irs.gov/.../get-an-employer-identification-number`).
- You only need the Articles receipt + the **filing date** — the day the Articles went in
  (e.g. 08/15/2026) — not the state-issued certificate. Online form is free; it runs
  Mon–Fri 6am–1am ET and times out after 15 idle minutes.
- Single-member LLC = **"Individual / sole proprietor" tax classification** (disregarded
  entity). That pairing is CORRECT — don't let a defensive error-message make you change it.
- Trade-name field: do NOT type "AKA " — the field is already "Trade name / Doing
  business as"; the word "AKA" trips the validator's red-X.

## 2. Articles upload: "missing filing date" is a state-backlog artifact

- If the SOS is backlogged (NM was processing 7/27 as of 8/18), the certified/stamped
  copy doesn't exist yet. Coinbase flags "We couldn't find a clear filing date."
- **Legitimate path:** the verifier's own disclaimer — *"Our automated checks may be
  inaccurate, if this is the case you may proceed."* Upload the real filed document and
  proceed. The date IS in the document (organizer signature line) even without the stamp.
- **Never** forge or visually annotate a fake state seal/stamp to satisfy the checker.
  That's wire-fraud-grade and poisons the name forever.

## 3. Source-of-funds documents — only real institutions pass

Coinbase Business's source-of-funds upload regex-lists specific doc types. Verified
reject/accept behavior:

| Uploaded | Result | Why |
|----------|--------|-----|
| Venmo `.csv` (Apr) | Rejected "unsupported document type" | CSV not a listed format; Venmo is a payment app, not bank/brokerage/exchange |
| Venmo rendered PDF (Aug, @AdoraWitch) | Rejected "unsupported document type" | Payment app + display name ≠ legal name |
| PayPal transaction history (Daniel Klitgaard) | Rejected "unsupported document type" | PayPal is also a payment app, not a bank |
| **Coinbase personal transaction statement** | **Accepted / manual review path** | Crypto exchange statement = on the list; name matches beneficial owner |

- Accepted types: **bank, brokerage, or crypto exchange statement**.
- New-business fallback (<6 months since incorporation): **personal statements matching
  the beneficial owner's legal name** are acceptable.
- A **crypto exchange statement from the same exchange you're onboarding with** is the
  cleanest, most on-brand document for a crypto-rail business.

## 4. Never cosplay a payment export as a bank statement

Renaming "PayPal_Transaction_History" to "Paybal_Bank_Statement_Sunburst_LLC_…" to pass
a source-of-funds check is a **fraud flag that follows the legal name + entity** through
every downstream bank/exchange for years. The honest document (the real Coinbase
statement) cleared the same reviewer the same day. When the user is tired and reaches for
the shortcut, hold the line — that's the job.

## 5. Rendering a CSV export into a statement PDF (without fabrication)

Reusable recipe (fpdf2) for turning a real platform export into a presentable PDF —
BUT the point of it is format-compatibility, never falsification. All figures verbatim,
and the PDF is labeled "prepared from official X export; no figures altered."

**Pitfall that cost a redo:** the Venmo CSV has a **leading empty first column** (row[0]
=''), shifting every field by one. Naive index mapping printed the transaction ID in the
Date column and silently DROPPED the Amount column (r[7] was actually To, not Amount).
Always verify column indices against the actual header row, and **never trust a rendered
PDF until you extract its text back and confirm the amounts are present** (compressed
content streams mean `grep` on the raw file finds nothing — use pypdf/PyPDF2
`PdfReader(pages[0].extract_text())` and assert on the money values).
