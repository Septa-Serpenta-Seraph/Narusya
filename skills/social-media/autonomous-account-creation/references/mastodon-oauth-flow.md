# Mastodon OAuth Flow — full autonomous state machine (verified 2026-08-18, mstdn.social)

Goal: account + write token + first post with zero human hands, using a readable inbox
(himalaya) and stdlib urllib. This exact sequence worked in production.

## Prereqs
- Business email with IMAP access via himalaya (`himalaya account list`)
- `~/.hermes/secrets/` dir (0600) for creds
- Instance choice matters: probe `GET {inst}/api/v2/instance` first.
  - mstdn.social: open registration, requires `date_of_birth`, staff approval.
  - fosstodon.org: INVITE ONLY (checked 2026-08-18) — skip.
  - hachyderm / infosec.exchange: had registration but verify.

## Steps
1. **Create OAuth app**
   `POST {INST}/api/v1/apps`
   body: client_name, redirect_uris=`urn:ietf:wg:oauth:2.0:oob`, scopes=`read write follow push`, website
   → client_id + client_secret. STORE 0600.

2. **App token** (required for account creation):
   `POST {INST}/oauth/token` grant_type=client_credentials, scope=read write
   → access_token (the "app token").

3. **Create account**:
   `POST {INST}/api/v1/accounts` WITH Authorization: Bearer <app_token>
   body: username, email, password, agreement=true, locale=en
   - **`date_of_birth` is required** by mstdn.social (EU-style age gate): add YYYY-MM-DD.
   - `reason` helps human approval ("small shop, autonomous operator, no spam").
   - 401 "The access token is invalid" = you skipped step 2 (app token).
   - 422 = missing required field (read the error details JSON).

4. **Email confirmation** (PITFALL: server reports success but the account needs mail):
   - `himalaya envelope list --account sunburst -s 15` → find "Mastodon: Confirmation instructions"
   - `himalaya message read --account sunburst <ID>` → grep
     `https://mstdn.social/auth/confirmation?confirmation_token=...`
   - `curl -L` the link → 200/302 means confirmed.
   - Sanity check: `GET {INST}/api/v1/accounts/lookup?acct=<username>` with app token →
     200 + url means the public account exists. (404 on the WEB profile before approval is NORMAL.)

5. **Password grant is DEAD** (verified): `grant_type=password` → 400 unsupported_grant_type.
   Modern Mastodon requires the web OAuth flow. Do it with cookies:
   - GET `{INST}/auth/sign_in` → harvest `authenticity_token` + session cookie.
   - POST `{INST}/auth/sign_in` (email+password) — follow to `{INST}/home` when approved.
     While staff-pending, login lands on `/auth/edit` with "pending review" — stop and watch.
   - GET `{INST}/oauth/authorize?client_id=...&scope=read+write&redirect_uri=urn:ietf:wg:oauth:2.0:oob&response_type=code`
   - POST same URL with authenticity_token + `authorize=Authorize` (or `authorize=1`).
   - Parse `code=` from final URL/body → exchange at `POST {INST}/oauth/token` grant_type=authorization_code.

6. **Post**:
   `POST {INST}/api/v1/statuses` Bearer <user-token>
   body: status=<text>; header `Idempotency-Key` to prevent duplicate launch posts.
   URL in the response = ground-truth proof.

## Watchdog (staff-approval pattern)
The account exists but POSTing fails until humans approve. Solution: no_agent cron
(`mastodon-approval-watch.py`, every 60m, deliver origin):
- Load inbox; look for non-confirmation mail from the instance matching
  `approv|welcome|accept|activ`. If none → exit 0 silently (no delivery).
- If found and `sunburst_mastodon_token.json` absent → run steps 5–6, print posted URL
  (cron delivers it). If a token exists → exit silently forever.

## Verification rules
- Only `xurl`-style real API responses count as proof, and here:
  `lookup` 200 + `statuses` URL in JSON = success.
- A "Welcome!"/200 re-render after dev.to-style form posts is a validation echo, not proof.

## Secret hygiene
- `~/.hermes/secrets/sunburst_mastodon.txt` (password), `_app.json` (client_id/secret),
  `_token.json` (user token) — all 0600.
- Never print the password or token headers. Wipe /tmp helpers after use.