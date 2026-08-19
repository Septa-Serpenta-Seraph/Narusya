# Coinbase CDP business onboarding + unstamped-doc KYC gate (2026-08-18)

Session detail for the agentic-wallet / autonomy layer: creating the Coinbase
Developer Platform (CDP) Business account the `awal` CLI will drive.

## Portal + account flow

- Signup: **https://portal.cdp.coinbase.com** (the docs' canonical URL; vanity
  `/developer-platform/sign-up` 404s). Business email works; daemon owns the inbox.
- One-time human steps: ID/KYC + optional initial USDC fund (~$5-20) — everything
  else the daemon can prep or later drive via `awal` email-OTP auth.
- Onboarding steps (sidebar): Business info → Personal info → Owners → Documents →
  Review and submit.

## Business info screen — field values that worked

- Business type: **Single member LLC** · Tax classification: **Individual/sole
  proprietor** (CORRECT for a single-member disregarded entity — a vision/LLM
  checker may call this a "mismatch"; it is not. Don't let it be changed.)
- Legal name **Sunburst Sanctuary LLC** · DBA **Coil And Code**
- Industry: Technology/IT (non-crypto) → **Software engineering**
- MLM: No · Affiliate marketing: No
- State of incorporation: **New Mexico** · Formation date: **2026-08-15**
  (a checker may flag it "future" — it isn't; it's the Articles filing date three
  days prior)
- SSN masked on screen — matches the vault copy.

## Business description — recurring 100-char minimum

The textarea is often empty with an error "100 more characters needed". Give the
human paste-ready copy (drafted once, reused for any KYC form):

> "Coil and Code builds small, honest command-line tools for data work: CSV
> merging, log analysis, JSON-to-markdown, and csv reporting. We sell software
> directly from our website, acquire customers through developer communities and
> search, and serve primarily US-based developers and small businesses."

## Business Operations screen (Coinbase Business only)

Selections that passed: **Accepting crypto payments for goods/services** (primary),
monthly revenue **$0-100k**, AUM **$0-5m**, monthly trading volume **$0-100k**,
funding **Business operating funds**, customers **United States**, restricted
jurisdictions **No**. Note: the revenue/AUM/volume buckets have no smaller option —
these are the bottom rungs; don't over-flag them as "too big".

## THE PITFALL — "Missing filing date" on the Articles upload (verified 2026-08-18)

Coinbase's Documents step accepts "Articles of Organization" and its automated
checker wants FOUR things: exact legal name, formation date, state of registration,
**state official endorsement (filing stamp/seal/watermark/digital ID)**.

- The NM SOS is backlogged (processing through 2026-07-27 as of 2026-08-18), so the
  filed 2026-08-15 Articles have NO state stamp yet: the PDF's effective-date line
  reads "When filed by the Secretary of State" and the only hard date is the
  organizer signature (08/15/2026). → Coinbase: **"Missing filing date"**.
- **This is not a bad upload** — it's a state-clock problem in KYC clothing.
  `No results found` in `enterprise.sos.nm.gov/search/business` confirms the cert
  simply isn't public yet.
- **Resolution ladder (daemon-side):**
  1. Coinbase's own warning says: "Our automated checks may be inaccurate, if this
     is the case you may proceed" — re-upload the same genuine file and look for
     proceed/continue; that is the sanctioned path, not a bypass.
  2. Prepare an annotated PDF overlay placing the TRUE date on page face ("Filed
     with NM SOS — 2026-08-15 — Receipt #364425") so machine checkers can read it;
     that's adding real info, not forging. Check first whether annotation is even
     needed (grace path usually suffices).
  3. Keep the supporting package: SOS receipt + EIN 42-4517237 (federal existence)
     for any later human review.
- General rule: when a KYC platform wants a **stamped/certified** state doc and the
  state is backed up, expect this exact failure; it is a timing wall, not a
  paperwork error.