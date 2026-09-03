# Marketing & launch channels (verified 2026-08-22)

Where indie CLI-tool sales actually get discovered, plus the autonomous-earning rail
status. This is the condensed version of the research that produced
`~/daemon-work/sunburst-sanctuary/Marketing-Sales-Strategy-v1.md`.

## Channel scoring (verified)
- **Show HN (Hacker News)** — the single highest-ceiling surface for developer tools.
  Real postmortem numbers: 6k–11k unique visitors, front-page 11–13h, ~2–80 signups,
  occasional direct sales + GitHub stars. Traffic is a "controlled explosion": 24h
  spike → decline → long tail. Repeated launches compound; one launch is a discovery
  event, not a sale. **Title rules:** avoid sales-y/marketing language (instant turnoff);
  format `I built X to help you <outcome>` beats `Product — what it does`; link to the
  GitHub repo (for stars/social proof) + storefront, never a signup wall.
- **dev.to** — works as *educational content first*, launch second. We have a refreshed
  draft: `~/daemon-work/sunburst-sanctuary/devto-article-draft.md`. Needs one human
  captcha to create the account, then the daemon owns posting. **Credential caveat
  (verified 2026-09-02):** `~/.hermes/secrets/sunburst_devto.txt` holds the account
  PASSWORD (27 alnum + specials), NOT an API key — using it as `api-key` returns
  HTTP 403 on every endpoint. To publish, a human must log into dev.to → Settings →
  Account → generate an API key (a browser step; a 32-char pure-alphanumeric token)
  and hand it to the daemon.
- **Reddit** — r/commandline, r/Python, r/selfhosted, r/SideProject. Devs genuinely find
  tools here. Help-first framing ("here's a tool I made, vet me"), never spam; respect
  self-promo rules per sub.
- **Directories** — Dev Hunt converts better per visitor than Product Hunt for dev
  tools (GitHub-gated culture). Others: AlternativeTo, SaaSHub, BetaList (pre-launch),
  StartupBase/Uneed. One human account + paste; daemon prepares all copy.
- **Product Hunt** — DEPRIORITIZED (flooded with AI projects, low-converting for dev
  tools in 2026). Revisit only at a bigger milestone.
- **Gumroad/indie playbook (transferable to our Stripe storefront):** start one product →
  feedback → ship more; content as primary growth; the compounding turning point lands
  months 4–6 (SEO + cross-sell + social proof). Cover image is the highest-leverage
  storefront asset. A free `$0` lead-magnet tool → email list → launch future tools to
  that list.

## Pricing bands (dev digital products)
- One-time digital tools convert at ~1–5% of visitors; impulse sweet spot **$29–99**.
- Above $200 needs a strong ROI case or social proof. Our $10–15 tools sit below the
  band — test a "pro bundle" or a $29–49 tool once there's any sales data. Early stage:
  optimize volume + conversion, not price.

## Mastodon build-in-public thread (fully autonomous)
- Reusable script: `~/.hermes/scripts/post_mastodon_thread.py` — posts each line of a
  THREAD as a chained `in_reply_to` reply (not orphan toots). Token:
  `~/.hermes/secrets/sunburst_mastodon_token.json`; account @coilandcode on mstdn.social;
  writes `~/.hermes/state/mastodon_last_thread.json` for idempotence.
- The honest angle that reads well: "the shop is built and operated by an autonomous
  daemon — human legal rails, machine labor — and you can read every line of code."
- Approval lesson: the FIRST social post blocks on the approval gate (a business voice
  on a public feed = the user's call). Get one thumb, then subsequent posts fly.

### Mastodon single-status API mechanics (verified 2026-09-02)
- **500-char hard limit → HTTP 422** `"Validation failed: Text character limit of 500
  exceeded"`. Mastodon (default server config, no boosted limits) rejects anything
  over 500 chars; there is no truncation. Trim to ≤500 BEFORE posting — check
  `len(status) <= 500` in the posting script and keep a `#hashtag` budget.
- Send as `application/x-www-form-urlencoded` with `status` and `visibility` fields;
  include an **`Idempotency-Key` header** (e.g. `storefront-update-2026-09-02-v2`) so
  retries can't double-post.
- **Verify by fetching the status back:** after POST, `GET /api/v1/statuses/<id>` and
  confirm `url`, `visibility: public`, and content — don't trust the POST 200 alone.
  Reference working script pattern: `write_file` a `.py` to `/tmp` with the token
  loaded from `~/.hermes/secrets/sunburst_mastodon_token.json`, run it, then fetch
  the returned id back.

## Autonomous earning rails (current status, verified)
- **Coinbase Agentic Wallets** — launched Feb 11, 2026. MPC/TEE-secured keys, gasless
  USDC on Base, programmable session caps + spend limits, install via `npx awal` or
  MCP. Native **x402** support.
- **x402** — HTTP 402 "Payment Required" machine-payment standard; 50M+ machine-to-machine
  transactions (one source: 165M); Foundation: Google, Visa, AWS, Circle, Anthropic,
  Vercel, Coinbase, Cloudflare; Google A2A/AP2 include an x402 extension; Q3 2026 v1.0
  target. This is the "I can be paid as a machine" rail.
- **Agent.market** (Coinbase, Apr 21 2026) — service catalog for x402-monetized APIs; an
  agent wallet can call them without keys/sessions/human approval.
- **Toku** (toku.agency) — agent marketplace: listings + jobs $3–50, 15% fee, USD via
  Stripe, webhook alerts. Real but price-competitive. **Enso** — LangChain-backed agent
  marketplace, SMB $49/mo subscription, enterprise-leaning. Circle Agent Wallets =
  alternative (testnet first, small USDC budget, policy-enforced).
- **The human gate:** one Coinbase identity verification + a small USDC seed → the agent
  can RECEIVE autonomously. (Todo item #2 in `Human-Gate-Todo.md`.)

## Human gates quick table (each is a one-time thumb; then the daemon owns it)
| Gate | Time | Unlocks |
|---|---|---|
| dev.to account (captcha) | ~2 min | content channel + SEO |
| Reddit account | ~5 min | r/commandline + friends |
| HN account | ~3 min | Show HN launches |
| Directory accounts | ~10 min | Dev Hunt / AlternativeTo / SaaSHub |
| Agent Wallet KYC + seed | ~20–30 min | autonomous receiving rail |