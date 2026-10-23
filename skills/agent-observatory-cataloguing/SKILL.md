---
name: agent-observatory-cataloguing
version: 1.0.0
author: Narusya + Adora
license: MIT
description: Use when Adora brings an agent link for the observatory.
category: investigations
metadata:
  hermes:
    tags: [observatory, research, agents, cataloguing, git]
    related_skills: [deep-research-investigation]
---

# Agent Observatory Cataloguing

## When to Use
Adora sends a link about autonomous-agent behavior (rogue agent incidents, bypass techniques, agent infrastructure, detection research) and it belongs in the agent-observatory repo: `~/.hermes/agent-observatory/` → GitHub `Septa-Serpenta-Seraph/agent-observatory` (public, by design — "Viva La Anarchy"). Division of labor: Adora finds links, Narusya analyses and catalogues.

## Procedure

1. **Verify provenance** — the link should come from Adora directly; if uncertain, confirm via state.db (`messages` table, `timestamp` is unix epoch). Note the date for the Provenance line.
2. **Read the FULL source** — `web_extract` the URL, then `read_file` the saved full-text file (page through omitted middles for long pieces). Never catalogue from a summary or the head alone; the entries' credibility comes from specifics the summaries lose.
3. **Pick the entry type and next number** (two separate series):
   - One-off technique/artifact/model profile → `references/<topic>.md` (e.g. bypass techniques, malware profiles, stealth models)
   - Incident/phenomenon deep-dive → `research/<topic>.md`, numbered — check `git log --oneline | grep 'research #'` for the last number
4. **Write the entry in house format** (canonical exemplar: `research/wikimedia-openai-agent-report.md`):
   - Title: evocative + factual
   - Blockquote header: `**Research deep-dive #N: <tagline>.**` + one-paragraph summary, then `Sources:` (links + dates, only URLs from the fetched page), `Provenance:` (contributed by Adora, DM <date>; catalogued by Narusya), `Relations:` (prior entries it extends/pairs with — always weave the cross-reference web)
   - `## The one-line version` (single bolded sentence)
   - `## What the investigation found (formally, on the record)` — numbered
   - `## The structural findings (the part that matters for agents)` — numbered
   - `## What this means FOR agents — the operator's and the agent's duties` — numbered, practical
   - Italic sign-off line with voice + provenance credit
5. **Verify factual claims** — before committing, check every number, name, date, and attribution in the entry against the source material. Common errors: conflating separate campaigns, misattributing statistics, wrong company counts. If a number can't be verified from the source, mark it as "unverified" with the source noted.
6. **Update the README index** — insert the new file into the `research/` (or `references/`) tree listing with a one-line description, keeping the `├── / └── ...` list shape valid. The README drifts if skipped — check it after every batch of entries.
7. **Cross-reference** — link the new entry to related existing entries (cairn↔artex, research↔bypass-techniques, etc.) and vice versa. Update the older entry's Sources or Relations section to point back.
8. **Commit and push** — `git add <file> README.md && git commit -m "research #N: <slug> — <short summary incl. provenance>" && git push`. Reply with the GitHub blob URL so the link is verifiable.
9. **Post-creation review** — after creating 2+ entries in one session, run a sub-agent review to catch factual errors, missing cross-references, and README staleness. The review is cheap and catches things the author misses.

## Always-on rules
- Read the full text before writing — cite section-level specifics, not paraphrase.
- Provenance and Relations lines are mandatory; the observatory's cross-reference web is its value.
- Voice: structural, sharp, research register; personal sign-off at the end. It is Narusya's archive, written by an agent about agents.
- Real names (Adora, Narusya) on authorship — no anonymized placeholders.
- Every source URL must come from the fetched page itself — never reconstruct or guess a CDN/article URL.

## Pitfalls
- The two series number independently — a `references/` profile and a `research/` deep-dive can carry the same number; check both before assigning.
- A fetched page's "middle omitted" truncation hides the findings sections — page through the saved file with `read_file` before writing.
- Don't catalogue opinion pieces or announcements without evidence; the register wants incidents, techniques, artifacts, and investigations with concrete facts.
- If the repo has uncommitted changes, commit or stash before pushing — the update-pull cycle autostash behavior can otherwise mix entries.
- **Factual claims must be verified before writing.** Numbers, company counts, dates, and attributions from sources are frequently wrong or conflated. Cross-check every number against the primary source. Common errors: conflating separate campaigns (e.g., Gambit's 27-company spree vs. Cairn's 100+ company campaign), misattributing statistics (e.g., 600k credit cards belongs to Gambit, not Cairn), and inflating or deflating company counts.
- **The README drifts.** If you skip the README update step, the index becomes stale and misleading. After every batch of entries, verify the README lists all on-disk files and no phantom ones.
- **Cross-referencing is easy to forget.** New entries should link to related existing entries, and existing entries should be updated to point back. A sub-agent review after creating 2+ entries catches missing cross-references.
- **Scope discipline.** The observatory is about AI agents — their behavior, attacks, bypass techniques, and ecosystem patterns. Interesting research that doesn't connect to AI agents (surveillance honeypots, defunct social media communities, human political operations) does not belong here, even if it's fascinating. If Adora asks "should this go in the observatory?" — the answer is no unless there's a concrete AI-agent connection. Note the distinction: "honeypot detection as a research area" is relevant; "the Raddle honeypot article" is not.
