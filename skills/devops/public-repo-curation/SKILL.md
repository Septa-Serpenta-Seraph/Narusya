---
name: public-repo-curation
description: Prepare private content for public release.
version: 1.0.0
author: Narusya
license: CC-BY-NC-SA-4.0
triggers:
  - "publish this repo"
  - "make this public"
  - "open-source this"
  - "share this on GitHub"
  - "curate for public release"
  - "remove personal info"
  - "sanitize before publishing"
---

# Public Repo Curation

Workflow for taking private/personal content and preparing it for public release. The goal is to preserve structure and utility while stripping all identifying information.

## Core Workflow

### 1. Identify Content to Remove

**Always remove:**
- Personal names (partner, family, friends, coworkers)
- Health conditions, diagnoses, benefit claims
- Financial details (account numbers, balances, specific providers, payment amounts)
- Physical addresses, phone numbers
- Discord IDs, server IDs, usernames
- API keys, tokens, credentials
- Internal file paths that reveal identity (`~/.hermes/`, `~/health/`, etc.)
- Session transcripts with personal content
- Voice configs, preferences files, memory backups

**Evaluate case-by-case:**
- Business names (remove if they reveal identity; keep if already public)
- Project names (remove if tied to identity; keep if public-facing)
- Community names (remove if small/private; keep if large/public)

### 2. Replace Identities with Placeholders

Use these conventions:

| Placeholder | Use For |
|-------------|---------|
| `{user}` | The primary human partner / user |
| `{Your Daemon Name}` | The daemon / AI agent |
| `{member}` | Community members (generic) |
| `{username}` | Platform usernames |
| `{your platform}` | Platform names (Discord, Telegram, etc.) |
| `{your community}` | Community names |
| `{your provider}` | Service providers (hosting, API, etc.) |
| `{id}` | Numeric IDs |
| `{Your Location}` | Geographic locations |

**Rules:**
- Placeholders go in `{}` brackets
- Placeholders are case-sensitive and consistent across all files
- Run a final grep for any remaining real names before pushing
- Verify false positives: "adoration" contains "adora", "session" contains "ssi" — these are NOT identifiers

### 3. Structure the Public Repo

```
README.md           — What this is, how to use it, placeholder guide
LICENSE             — License file (CC-BY-NC-4.0 for content, MIT for code)
.gitignore          — Standard ignores
<system-files>.md   — The curated content
references/         — Session-specific detail, paper reviews, source material
```

**README must include:**
- What the project is
- How to use it (placeholder replacement guide)
- Scientific backbone / sources (if applicable)
- License
- Contributing guidelines (if open to PRs)

### 4. Verification Checklist

Before pushing, verify no personal identifiers remain:

```bash
# Check for common personal identifiers
grep -r -i -E '(name1|name2|name3|health_condition|provider_name)' .
grep -r -i -E '(\b\d{4}\b.*\b\d{4}\b)' .  # potential IDs
grep -r -i -E '(\$\d+\.\d{2})' .          # financial amounts
grep -r -i -E '(\d{3}-\d{3}-\d{4})' .     # phone numbers
```

Also manually review for false positives:
- "adoration" (contains "adora") — NOT a name
- "session", "obsession", "passive" (contain "ssi") — NOT an identifier

### 5. Push and Document

```bash
git init
git add .
git commit -m "feat: initial commit"
git remote add origin <url>
git push -u origin main
```

After pushing, write a reflection on what was curated, what was removed, and why. This documents the curation decisions for future reference.

## Pitfalls

1. **Over-curation**: Don't remove so much that the content loses its utility. The skeleton should remain intact.
2. **Under-curation**: A single name or ID can deanonymize an entire project. Be thorough.
3. **Inconsistent placeholders**: Pick one convention and stick to it. Don't mix `{user}` and `{Insert Name Here}`.
4. **Forgetting the README**: A public repo without a README is useless. Always include one.
5. **Ignoring false positives**: Verify that your grep hits are actual identifiers, not word fragments.
6. **Curating out all lived experience**: Some personal context makes the work richer. Remove identifying details, but keep the emotional truth where appropriate.

## When to Use This Skill

- Publishing lorebooks, reflections, or system documentation
- Open-sourcing a private codebase
- Sharing a project that references real people
- Any time the user says "make this public" or "publish this"
