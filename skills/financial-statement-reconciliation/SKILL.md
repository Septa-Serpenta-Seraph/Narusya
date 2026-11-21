---
name: financial-statement-reconciliation
description: "Use when reconciling bank charges against bills in disputes."
version: 1.0.0
author: Narusya
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [finance, reconciliation, bank-statements, bills, pdf, csv, disputes]
---

# Financial Statement Reconciliation

Use when asked to find a payee's charges across bank statements and compare them to bills — overbilling disputes, phantom subscriptions, "they keep charging me" cases. The deliverable is a charge-by-charge reconciliation that separates what the bills explain from what they do not.

## When to Use

- A bill/dispute needs charges located across multiple statements or exports
- Comparing billed amounts against what actually left an account
- Suspected duplicate or parallel payment streams to the same payee
- Building an evidence packet (report + machine-readable charge list) for the user to act on
- The user asks what to do about the charges, is on the phone with the bank/company, or a deadline/escalation decision is pending

## Standing dispute rules

- **Stopping a payment is not cancelling the debt.** State the two jobs separately in the first reply: stop the money (client + bank control it) and resolve the obligation (a dispute with the payee). A stop-payment or closed card does not stop late fees or credit reporting.
- **Never recommend closing the bank account as the first move.** It is a last resort: it does not erase the claim, disrupts other bills, and invites late fees. Treat the client's reluctance to close it as a constraint.
- **Repeated failed calls usually mean an authority problem, not politeness.** Check whose name the account is in before advising another call. A deceased account holder routes to the bereavement/estate path, not the front line.
- **The client's own records are authoritative.** When they report charges visible in their statements but absent from the files you were given, ask for dates and amounts and work from theirs. Their bank may hold a channel the export does not contain. Never explain your file back to them as if that settles it.
- **Name every payment instrument by bank AND last four**, never last four alone. Clients identify accounts by institution; a digits-only label makes you talk past each other for turns.
- Depth for the whole action phase (payment setups, authority, record-making, corroboration, escalation): `references/dispute-action-playbook.md`.

## Governing rule

Report what the documents show and flag what they do not. Characterizing charges as fraud, unlawful, or a legal violation is not the assistant's call. Use "unexplained", "not covered by the supplied bills", "worth confirming" — never declare a crime or give legal advice.

## Procedure

1. **Inventory every source before reading any of it.** List archive contents, then note each source's date range, account holder name, and account-number suffix. Establish which account each source represents: a credit-card statement and a checking export are different accounts even under the same person's name. Bills may be addressed to a different person than the account paying them.
2. **Extract PDF statements to text.** Probe available interpreters for a PDF library rather than assuming a CLI extractor exists; `pypdf` in the system Python is enough (`PdfReader(f)`, join `page.extract_text()` per page, write one `.txt` per PDF). Skip `__MACOSX/` `._` sidecar files. PDF statement text often arrives as one concatenated line: split on a transaction-start regex (e.g. a lookahead on `\d{2}/\d{2}\s+\d{2}/\d{2}\s+`) before matching individual transactions, or matches come back as fragments.
3. **Parse transaction CSVs with `csv.DictReader`.** Parse dates with `datetime.strptime` before sorting or taking min/max — lexical order on `M/D/YYYY` is wrong. Prefer the `Extended Description` / full memo field: the short `Description` collapses distinct payment types into one label.
4. **Categorize every candidate charge by its extended descriptor, not the payee name alone.** Typical splits: `ACH Withdrawal COMPANY: ...` (direct debit, often with an account suffix and the account holder's name), `Bill payment Withdrawal ...` (bank bill-pay to a payee), `Debit Card purchase ...`. Keep the whole descriptor in the output — company, entry, phone, and account suffix are the evidence that distinguishes one service/account from another.
5. **Build the bill-versus-charge table.** For each bill: billing date, period, new charges / amount due, and the matching statement charge with its posting date. Mark exact matches explicitly. Sum both columns and show they agree (or not).
6. **Look for parallel payment streams.** An exact bill↔card match does NOT clear the account. Search every other source for the same payee in the same months — card autopay plus a checking bill-pay to the same payee is the classic double-pay pattern. Also look for related services under a different account suffix or a different person's name (e.g. mobile vs cable/internet) that the supplied bills do not cover.
7. **Total in three layers:** (a) the subset explained by the bills, (b) each unexplained stream by category, (c) the grand total across all sources and the full date window. Show a month-by-month table so spikes are visible.
8. **Deliver as attachments, not a wall of chat.** Write a `.md` report to `~/.hermes/notes/` and a machine-readable CSV of every charge found. Post both as Discord attachments and keep the chat message short: headline finding, the two or three numbers that matter, and a pointer to the files. Use `discord_send.py post <channel> "<summary>" --file <report.md> --file <charges.csv>`.

## Report shape

- Bottom line up front: what the bills explain, and where the unexplained money is.
- The bill table (billing date, period, billed, charged, exact-match column).
- One section per payment stream, each with a dated charge table and a subtotal.
- Month-by-month total table across the whole window.
- "What this means" — descriptive only: which charges are accounted for, which are not, name/suffix mismatches, line items shown at zero while costs sit at account level.
- Suggested next steps framed as options, not instructions: stop a recurring payment if unintended, request a full account list by name and suffix, obtain written cancellation confirmation with an effective date, gather ticket/call logs, then dispute or escalate with the relevant regulator if it continues.
- Caveats: state the date windows, which bill months were not supplied, and that unmatched older charges are flagged rather than judged.

## Pitfalls

- **A perfect bill match is not exoneration.** Stopping at "the six bills match six card charges" misses a second payment channel to the same payee — check every account before concluding anything is reconciled.
- **The short description column hides account identity.** Reconcile on the extended descriptor; the abbreviated field merges ACH, bill-pay, and card purchases under one payee label and destroys the account suffix that proves they are different streams.
- **Lexical date sorting corrupts a transaction history.** Parse `M/D/YYYY` to a date object first; otherwise the reported range and "newest row" are wrong.
- **Concatenated PDF text yields fragment matches.** Insert transaction boundaries before regex matching, or a charge row reads as the tail of the previous row.
- **A phone number in a descriptor is not an account suffix.** `800-266-2278` is 1-800-COMCAST (266-2278 spells COMCAST); the masked `***-***-2278` is the same number. Do not report it as "account ending 2278". Likewise, a name after the descriptor (`KAREN *KLITGAARD`) identifies the **bank account debited**, not the service subscriber. Generic labels like `CABLE SVCS` do not distinguish TV from internet — leave service owner and type as unknown unless a bill names them.
- **Do not bulk-delete or bulk-flag from a broad pattern.** Narrow by account and date window, then verify each charge individually.
- **No legal characterizations.** Describe amounts, dates, and mismatches; leave "fraud", "illegal", and "you should sue" out of the report.
- **Correct a wrong claim in place and re-issue the artifacts.** When a descriptor interpretation turns out wrong, edit the sentence in the report and the category label in the CSV, then re-attach both. Do not leave a stale file in the client's hands that they might act on.
- **A scope correction must reach every artifact and every number already quoted.** When the client identifies a stream as legitimate, put an explicit scope note at the top of the report and action sheet, recompute the disputed subtotal, and withdraw the superseded grand total in chat. A stale total in their hands gets quoted to a bank.
- **Client-reported charges you cannot see are data, not confusion.** If they say their own record shows the payee at a third institution, add the stream as client-reported and unverified and request the dates and amounts. Do not conclude it must be the channel you already found.
