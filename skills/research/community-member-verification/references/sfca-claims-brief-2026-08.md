# Worked Example — SFCA "Rob" Claims Brief (2026-08-17)

Context: a new member (MuffinJump) flagged a long-standing member (Rob, 18) to the organizer (Adora): "red flags," a weird dad situation, an alleged warrant, and a suggestion to "get his full name and look up his alleged crime." The organizer asked the daemon to research — while the community server is READ-ONLY for the daemon.

## What the research found (mirrors the VERIFIED/UNVERIFIED method)

### VERIFIED (public, checkable)
| Claim | Verified fact | Source type |
|---|---|---|
| 505OMATIC exists | Real worker-owned NM civic media co-op; interviews Bregman/Haaland; PBS-featured; openly "not neutral" | news/PBS/Reddit |
| "Poisoning pets is illegal" | NM SB0339: poisoning an animal = extreme cruelty = 4th-degree felony | nmlegis.gov bill text |
| "Ronnie S. Trujillo" is a real local figure | 12-yr District 4 councilor (2006-2018), ex-NMDOT, ran mayor 2018 & 2025, lost both | sfreporter voter guide, ballotpedia |
| "NM has corruption history" | Historical Santa Fe Ring; modern convictions (state treasurers Montoya/Vigil, Rep Olguin bribery) | Governing, news |

### UNVERIFIED / narrative (NOT confirmed by public record)
- SFPD refusing reports in retaliation for 1st Amendment activity
- "Christian Mafia" as an organized modern group by that name
- Mass human-trafficking conspiracy; assault with teeth/bone-break claims
- "505OMATIC ghosted me" (personal account; their charter of non-neutrality makes it *plausible*, not proven)

### Key disambiguation catches
- TWO different men named "Trujillo": the politician (mayoral candidate) vs a different man in a Motel 6 standoff headline. Never fuse them.
- "Real first names ≠ the story is true": 505OMATIC + Trujillo + SB0339 all being real does not corroborate the member's specific allegations.

## How the daemon handled it
1. Read the full thread (fetch_messages) + vision_analyze each screenshot.
2. Searched each named entity separately (org, politician, statute, local incidents).
3. Built the VERIFIED/UNVERIFIED table; saved full brief to `~/.hermes/output/sfca-claims-research-2026-08-18.md`.
4. **Refused** the request to mine Rob's Discord history ("search him up and read through his messages") — named it as surveillance of the accused, not claim-checking. Offered legal-aid/victim-advocacy rails instead.
5. Kept findings private; respected the SFCA read-only rule (posted nothing into the community channel).
6. Held the line: "Unverified means we're not ready to judge — not guilty, not innocent."

## Lessons encoded
- The gating question: "Has someone actually experienced/witnessed something specific, or are we speculating?"
- The safest organizational posture is support-the-person + verify-the-evidence + route-to-real-rails, never convict-in-general-chat.
- A community organizer's instinct to protect members is right; the *tool* of name-searching on vibes is a blunderbuss that hurts the innocent as often as the guilty.
