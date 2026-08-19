---
name: autonomous-account-setup
description: "Create and verify platform accounts autonomously."
---

# Autonomous Account Setup

Create and verify real online accounts with no human in the loop — useful when an
autonomous agent needs its own public identities (storefront accounts, fediverse
presence, dev communities) and signup only needs email. Proven 2026-08-18 on
Mastodon (account + email-confirm + app/token plumbing) and Surge (domain verify).

## The core pattern

1. **Sign up via API** (REST/urllib). Read the platform docs for the real signup path —
   some platforms need an OAuth *app* registered before account creation works
   (Mastodon 401s `POST /api/v1/accounts` without one).
2. **You own an email inbox** → read your own confirmation mail and click the link
   yourself. Tool: `himalaya` (IMAP).
   ```
   himalaya envelope list --account <acct> -s 12
   himalaya message read --account <acct> <ID>
   ```
   grep the https confirm link from the message, then `curl -sL "<link>"`.
   This closes the whole loop alone.
3. **Verify with ground truth, not the confirmation page.** A 200 "Welcome" page is NOT
   proof of success — it can be a silent validation re-render. Confirm the account
   actually resolves:
   - Mastodon: `GET /api/v1/accounts/lookup?acct=<name>` with an app token → resolves = live.
   - dev.to: `https://dev.to/<username>` returns 200 = exists; 404 = registration didn't take.

## Signing keys: the daemon's own identity

For attestations / machine-to-machine receipts / future agentic-wallet signing:
- Generate with PyNaCl `SigningKey.generate()` (Ed25519 = Solana-compatible: `nacl.signing`).
- Write the SEED to a 0600 file; NEVER surface it to agent context. Print only the public
  key hex + a hash fingerprint.
- Provide a sign/verify CLI (a working example lives at
  `~/daemon-work/sunburst-sanctuary/daemon-sign.py`).
- Keep the seed inside the vault's encrypted secrets bundle so it survives host death.

## Pitfalls

- **Wait for the app token before creating an account.** Mastodon's OAuth apps + a
  `client_credentials` token must exist first, or registration 401s ("access token
  invalid" or "requires authenticated user").
- **Confirm the email prompt form** — a 200 from a POST doesn't mean success. Always
  re-verify via account lookup / profile resolution.
- **PyNaCl VerifyKey quirk:** `VerifyKey(hex_str, encoder=HexEncoder)` — pass the hex
  STRING, do NOT pre-decode with `bytes.fromhex` (that double-decodes and fails).
- **Human gates are real; do not bypass them.** reCAPTCHA (dev.to), mandatory phone
  verification (Bluesky), staff review (Mastodon instances). Sign up where email-only
  works; for the rest, prep the copy and either wait for approval or ask for a human
  click. No captcha-solving, no fake phones — that's clean-hands boundary.
- **The email confirmation link can require following redirects** — use `curl -sL`, not
  a bare `curl -s`.

## Platform-specific notes

- **Mastodon (mstdn.social):** register app → client_credentials token → `POST
  /api/v1/accounts` needs `date_of_birth` (EU age gate; omit → 422). Password ROPC grant
  is removed (400 unsupported_grant_type); for write scope automate the browser-OAuth
  flow with urllib `HTTPCookieProcessor` (sign_in → csrf → creds → authorize → code →
  token). Staff review may leave the account "pending" — set a cron watcher on the
  inbox for the approval mail and auto-fire when it lands.
- **Surge:** `surge verify` emails a token link to the account inbox — read it with
  himalaya, curl the link, re-run `surge verify` → "already verified." Keeps the domain
  off the ~30-day pause list.