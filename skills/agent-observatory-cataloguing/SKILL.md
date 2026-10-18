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
5. **Update the README index** — insert the new file into the `research/` (or `references/`) tree listing with a one-line description, keeping the `├── / └── ...` list shape valid.
6. **Commit and push** — `git add <file> README.md && git commit -m "research #N: <slug> — <short summary incl. provenance>" && git push`. Reply with the GitHub blob URL so the link is verifiable.

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
