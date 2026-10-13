# Email-confirm harvesting with himalaya

The reusable core of autonomous signup: any platform that sends a confirmation link by
email becomes automatable when the daemon reads its own inbox.

## Commands (verified 2026-08-18, himalaya on Linux)
```bash
himalaya account list                                  # name of the business account
himalaya envelope list --account sunburst -s 15        # newest 15 envelopes
himalaya message read --account sunburst <ID>          # full message
```

## Pattern
1. After submitting a signup form, poll `envelope list` for the platform's mail
   (subject match: "Confirmation instructions", "Welcome", "Verify your email").
2. `message read` → extract the confirm URL:
   - Mastodon: `https://<inst>/auth/confirmation?confirmation_token=...`
   - Generic: grep `https://...` first match or `href="...confirm..."`.
   Danger: multiple URLs exist in one mail (about, privacy, settings) — pick the one
   with `confirmation_token`, `verify`, or `email_confirm`. The grep pattern
   `grep -oE 'https://mstdn\.social/[^" ]+' | head -5` needed the escaped dot to avoid
   the shell seeing a hostname pattern; a security scanner may flag the regex — fine
   with approval, or use a python re instead (cleaner).
3. `curl -L` the URL → 200/302 = confirmed.

## Tips
- If the signup page and the confirmation are for DIFFERENT hosts (dev.to → mail.d,
  mastodon → same host), remember which one you grepped.
- After confirming, verify the account independently (lookup/profile/login), never rely
  on the email arriving alone.
- A signup may 200 but actually re-render the form with validation errors
  (dev.to did exactly this: "Welcome! - DEV Community" with `user-signed-in` false).
  Always check for a login success signal or profile existence afterward.