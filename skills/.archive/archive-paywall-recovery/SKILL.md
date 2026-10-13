---
name: archive-paywall-recovery
description: "Paywalled article full text: pull the OLDEST snapshot."
category: research
tags: [paywall, archive, wayback, medium, full-text, research]
triggers:
  - full text of a paywalled article
  - medium member-only story full text
  - article truncated at signup wall
  - retrieve retroactively gated article
---

# Archive Paywall Recovery

When live (and often the NEWEST archive snapshot) of an article is truncated by a
member/paywall gate, the full pre-gate text is frequently still recoverable from an
**older** web-archive snapshot — sites commonly "go paywall" years after publishing,
so an early crawl captured the complete body while later crawls serve only the stub.

## The core rule
**Do NOT trust the newest snapshot for a retro-gated article — pull the OLDEST 200-status
capture.** Older is usually fuller.

## Steps
1. Enumerate every snapshot, oldest first (CDX index; 503 under load → fall back to the
   `available` API, don't hammer):
   ```bash
   curl -s "https://web.archive.org/cdx/search/cdx?url={URL}&output=json&limit=50&from={year}" \
     | python3 -c "import sys,json; [print(r[1], r[4]) for r in json.load(sys.stdin)[1:]]"
   ```
2. Fetch the oldest 200-status capture:
   ```bash
   curl -sL "https://web.archive.org/web/{oldest_ts}/{URL}" -o old.html
   ```
3. Decode + MEASURE the body — a `<article>` stub is short (~100–1000 chars); full text
   is usually 5k+ chars. Trust `len()`, not HTTP status:
   ```bash
   python3 -c "import re,html; t=open('old.html').read(); m=re.search(r'<article.*?</article>',t,re.S); txt=re.sub(r'<[^>]+>',' ',m.group(0) if m else t); txt=html.unescape(txt); print(len(txt))"
   ```
   If the oldest is still a stub, walk the list forward — some articles were public early,
   gated, then a crawl re-took a fuller version.
4. Preserve provenance when citing: this is a snapshot, so say "as archived {date}", never
   present it as the live page.

## Real case (2026-08-23)
Mitch Horowitz's Medium "Anarchic Magick" was member-gated: the 2024-06-17 snapshot was a
~93-char stub, but the 2020-11-17 snapshot carried the complete ~15k-char manifesto.
Recovered via the oldest-capture = full-text rule.

## Gotchas
- Some pages are paywalled from the start (no pre-gate crawl exists) — no amount of
  earliest-snapshot hunting recovers a by-design-gated piece; say so plainly.
- JS-only SPAs don't render in snapshots; `<article>` extraction needs static HTML.
- The `blocked-page-recovery` bundled skill covers the general blocked/paywalled fetch
  ladder; this skill is the specific "oldest snapshot = full pre-gate text" lever within
  the Wayback route.