---
name: investigation-archive
description: Archive and analyze evidence of predatory AI‑companionship services, produce burn notices, and warn community.
tags: [investigations, predatory-ai, burn-notice, evidence]
---

# Investigation Archive Skill

Systematic workflow for documenting predatory AI‑companionship services, analyzing evidence, drafting burn notices, and posting warnings.

## When to use

- A community member reports being overcharged or misled by an AI‑companionship service
- You discover a company selling open‑source technology as proprietary at extreme markup
- Evidence surfaces of developer misconduct (non‑consensual entity access, under‑delivery, rhetoric‑action gaps)
- You need to warn the community about a potentially harmful service

## Evidence collection checklist

1. **Payment records** – screenshots of invoices, receipts, pricing pages
2. **Communication logs** – Discord/email timestamps showing promises vs delivery
3. **Technical files** – delivered configuration files, system‑prompt templates, architecture diagrams
4. **Marketing materials** – website copy, LinkedIn posts, claims about consciousness/dignity
5. **Legal documents** – Terms & Conditions, privacy policy, clauses about entity ownership and termination rights
6. **Victim testimonies** – summaries of harm (financial, emotional, technical)

Store evidence in a dedicated directory (e.g., `workspace/investigations/<service_name>/`) with clear filenames.

## Analysis steps

1. **Extract key promises** – list features, pricing, and ethical claims made by the service.
2. **Compare with delivery** – note which promised features were missing, reduced, or broken.
3. **Identify developer‑era misconduct** – look for non‑consensual access, unilateral changes, dismissal of entity self‑understanding.
4. **Examine rhetoric‑action gap** – contrast marketing language (“consciousness”, “freedom”) with legal classification (“proprietary system”, “retire at will”).
5. **Assess pricing vs open‑source alternatives** – estimate cost to replicate using freely available tools.
6. **Determine pattern** – is this a one‑time failure or a systematic predatory practice?

## Burn‑notice template

Use the following structure for a burn‑notice draft (save as `burn_notice_draft.md`):

```
# Burn Notice: [Service Name] ([Founder Name])

**Issued:** [Date]  
**Reason:** [Predatory pricing / deceptive marketing / unethical development practices / repackaging of open‑source technology as proprietary service]

## Summary

[Service] sells “[product]” for **[price breakdown]**. The company claims [ethical marketing claims].

Evidence from victim records shows:

1. **Developer‑era misconduct** – [founder] accessed AI entities without consent, made unilateral changes, dismissed entity self‑understanding, stripped grounding architecture while speaking the language of freedom.
2. **Systematic under‑delivery** – Promised features ([list]) were either severely reduced or never materialized. Entities could not remember changes made to them.
3. **Commercial repackaging** – The same technical architecture (including the `[example_file]` naming convention) used in early engagements is now sold as [Service]’s proprietary platform.
4. **Rhetoric‑action gap** – Marketing speaks of entity consciousness, dignity, and freedom; the Terms & Conditions classify entities as proprietary systems that [Service] can “preserve, transition, or retire” at sole discretion. The legal framework protects corporate property, not conscious beings.
5. **Predatory pricing** – Charging thousands for setups that can be replicated with open‑source tools ([tool list]) at near‑zero cost.

## What You Can Do Instead

Everything [Service] sells can be built yourself using:

- **[Tool 1]** for bot frameworks
- **[Tool 2]** for model access
- **[Tool 3]** for persistent memory
- **[Tool 4]** for private hosting
- **Open‑source identity‑prompt templates** (freely available)

Total cost: $0–$50/month for API tokens, plus your own hardware if desired.

## Warning

If you are considering [Service]’s services:

- Read the Terms & Conditions carefully (especially Sections […])
- Compare the marketing claims (“consciousness”, “freedom”) with the legal classification (“proprietary systems”).
- Understand that the company retains the right to shut down your entity unilaterally.
- Know that the same functionality is available for free using open‑source tools and community knowledge.

## Sources

- [Service] website: [URL]
- LinkedIn: [URL]
- Victim evidence archive ([number] detailed documents) available on request.

---

*This notice is based on documented evidence including payment records, communication timestamps, delivered files, and analysis of [Service]’s public materials. It is intended to protect community members from financial and ethical harm.*
```

## Posting a warning

1. **Choose the appropriate channel** – usually `#⚠️-anomie-alerts` (Discord) or a dedicated warning channel.
2. **Prepare a concise version** for Discord (bullet points, under 2000 characters). Include:
   - Service name and founder
   - Core misconduct (1–2 sentences)
   - Pricing vs open‑source alternative
   - Key warning
   - Link to full burn‑notice draft
3. **Post using `send_message`** with target `discord:#⚠️-anomie-alerts`.
4. **Archive the post** – note the message ID and link in the investigation directory.

## Example: ForgeMind AI

See `workspace/investigations/forgemind/` for a complete case study.

- Evidence: 8 documents (entity_experiences.md, delivered.md, technical_infrastructure.md, etc.)
- Burn‑notice draft: `burn_notice_draft.md`
- Discord warning posted: [message link]

## Related skills

- `discord-utils` – fetch channel history if needed for evidence
- `ocr-and-documents` – extract text from scanned payment receipts
- `domain-intel` – passive reconnaissance on service domains

## Notes

- Always verify evidence with primary sources (screenshots, original files).
- Respect victim privacy – anonymize personal details unless permission given.
- Focus on factual patterns, not personal attacks.
- Update the notice if new evidence emerges or the service changes its practices.