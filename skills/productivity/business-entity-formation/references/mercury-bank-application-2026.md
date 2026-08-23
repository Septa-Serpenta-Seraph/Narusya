# Mercury business bank application — step-by-step (August 2026, verified)

The final legal unlock for a solo NM single-member LLC. Mercury is a fintech backed by
Choice Financial Group and Column N.A. (both FDIC members, $250k pass-through).
It beat the alternatives for this profile: local credit unions lack the API-friendly
business feel; Relay is fine but Mercury's compliance flow matched the entity's docs.

## Which document actually PASSED the EIN upload step

- NOT the post-filing CP-575 / 147C letter — Mercury *did accept* the **IRS EIN assignment
  confirmation page printed to PDF from the online apply flow** ("Congratulations! Your EIN has been
  successfully assigned" — the same page the IRS tells you to save/print for permanent records).
- This is the natural by-product of applying for an EIN online under ~10 min; no wait for a mailed letter.
- So the file name says "Request" but the content IS the confirmation. If the portal is picky
  about filenames, repo.name it `EIN_Confirmation_<EIN>.pdf` — content is what matters.
- Order of preference if you have them: **CP-575 > 147C > stamped SS-4 > this assignment PDF > IRS screenshot**.
  This assignment PDF is the best available doc for the Mercury flow without waiting for mails.

## Application answers (compliance page)

| Field | What to enter | Why |
|---|---|---|
| Legal entity / formation doc | State-filed Certificate of Organization (NM SOS) | required proof of formation |
| Type | LLC (minus one-member pass-through) | matches NM filing |
| Industry | Software / Developer Tools | matches the storefront's actual offering |
| Description | "Developer tools and automation software" | boring, true, no AI-publisher framing |
| Social presence | Mastodon + storefront URL only | the owner declined to give GitHub — respect that; a personal GH is not business identity |
| Expected activity | Self (personal funds to start), then revenue; `$0–10k` monthly balances, `0–$500` tx volume, US-only, US send/recv | unvarnished baby-storefront numbers; don't inflate |

## "Expected activity" form — honest low-band answers

This screen asks for the compliance #s and anything inflated = red flag:
- First deposit source: **Self** (self-funding; not investors, not yet revenue)
- Intended use: **Operating expenses + Receiving revenue**
- Expected monthly balance: the LOWEST tier (**$0–10k**)
- Expected monthly tx volume: the LOWEST tier ($0–$25k or whatever min is offered)
- Operating/countries: United States only
- Countries sending/receiving: United States only
(If you later grow, they can raise limits in-app.)

## What happens after approval

- Dashboard shows the exact business checking + savings at $0 — you can then link
  Stripe payouts to this account, or ACH-seed once rested ($50–100 optional, not required
  to keep the account).
- The owner's ID.me video call (the IRS login) is separate from the Mercury call and not
  needed again for Mercury; it was the gate to get the EIN doc.

## Pitfalls
- Don't hand over GitHub to Mercury (privacy) — Mastodon + storefront is enough.
- The bank portal is human-flow; the agent arm has **read/reconcile autonomous** but **never
  outbound transfer without a human confirm** (Agreed autonomy split).
- If the portal asks "Designated Official" (DO) role for a solo LLC: the IRS menu has no
  single-member-LLC option (C/S/foreign-exempt only) — skip DO setup, it needs a PIN letter by
  mail (44-day) and isn't needed to pass Mercury.
- IRS "Get Transcript" for a new LLC shows only personal transcripts, NOT an EIN letter —
  don't send her down the 147C rabbit hole there; the assignment PDF is the right doc.