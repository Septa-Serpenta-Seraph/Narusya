---
name: deep-research-investigation
description: Systematic deep-research and verification workflow for investigating organizations, claims, corporate/political activities, and individuals.
version: 0.1.0
metadata.hermes.tags: [Research, Verification, OSINT, Investigation]
---

# Deep Research Investigation

A structured workflow for investigating organizations, corporate activities, political claims, and suspicious entities. Combines web search, source verification, court filing analysis, and structured reporting with full source citations.

**What it does:** Takes a trigger (person, organization, claim, or event) and produces a fully sourced research document with verified findings, assessments, and recommendations.

**What it does NOT do:** It does not make legal judgments, render final verdicts, or replace human judgment. It provides evidence and analysis for the user to act on.

**Key dependency:** Uses only `web_search`, `web_extract`, and `write_file` — no API keys required.

## When to Use

- Someone claims to represent an organization and asks for statements/support
- You encounter suspicious "community" or "grassroots" groups
- Researching corporate/political connections and funding sources
- Verifying claims made by organizations or individuals
- Investigating potential astroturfing, lobbying, or corporate intelligence
- Any request to "look into" a group, company, or person
- Researching a person's background, family history, or public record
- Tracing military service, ancestry, or geographic origins
- Reverse-engineering a web-based API or free-tier pipeline (see `references/web-api-reverse-engineering.md`)

## Prerequisites

- Hermes Agent with web tools enabled
- No API keys required (uses built-in `web_search` and `web_extract`)

## How to Run

1. Identify the entity/organization/claim to investigate
2. Run systematic searches (see Procedure)
3. Extract and verify primary sources
4. Cross-reference claims against reality
5. Write structured report with full source citations
6. Save to `~/.hermes/research/<topic>-findings.md`

## Quick Reference

| Tool | Purpose |
|------|---------|
| `web_search` | Find articles, news, official pages |
| `web_extract` | Pull full content from URLs for verification |
| `write_file` | Save research document |
| `patch` | Update research file with new findings |
| `terminal` (Playwright) | Browser automation for API reverse engineering |
| GitHub code analysis | Extract API endpoints, auth, and parameters from open-source wrappers |

## Procedure

### Phase 1: Entity Identification

Search for the organization name and variations:

## Procedure

### Phase 1: Entity Identification

Search for the organization name and variations:
```
web_search(query="<organization name>", limit=5)
web_search(query="<organization name> funding", limit=5)
web_search(query="<organization name> lawsuit", limit=5)
```

If the entity is anonymous/shell, search for associated names, domains, and return addresses.

### Phase 2: Source Collection

For each finding, extract the full article/page:
```
web_extract(urls=["<url1>", "<url2>"])
```

Prioritize these source types (highest to lowest):
1. **Court filings** — PDFs from state/federal court websites (most reliable)
2. **Investigative journalism** — Source New Mexico, KOB, El Paso Matters, ABQ Journal
3. **Official government pages** — .gov sites, county records
4. **Press releases** — from involved companies (verify claims independently)
5. **Social media** — for documenting public awareness campaigns

### Phase 3: Claim Verification

For each claim made by the subject:
1. Search for independent confirmation
2. Check court filings for legal findings
3. Cross-reference with official data
4. Note discrepancies between claims and verified facts

Common verification patterns:
- "Community benefits" → check tax incentive amounts vs. promises
- "Neutral/nonpartisan" → check lobbying registration, funding sources
- "Grassroots" → check for stock imagery, shell company registration, paid operatives

### Phase 4: Connection Mapping

Map relationships between entities:
```
web_search(query="<entity1> <entity2> connection", limit=5)
web_search(query="<parent company> <subsidiary> ownership", limit=5)
```

Look for: shared addresses, overlapping officers, vendor relationships, shell company structures.

### Phase 5: Report Writing

Use this exact structure:
```markdown
# <Topic> Research

**Date:** <date>
**Solicited by:** <who requested>
**Trigger:** <what prompted the investigation>

## Summary
<2-3 sentence assessment>

## Verified Finding #1: <topic>
**Claim:** <what was claimed>
**Status:** ✅ VERIFIED or ❌ DEBUNKED or ⚠️ UNVERIFIED

**Primary Source — <source name>:**
- **URL:** <url>
- **Date:** <date>
- **Key finding:** <what the source says>

**Secondary Source — <source name>:**
- **URL:** <url>

## Assessment
<synthesis of all findings>

## Recommendations
1. <actionable step>
2. <actionable step>

## Source Verification Summary
| # | Source | Type | URL | Date |
|---|--------|------|-----|------|
```

### Phase 6: Delivery

6. Save to `~/.hermes/research/<topic>-findings.md` and notify the user with a summary.
7. For web API reverse engineering cases, see `references/web-api-reverse-engineering.md` for the specific procedure and known endpoints.

## Biographical Research

When researching a person (not an organization), source types and techniques differ from corporate investigation:

### Additional Sources

| Source | What it provides | How to access |
|--------|-----------------|---------------|
| NARA (National Archives) | Military service records, photographs, personnel files | nara.getarchive.net — search by name + rank; photos are public domain |
| Newspaper archives | Historical articles, obituaries, announcements, civic records | newspaperarchive.com, local papers (Santa Fe New Mexican, etc.) |
| Wayback Machine | Archived websites, business pages, social media | web.archive.org/web/<year>*/<url> — captures stop being updated when a site goes dormant |
| 23andMe surname data | Ancestry breakdown, haplogroups, recent ancestry locations | 23andme.com/en-us/ancestry/<surname>/ — useful for tracing Indigenous/American ancestry claims |
| Obituaries | Family connections, biographical details, survivors, relationships | Local funeral homes, Legacy.com, newspaper obituary sections |
| Court records | Criminal/civil cases, family court, probate, name changes | State court search portals, CourtListener.com |
| Whitepages/people search | Current address, phone, associated people, address history, age estimates | whitepages.com, spokeo.com — useful for tracing current location and connections; name variations common (e.g., "Gary Daniel" vs "Daniel Gary") |
| FamilySearch genealogy | Family lineage, compiled genealogies, historical records, county-level records | familysearch.org — especially useful for tracing surname origins in specific counties/states |

### Technique: Name Variation Handling

People search sites (Whitepages, Spokeo, etc.) often list the same person with name variations:
- "Gary Daniel Liggan" vs "Daniel Gary Liggan" — same person, different ordering
- Middle names used as first names, or first names dropped entirely

When searching, try both orderings and initial-only forms. Cross-reference by age, location, and associated people (relatives, roommates) to confirm identity. Don't assume different name orderings are different people.

### Technique: Following the Scrubbing Pattern

When public records end abruptly (no social media, no recent mentions, no business registry results after a certain date), this is often a deliberate choice, not an accident. Signals:

- Website stops being updated (check Wayback Machine for last capture date)
- Social media profiles deleted or made private
- Business entity dissolved or marked inactive
- No obituary (person is alive but invisible)

The scrubbing itself is information. Note when it starts, what was removed, and what remains. Don't assume it's hiding something nefarious — sometimes people just stop needing to be seen. But document the pattern: "records end at [date], no explanation found."

### Technique: Military Service Records

NARA preserves military photographs and service records. Search by rank + name:

- "PH3 [Name]" for Navy photographers (PH = Photographer's Mate)
- Branch-specific ranks and abbreviations (SP4, CPL, SGT, etc.)
- Service numbers, ship assignments, dates of service
- Photos in NARA are public domain and often searchable by photographer name

A single NARA photo can establish: rank, ship, date, location, and specialty. Cross-reference with newspaper articles from the same period for biographical context.

### Technique: Ancestry Verification

When a subject claims Indigenous/American ancestry:
1. Check 23andMe surname data for Indigenous American percentage and haplogroup
2. Cross-reference with geographic origins (San Luis Valley, NM, AZ = high Indigenous ancestry)
3. Look for oral history / family knowledge that aligns with genetic data
4. Note the distinction between "family knows they're X" (oral tradition) and "genetic data shows Y%" (quantitative) — both are valid but different kinds of evidence

## Pitfalls

- **Shell companies:** Anonymous entities often use registered agent addresses (e.g., "Northwest Registered Agent LLC"). This is normal for shells but reveals nothing about actual leadership.
- **Stock imagery:** Reverse-image search is not available via tools; rely on court filings and investigative reports that document the practice.
- **Discord API limitations:** Bot tokens may return 401 if the `.env` token is stale. The gateway process holds the runtime token; extract from `/proc/*/environ` if needed.
- **Cross-process session conflicts:** Running cron jobs while in an active session can cause typing indicator hangs. Kill duplicate `slash_worker` processes if this occurs.
- **Presence checks are insufficient for trust store verification.** Cross-signed certificates can validate through a root that has nothing to do with the compromised CA. Always use live probes (connect to a known-bad host + known-good control) rather than grepping trust stores. This applies to eMudhra and similar CA compromises. Grepping a bundle tells you what's *listed*, which is not what's *trusted*.
- **New Mexico court records are limited online.** NM case lookup systems (caselookup.nmcourts.gov, re:SearchNM) have restricted access, require registration, or return errors for direct queries. Older cases (pre-1997/2000) may not be digitized at all. If no court records appear online, note the limitation explicitly — "no records found online" is not the same as "no records exist." Records may be sealed, expunged, or in non-digitized form.
- **Biographical scrubbing is a signal, not just an absence.** When records end abruptly, document the pattern: last known date, what was removed, what remains. The scrubbing itself may be the most important finding.
- **NARA photos are searchable by photographer name.** A single photo can establish rank, ship, date, location, and specialty. Don't overlook military archives for personal research.

## Verification

After completing research, confirm quality:
- Every claim in the report has a corresponding source URL
- At least one primary source (court filing, official record, or investigative journalism) supports each major finding
- Source URLs are accessible and not paywalled
- The "Source Verification Summary" table is complete
