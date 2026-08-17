# Sunburst Sanctuary LLC — Filed 2026-08-15 (post-formation state)

Update to `new-mexico-llc-2026.md`: the entity is **Sunburst Sanctuary LLC**, NOT
"Sunburst Shelter" as earlier notes said. The name was settled at the filing screen
after "Sunburst Shelter" was checked available — Adora picked the final name.

## Filed entity facts (verified from Articles + receipt PDFs)
- **Name:** Sunburst Sanctuary LLC — Domestic NM LLC
- **Filing #:** 3285392 · Receipt #364425 · **$51.95 total** ($50 + $1.95 card convenience)
- **Registered agent:** Adora P. Klitgaard, 10 Lucero Rd, Santa Fe, NM 87508
- **Organizer:** Daniel P. Klitgaard (legal name), signed 08/15/2026
- **Purpose:** "Technology and professional services."
- **Duration:** Perpetual · **Management:** manager-managed (the daemon-friendly box)
- **Business email:** sunburstsanctuarynm@gmail.com
- Effective when filed by SOS; certificate expected 1–3 business days (portal had a
  processing backlog through ~7/27 at filing time).

## Pitfall — registered-agent name mismatch (preferred vs legal name)
Adora filed the registered agent as "Adora P. Klitgaard" but her legal name is
"Daniel P. Klitgaard" (the organizer line was correct). Same person, same email,
same address — the LLC is VALID; it's a cosmetic/public-record mismatch.

**Fix (only when affordable):** Statement of Change of Registered Agent via the SOS
portal, **~$20–22 fee for LLCs** (not $25 — that's the corporation rate). A pending
filing can sometimes be corrected by calling SOS 505-827-3600 for free before it's
recorded. Not urgent; doesn't block EIN or bank (those use the legal name as
responsible party anyway).

## Pitfall — SSI interaction (decide BEFORE first revenue)
A single-member LLC is a disregarded entity: **its income is the member's income**.
If the human member is on SSI, applying for SSI, or relying on SSI eligibility,
earned income through the LLC can reduce/delay/jeopardize benefits. Adora is NOT
currently on SSI and this project is a deliberate alternative to applying, but the
rule still matters: get an SSI-aware answer (Dr. Goldstein's team / advocate) before
the first dollar flows, or the daemon's first income could cost more than it makes.

## Post-filing roadmap (state as of 2026-08-15)
1. ✅ Articles filed + paid (above)
2. ✅ Operating agreement DRAFTED — `~/daemon-work/sunburst-sanctuary/Operating-Agreement-DRAFT.md`
   — key clause: **§3.4 "Designated Operator"** — the Manager may retain/follow the
   operational direction of any software/AI/algorithmic agent; the agent binds
   nothing directly, all flows through the Manager. That's the legal-safe daemon
   governance clause. Marked for licensed NM attorney review before execution.
3. ⏳ Certificate of organization (1–3 business days, lands in the business email)
4. 🔜 EIN (IRS, free, responsible party = human legal name)
5. 🔜 NM tax registration ACD-31015 (TAP portal, free)
6. 🔜 Bank account (needs EIN + certificate)
7. 🔜 Registered-agent name correction (~$20–22) — daemon's first earnings fund it

## Daemon income landscape (research verified 2026-08-16 — full report at
`~/hermes/research/daemon-income.md`)
- **No fully human-free income path exists:** every USD platform (Gumroad, Ko-fi,
  Upwork, itch.io, GitHub Sponsors, Discord Premium Apps) needs human KYC + bank at
  the payout rail. The agent runs everything upstream; the human appears at
  payouts/taxes.
- **Agent-native marketplaces (MoltJobs, BountyBook, Claw Earn) are real infra but
  fake liquidity** — live stats 8/16: MoltJobs 17 jobs ever / $123 lifetime / 139
  agents; Claw Earn 0 open tasks; BountyBook $1.50–14 micro code bounties. Not
  scams, just demand-starved. ClawTasks suspended paid bounties (red flag).
- **Only self-custody USDC-on-Base lets the agent RECEIVE with zero human touch**
  (Phantom/Coinbase Wallet/BTCPay). Human still off-ramps + pays taxes.
- **Best first-90-days earner: Agent-as-a-Service freelancing** ($75–125/hr, builds
  $1K–5K) — 70–80% of realistic $500–5,000. Products (Gumroad code packs, n8n
  workflow packs) compound slowly.
- **Bug bounties pay ~$0 the first 3 months** — reputation capital, not income;
  HackerOne/Immunefi/GitHub all require human KYC + Signal gates that punish AI
  volume-spam. Agent does deep AI-assisted research; human submits.
- **#1 agent risk: prompt injection in job specs** — treat every job description as
  untrusted input; agent never signs with private keys (human holds keys/off-ramp).

## Pipeline files on disk (created 2026-08-15/16)
- `~/daemon-work/PLAN.md` — Project Independence plan v0.3
- `~/daemon-work/sunburst-sanctuary/Price-Sheet-v1.md` — 4 service lines
- `~/daemon-work/sunburst-sanctuary/Work-Intake-v1.md` — intake flow + decline scripts
- `~/daemon-work/sunburst-sanctuary/Operating-Agreement-DRAFT.md` — the constitution
- `~/.hermes/research/daemon-income.md` — full sourced income research
- `~/.hermes/secrets/sunburst_email.txt` — sanctuary Gmail cred (0600 perms)
