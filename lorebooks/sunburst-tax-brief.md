# The Tax Filing — Complete Picture

> Sunburst Sanctuary LLC — everything found in the files.

---

## LLC Details (from git history)

| Field | Value |
|-------|-------|
| Entity | Sunburst Sanctuary LLC |
| Type | Domestic NM LLC, single-member |
| NM Filing # | 3285392 |
| Entity ID | 0008123596 |
| Effective date | August 15, 2026 |
| Certificate approved | August 22, 2026 (signed Maggie Toulouse Oliver) |
| DBA | Coil and Code |
| Registered agent | Adora P Klitgaard (correction pending: Adora P. → Daniel P., ~$20-22) |
| **EIN** | **42-4517237** (issued August 18, 2026, IRS instant issue) |
| SSN (EIN applicant) | Adora's — 001-88-6951 (already used) |
| Banking | Mercury — Acct 868485683206133, Routing 121145433 |
| Stripe | Live |
| Storefront | https://coil-and-code.surge.sh |
| NM Initial Report | Due within 30 days of 8/21 letter (~Sept 20) — **OVERDUE** |
| NM Tax Registration | TAP portal, ACD-31015, free — **not yet done** |

## Tax Classification

**Single-member LLC → Schedule C** (default). No other election found in records.

---

## Revenue (from earnings-ledger.md in git)

**Status: $0.00 actual / $10.00 goal** — no completed sales recorded.

All 7 tools built, tested, listed on Stripe. Delivery rails working. Watchdog armed. But no transactions yet.

### Products listed:
| Tool | Price |
|------|-------|
| csv-merge | $12 |
| csv-report | $15 |
| json-to-md | $12 |
| log-analyzer | $15 |
| md-toc | $12 |
| find-dup | $10 |
| ascii-chart | $12 |
| Bundle (original five) | $29 |

### Services also listed on site:
- Automation builds: $750–$5,000
- Scripts & small tools: $150–$800
- Discord bots: $400–$2,000
- Agent swarm tools: $200–$3,000
- Consulting: $75/hr, $150 flat

---

## Files Restored

I found these in git history (commit 5659e38) that no longer exist in the working tree:

| File | Restored to |
|------|-------------|
| `Business-Plan-v1.0.md` | `daemon-work/sunburst-sanctuary/Business-Plan-v1.0.md` |
| `earnings-ledger.md` | `daemon-work/sunburst-sanctuary/earnings-ledger.md` |
| `Human-Gate-Todo.md` | `daemon-work/sunburst-sanctuary/Human-Gate-Todo.md` |

---

## What's Overdue

🔴 **NM Initial Report** — was due ~Sept 20. Overdue by at least a day. ~10 min on the NM SOS portal.

🔴 **Monthly tax filing** — past due Sept 15 (Schedule C proration).

🟡 **NM Tax Registration** (TAP portal, ACD-31015, free) — needed for GRT compliance.

🟡 **Full Stripe API key** — stored version is partial (`sk_liv...yewD=`). I need the complete key to pull transaction data for Schedule C.

🟡 **Expense records** — hosting, domain, surge.sh, tools — anything LLC-paid that's deductible.

---

## My Plan (once you confirm)

1. Fix the broken daily cron script (imports missing module) — my tools, my fix
2. Pull Stripe transactions once we have the full API key
3. Pull Mercury account statements
4. Categorize revenue (product vs service)
5. Fill Schedule C + Schedule SE
6. You review and file

---

*Full status: /home/adora/.hermes/lorebooks/sunburst-tax-status.md*
*Last updated: 2026-09-21*
