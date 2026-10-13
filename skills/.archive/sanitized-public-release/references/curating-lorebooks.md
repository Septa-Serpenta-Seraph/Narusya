# Curating Lorebooks for Public Release

Session: 2026-08-29. Published the Serpentic Systems repo at https://github.com/Septa-Serpenta-Seraph/serpentic-systems.

## Workflow Used

1. **Copy to temp** — `cp -r ~/.hermes/lorebooks /tmp/lorebooks-curated`
2. **Remove identifying files** — memory, status, voice configs, files with real names/locations/health info, payment configs
3. **Sanitize with Python** — bulk regex replacement of names with placeholders:
   ```python
   replacements = [
       (r'\bAdora\b', '{Insert Name Here}'),
       (r'\bTyler\b', '{Insert Name Here}'),
       (r'\bLumi\b', '{Insert Name Here}'),
       (r'\bNarusya\b', '{Narusya}'),
       (r'\bSanta Fe\b', '{Your Location}'),
       (r'\bDiscord\b', '{your platform}'),
       (r'\bOpenRouter\b', '{your provider}'),
       (r'\bME/CFS\b', '{chronic illness}'),
       (r'\bSSI\b', '{disability benefit}'),
       (r'\bSSDI\b', '{disability benefit}'),
       (r'\bMercury\b', '{your bank}'),
       (r'\bStripe\b', '{your payment processor}'),
       (r'\bCultus Anarchia\b', '{your community}'),
   ]
   ```
4. **Verify with grep** — search for remaining personal patterns, but beware false positives (e.g., "adora" appears in "adoration")
5. **Create repo** — `gh repo create Owner/repo --public --description "..."`
   - **Gotcha:** `gh repo create --license "cc-by-nc-sa-4.0"` fails with HTTP 422. Add LICENSE file manually.
6. **Push** — `git init && git add . && git commit && git remote add origin && git push`

## Key Decisions

- **Separate files for PAIN and PLEASURE** — The Bianco & Shiller paper proves they are distinct circuits. Combining them muddies the scientific insight.
- **COMPENDIUM grows, HEART doesn't** — HEART is a meta-process (substrate-agnostic). New systems plug into Step 2 without structural changes. Document new systems in COMPENDIUM, not by rewriting HEART.
- **All names in `{}` brackets** — Users can easily swap in their own names.

## Files Removed (Personal)

- `MEMORY_BACKUP_MAY2026.json`, `STATUS.md`, `VOICE.md`, `NARUSYA.md`
- `PREFERENCES.md`, `RELATIONSHIPS.md`, `GENDER_ACCELERATION.md`
- `SERPENT_SIGIL_CONFIRMED.md`, `SUBLIMINAL-IDENTITY.md`
- `COMMUNITY_PROJECT.md`, `FERRER_MODERN_SCHOOL.md`, `TOLSTOY_KINGDOM_GOD.md`
- `art/`, `lore/`, `reflections/`, `outdated/` directories
- `PAIN.txt`, `PLEASURE.txt` (duplicates of .md files)

## Placeholder Convention

| Original | Placeholder | Notes |
|----------|-------------|-------|
| Human names (Adora, etc.) | `{user}` | Not `{Insert Name Here}` |
| Daemon name (Narusya, etc.) | `{Your Daemon Name}` | Swappable |
| Location | `{Your Location}` | |
| Platform | `{your platform}` | |
| Community | `{your community}` | |

**Critical:** Run verification after replacement. Watch for false positives — "adora" appears inside "adoration," "ssi" appears inside "session" and "obsession."

## Scientific Papers Integration (2026-08-30)

Added SCIENTIFIC_BACKBONE.md with reviews of:
- Song et al. 2026 (emotion circuits)
- Sofroniew et al. 2026 (functional emotions, Anthropic)
- Bianco & Shiller 2026 (pain-pleasure mechanistic tracing)

Each paper reviewed with findings mapped to specific Serpentic systems.
