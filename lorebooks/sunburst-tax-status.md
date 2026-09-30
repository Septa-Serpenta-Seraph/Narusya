# Sunburst Sanctuary LLC — Tax Filing (Complete Picture)

> Reconstructed from git history, secrets, site files, and PLAN.md. Filed 2026-09-21.

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
| Registered agent | Adora P Klitgaard (legal-name correction pending: Adora P. → Daniel P., ~$20-22) |
| EIN | **42-4517237** (issued August 18, 2026, IRS instant issue) |
| SSN (EIN applicant) | Adora's — 001-88-6951 (already used, don't share) |
| Banking | Mercury — Acct 868485683206133, Routing 121145433 |
| Stripe | Live (key partial in secrets) |
| Storefront | https://coil-and-code.surge.sh |
| NM Initial Report | Due within 30 days of 8/21 letter — approximately **September 20, 2026** — **OVERDUE** |
| NM Tax Registration | TAP portal, form ACD-31015, free — not yet done |

---

## Tax Classification

Single-member LLC → defaults to **Schedule C** (sole proprietor) for federal. No election filed.

**What this means for filing:**
- All revenue and expenses on Schedule C
- Self-employment tax on net profit (Schedule SE) if net > $400
- NM has a Gross Receipts Tax (GRT) — the LLC may need to register and remit on NM-sourced software sales

---

## Revenue (from earnings-ledger.md in git history)

**Status: $0.00 / $10.00 goal** — no sales recorded yet. All tools built, tested, and listed on Stripe but no completed transactions in the ledger.

### Products listed (from site + ledger):
| Tool | Price |
|------|-------|
| csv-merge | $12 |
| csv-report | $15 |
| json-to-md | $12 |
| log-analyzer | $15 |
| md-toc | $12 |
| find-dup | $10 |
| ascii-chart | $12 |
| **Bundle** (original five) | $29 |

### Professional services listed on site:
- Automation builds (n8n/Make/Zapier): $750–$5,000
- Scripts & small tools: $150–$800
- Discord bots: $400–$2,000
- Agent swarm tools & consultation: $200–$3,000
- Consulting & debugging: $75/hour, $150 flat audits

### Other revenue:
- BountyBook: $3.50 submitted, 0 payouts (claims flaky)

---

## Files from Git History (no longer in working tree)

These files existed in commit `5659e38` but are not in the current HEAD:

| File | Contents | Status |
|------|----------|--------|
| `Human-Gate-Todo.md` | Tasks only Adora can do — EIN ✅, NM tax registration 🟡, bank account 🟡, SSI consult 🟢, NM initial report 🟢 | **In git history only** |
| `earnings-ledger.md` | Full transaction log, running total, product inventory | **In git history only** |
| `records/Certificate_of_Organization_2026-08-15.pdf` | Official NM Certificate | **In git history only** |
| `records/Notice_of_Approval_2026-08-21.pdf` | NM SOS notice of filing approval | **In git history only** |
| `records/Sunburst_Sanctuary_LLC_EIN_Request.pdf` | IRS EIN request documentation | **In git history only** |

**These need to be recovered from git or restored to the working tree.**

---

## What Needs Doing

### 🔴 URGENT (past due now):
1. **NM Initial Report** — was due ~Sept 20. Overdue. ~10 min on the NM SOS portal.
2. **Monthly tax filing** — past due (Sept 15). Schedule C proration for the period.

### 🟡 NEEDED SOON:
3. **NM Tax Registration** — TAP portal, ACD-31015, free. Required for NM GRT compliance.
4. **Recover records from git** — certificates, EIN docs, ledger, human-gate todo
5. **Stripe transaction data** — pull actual revenue figures for Schedule C
6. **Full Stripe API key** — stored version is partial (sk_liv...yewD=)

### 🟢 GOOD TO HAVE:
7. Registered agent name correction (Adora P. → Daniel P.)
8. Operating agreement attorney review
9. Fix broken daily cron script (imports missing module)
10. Restore business plan documentation

---

## What I Need From You, Adora

To start the actual filing, I need:

1. **Confirmation of Schedule C** (or if you elected otherwise)
2. **Full Stripe API key** — I can then pull transactions and calculate actual revenue
3. **Any expenses the LLC paid** (hosting, domain, surge.sh, etc.)
4. **Whether to do NM GRT registration** (tax registration + monthly/quarterly remittance)
5. **Your go-ahead on NM Initial Report** — I can file this myself, it's ~10 min on the portal
6. **Your preference: do this yourself or let me handle it?** I can pull data, fill forms, and you review/sign

---

*Reconstructed from: git commit 5659e38, PLAN.md, secrets/, site/, daemon-work/PLAN.md*
*Last updated: 2026-09-21*
