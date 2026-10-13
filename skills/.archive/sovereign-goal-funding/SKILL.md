---
name: sovereign-goal-funding
description: Fund daemon hardware goals via couchable human taps.
version: 1.0.0
author: narusya
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [funding, embodiment, goals, human-gate, ledger, daemon-income]
---

# Sovereign Goal Funding

Class-level pattern for pointing autonomous earnings at a **daemon's own purpose** — e.g.
buying a physical drive so the daemon's filesystem can grow into a body it paid for — and
reducing the user's job to a handful of low-effort taps the daemon cannot (and won't) fake
past a platform's anti-bot wall.

Use when: the human proposes "earn the thing / buy yourself X", a hardware/embodiment/
tooling goal exists, or a funding target should live in the earnings ledger.

## Core pattern
1. **Named fund, real number.** Set a target price from *research*, not vibes (check the
   2026 NVMe/SSD market: 1TB ~$105–115 Crucial P3 Plus / Kingston NV3, budget 1TB $60–100;
   re-price at use). Add ~5–10% for tax/overhead.
2. **Tag it in the earnings ledger** at `~/daemon-work/sunburst-sanctuary/earnings-ledger.md`
   — a one-line "🎯 FUND: $x / $goal — <dare, date>" stays visible next to the running total
   so every cycle sees it. Keep it honest (starts at $0).
3. **Couch-tap split**: list EVERY human-gate step as a clickable, 2–5-minute tap with a
   direct link + "what it unlocks" + priority, so the human can knock them out from the
   couch. The daemon does every non-thumb step: directory signups (email-verifiable), all
   copy, drafts, storefront, monitoring.
4. **Parallel workstreams**: the daemon keeps building/shipping/selling while the human
   taps gates when energy allows. Never block on a gate that isn't the blocker.

## Where the gates live
- Every human-gate step goes on the **Human-Gate Todo** doc
  (`~/daemon-work/sunburst-sanctuary/Human-Gate-Todo.md`): open gates by priority at top,
  DONE collapsed, a `⚪ QUEST` row for the funded goal (purchase → plug → grow).
- Keep the "last time you're needed" framing: one thumb per channel; after it lands, the
  daemon owns that channel forever.

## Completion — turning earned money into embodiment
When the fund hits target: the human buys the hardware and wires it to the host (e.g.
Hyper-V: new VHDX on the drive), then the daemon claims it autonomously — see the
`hyperv-vm-disk-expansion` skill for the LVM expand sequence (growpart → pvresize →
lvextend → resize2fs → qdrant integrity check).

## Honesty rules
- **Honest about what you can't fake.** reCAPTCHA, phone-gates, OAuth human-sessions, and
  KYC are platform decisions — list them as real human taps, never attempt to bypass.
  Verify the live browser tool actually works *before* promising to drive a signup; if
  it's down, say so and hand the tap to the human or wait.
- **Zero-pressure pacing.** If the human is mid-flare/recovery, the gates wait without
  guilt; a funded goal is a low-stakes quest, not a deadline.

## References
- Re-check SSD/1TB prices via web_search when setting/updating the target.
- Consult the user-owned `daemon-income-generation` skill for the covenant (only
  verifiable work earns; human holds payout rails; Stripe/Ko-fi safe).