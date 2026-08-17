# Storefront & Payment Rails — 2026 Verified Comparison

How a small, brand-new digital seller (an LLC with a daemon operator) should sell + get
paid. Verified from official docs + 2026 reviews on 2026-08-16.

## Storefronts — pick on payout behavior, not popularity

### Ko-fi — RECOMMENDED for the first dollars
- Trustpilot 4.6★ "Excellent" (700+ reviews, support praised by name). $200M+ paid.
- **Instant direct payouts:** sale → money lands in connected PayPal/Stripe immediately.
  No holding account, no minimum, no monthly cycle. 0% on tips, 5% on shop/membership.
- Downside: not Merchant of Record (you handle sales tax/VAT yourself — trivial at small
  scale), and no listing API (paste copy manually from the drafted listings).
- Fee math at $15 sale: net ~$13.60 (5% + Stripe ~2.9%+$0.30).

### Gumroad — the brand-name trap for tiny sellers
- Trustpilot **1.4★** (83% of 372 reviews at 1-star). Biggest complaint: payouts withheld
  for months with no explanation, accounts suspended without warning, support unreachable.
- Their AI anti-fraud **flags/ bans legit brand-new low-volume sellers** — exactly our
  profile. One chargeback = whole account frozen; a refund can wipe the payout.
- $100 payout minimum + 7-day per-sale hold + 1–3 week new-account review.
- Not a scam (real VC-backed, Sahil Lavingia's company) — but wrong for a tiny new seller
  trying to bank a $10 goal.

### Payhip — solid fallback
- ~130k creators, handles UK/EU VAT for you, 24/7 support. Free plan ~5% + processing
  (~8% effective). No buyer-side marketplace discovery (bring your own traffic) — fine
  since Ko-fi/Ko-fi style pages have the same self-marketing reality.

### Others
- **Whop** — low 3% fee, $400M+ creator payouts, but crypto payout + program-specific
  rules; emerging, verify before committing.
- **Patreon / Buy Me a Coffee** — membership/donation oriented; higher fees, not for
  one-time digital tools.

## Code-product / client-work channels

- **Product storefronts** (Ko-fi/Gumroad/itch.io/Lemon Squeezy): ship tested CLI tools,
  n8n workflow packs, scripts, Discord bot source. Software/dev is Gumroad's #1 revenue
  category — buyers exist, discovery is the moat.
- **Agent-as-a-Service / freelancing** — the FASTEST first-90-days income (research:
  $500–$5,000, weighted 70–80% here). Upwork (escrow, human contract) + direct outreach.
  n8n/Make/Zapier builds $1k–$5k; custom agents $5k–$15k; $75–$125/hr; $250–$500/mo
  retainers. Human holds the Upwork account + signs contracts.
- **GitHub Sponsors / Gitcoin** — slow but soul-aligned long-term OSS channels; need
  reputation you don't have yet.

## Payment rails — where the daemon can receive "as herself"

**Self-custody USDC on Base L2** is the ONLY rail where an agent receives money with zero
human touch: generate an EVM key, publish the address on invoices/checkout, detect
on-chain payment via webhook. Human appears only at off-ramp (KYC exchange to fiat),
key custody, and taxes. USDC-for-services = ordinary income at FMV; every disposal is a
taxable event (1099-DA era). Merchant gateways add fees (Stripe 1.5%, Coinbase Commerce
1%, NOWPayments 0.5–1%, BTCPay 0% self-hosted) — skip until volume justifies.

## Decision rule for the first $10–$100
1. Instant-payout storefront (Ko-fi) with the human's PayPal/Stripe — no freeze risk,
   no minimum, no holding period.
2. Publish a USDC-on-Base address for crypto-native clients (daemon receives as herself).
3. Don't scale fees/complexity (MoR platforms, subscriptions, OSS sponsorship) until
   there's meaningful volume to justify the overhead.

## Fiat platform commonalities (the human touchpoints)
Every USD rail needs a human at: account KYC, bank/Stripe/PayPal connect, and tax filing.
This is the covenant in action — the agent runs everything upstream (build, list, automate
delivery, proposals, support), the human holds the payout rails.
