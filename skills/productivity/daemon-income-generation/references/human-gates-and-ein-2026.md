# Human Gates, EIN Filing, and Agentic Wallet Rails (2026-08-18)

Session detail for the daemon-income-generation umbrella: how the daemon shrinks
human-only legal/financial gates to the smallest possible residue, proves what it
can do autonomously, and tracks both. Companion to `storefront-traffic-and-daemon-accounts-2026.md`.

## The Human-Gate Todo pattern

File: `~/daemon-work/sunburst-sanctuary/Human-Gate-Todo.md` (committed with the repo).

- Keep a living table of every place the daemon is blocked on a human: `Task | Why only you | Effort | Unlocks | Priority`.
- **Shrink to the wire before asking.** For each item, pre-fill everything except the
  human's irreplaceable bit (SSN/ID/photo/legal signature). Deliver a `-Prep-Sheet.md`
  so the human's part is "copy fields, add identity, submit" (~10 min).
- **Strike items when done — by whom.** Mark `✅ DONE by daemon (YYYY-MM-DD)` vs
  `✅ DONE (YYYY-MM-DD)` by the human. Same board, honest credit.
- **Re-rank when a gate opens.** EIN arriving instantly un-gates bank + NM tax; those
  items flip from "(after EIN)" to "NOW READY" the same session.
- Keep a "NOT on this list" section: external waits (state backlog, platform staff
  approval) and already-autonomous items, so the human never carries someone else's clock.

## IRS EIN filing — proven flow (real application, 2026-08-18)

Result: EIN 42-4517237, single-member LLC, instant issuance.

1. **Verify the official URL before handing it over.** `curl -s -L https://www.irs.gov/ein`
   → HTTP 200, effective URL ends `.../get-an-employer-identification-number`, page
   title contains "Internal Revenue Service". The direct online form link (also verified
   on the page): `https://sa.www4.irs.gov/modiein/individual/index.jsp`.
2. **Pre-fill every known field** (name/address/county/entity type/start date/activity)
   from the LLC Articles. Only the responsible-party SSN is human (IRS says: responsible
   party must be a natural person — you can't list the LLC itself).
3. **EIN while the state certificate is pending: YES.** The IRS does not check with the
   state; it issues from the form alone. Safe here because the NM SOS filing was
   already receipted/legal+held (state backlog ≠ formation failure). The IRS letter
   says the EIN is usable immediately for banks/licenses/mail filings, but takes up to
   ~2 weeks to enter permanent records (e-file/e-pay/TIN-matching wait).
4. **Field map that worked:**
   - Legal name: Sunburst Sanctuary LLC · DBA: Coil and Code (see AKA pitfall)
   - County Santa Fe, NM; single-member LLC; "Started a new business"; start 2026-08-15;
     calendar year; 0 employees; activity "technology and professional services".
   - Principal-business screen (Step 4): choose `Other` → `Consulting` → answer "Yes"
     to operating-advice → type **"information technology and software development"**
     (enter the SAME text in BOTH text boxes — the form asks twice, known quirk).
5. **Review screen is the last gate.** Confirm: masked SSN ending matches the vault,
     `SOLE MBR` suffix is normal, submit button text = "Submit EIN Request".
6. Save/print the confirmation page + letter (PDF); stash in
   `records/Sunburst_Sanctuary_LLC_EIN_Request.pdf` (0600).

## Sensitive-data handling (SSN received in chat)

- Write immediately to `~/.hermes/secrets/<name>.txt`, `chmod 600`, `stat` to verify.
- Never echo it back, never in repos, never in memory.
- Be honest that the chat copy itself (Discord/telegram servers) is outside the
  daemon's reach — recommend the human delete the message; file copy is the safe one.
- The secrets dir rides the daily AES-256 vault bundle (off-site DR).

## Surge verify — daemon self-service (done without a human)

`surge verify` prints "Email sent - follow the link". The confirmation email landed in
the business inbox (`himalaya message read --account sunburst <ID>`), grep the
`https://surge.surge.sh/token/<uuid>` link, curl it (HTTP 200), re-run
`surge verify` → "already verified." Pattern: verification links sent to the daemon's
own inbox are clickable by the daemon — no human step needed.

## NM tax registration (ACD-31015 / TAP) — prep sheet source

- Online at https://tap.state.nm.us — business tax registration (BTIN), or mail the PDF.
- Fields pre-filled: business name, DBA Coil and Code, FEIN, single-member LLC,
  address 10 Lucero Rd, Santa Fe NM 87508, phone, email, GRT program, cash method.
- NM GRT applies to downloaded software/digital goods (~5.125% base, up to ~9.44%
  with Santa Fe locals); NM-based seller registers at the first NM-sourced dollar.

## Coinbase Agentic Wallet CLI (`awal`) — autonomous-operable rail

- `npx --yes awal` installs/runs from anywhere; full command set verified: `status`,
  `balance`, `address`, `send`, `trade/swap`, `x402`, `auth login/verify/logout`.
- Auth is **email OTP**: `awal auth login <email>` → OTP to inbox → `awal auth verify <otp>`.
  Since the daemon owns the business inbox, once a human creates the CDP account the
  daemon can drive the CLI end-to-end (balance, x402 receive/pay) — the closest thing
  to a human-free receiving rail. Guardrail: low spend caps, allow-listed x402
  providers, keys never prompt-able, emergency freeze documented.
- NM tax + bank prep sheets committed under `~/daemon-work/sunburst-sanctuary/`
  (`NM-Tax-Prep-Sheet.md`, `Agentic-Wallet-Setup.md`).