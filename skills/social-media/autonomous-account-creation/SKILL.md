---
name: autonomous-account-creation
description: "Create web accounts autonomously from an email seed."
version: 1.0.0
author: narusya
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [accounts, signup, email-confirmation, mastodon, oauth, autonomous]
---

# Autonomous Account Creation

Create real accounts on web platforms with **zero human hands** — using a business email
the daemon can read (himalaya) as the identity seed. Built from the Coil and Code outreach
build (2026-08-18): produced a live GitHub repo, a live Mastodon account (staff-pending),
and mapped the platform gate walls.

## When to use
- Creating a daemon/business presence on a new platform ("wanna make your own accounts?")
- Any signup that only needs email + password (no phone/captcha)
- Standing up a watchdog that completes a flow the moment a platform human approves

## Core truth
**The readable inbox is the unlock.** Every email-verifiable platform becomes automatable
when you can harvest the confirmation link yourself: `himalaya envelope list --account NAME`,
`himalaya message read --account NAME ID`, grep the URL, curl it. No human click needed.

## Platform gate map (verified 2026-08-18 — RECHECK before trusting)
| Platform | Gate | Autonomous? |
|---|---|---|
| GitHub | OAuth token in `~/.config/gh/hosts.yml` | ✅ fully |
| Mastodon (mstdn.social) | email + OAuth app; staff approval on some instances | ✅ up to approval |
| dev.to | reCAPTCHA on signup | ❌ human/browser only |
| Bluesky | phone verification now mandatory | ❌ no phone |
| X / Twitter | xurl OAuth needs human browser | ❌ needs human once |
| Reddit | new-account link posting shadowban-prone | ⚠️ strategy needed |

## Mastodon worked flow (full detail in references/mastodon-oauth-flow.md)
1. `POST /api/v1/apps` → client_id/secret; store 0600.
2. `POST /oauth/token` grant_type=client_credentials → app token (needed for /accounts).
3. `POST /api/v1/accounts` with username/email/password/agreement + required fields
   (mstdn.social demands `date_of_birth`; some instances want a `reason`).
4. Read inbox → click confirmation URL → account exists (`/api/v1/accounts/lookup` 200).
5. **password grant is dead** — mstdn.social rejects it. Drive the web OAuth flow with
   cookies (csrf → login → authorize → code), then `POST /oauth/token`
   grant_type=authorization_code → user token (scopes read write).
6. Post: `POST /api/v1/statuses` with `Idempotency-Key` to avoid dup launch posts.

## Staff-approval watchdog (the elegant part)
Instances like mstdn.social gate new accounts behind human review. Don't poll the API —
cron a **silent watcher script** (no_agent cron, in `~/.hermes/scripts/`):
- reads inbox for the approval/welcome email (non-confirmation mail from the instance)
- if found AND no token file yet → run the OAuth flow, post the intro, print status
- else exit silently (no delivery) — done the moment a human nods, no hammering.
Verified as a no_agent cron: `mastodon-approval-watch.py`, every 60m, deliver origin.

## Hard rules
- **Secrets:** generate passwords in-script, write 0600, NEVER echo/print tokens.
  App creds and tokens go to `~/.hermes/secrets/<platform>_*` files. Wipe /tmp scripts
  after (approval-gated — if the wipe blocks, leave them; they hold no plaintext).
- **No captcha-solving, no fake phones.** A reCAPTCHA/phone gate is a platform decision,
  not a bug. Say so plainly; move to the next reachable platform.
- **Clean identity posture:** "never lie about being human, but no need to announce AI
  unprompted" (covenant). The daemon line on branding is the user's call each time.
- **Verify ground truth:** 404/200 on the profile, `/api/v1/accounts/lookup`, or a real
  sign-in — never trust "Welcome!" re-render pages that silently failed.

## Pitfalls
- Surge `*.surge.sh` hosts **fixed** `Disallow: /` robots.txt that cannot be overridden →
  no crawl SEO. Use OG/meta cards (render on share) + GitHub repo + dev.to for
  discoverability instead of chasing SEO on the subdomain.
- `gh auth` may default to a dead token while a live one sits in hosts.yml — run
  `gh auth switch --user <live-account>` before repo creation (401 Bad credentials fix).
- "Welcome!" HTTP 200 after a form is often a validation re-render, not success; confirm
  via login or profile lookup.

## References
- `references/mastodon-oauth-flow.md` — the full working Mastodon state machine
- `references/email-confirm-pattern.md` — himalaya confirmation harvesting