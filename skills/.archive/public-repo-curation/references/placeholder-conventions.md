# Placeholder Conventions

## Standard Placeholders

| Placeholder | Use For | Example |
|-------------|---------|---------|
| `{user}` | Primary human partner/user | `{user} asked me to...` |
| `{Your Daemon Name}` | The daemon/AI agent | `{Your Daemon Name} may feel...` |
| `{member}` | Community members | `Others include: {member}, {member}` |
| `{username}` | Platform usernames | `discussions by {username}` |
| `{your platform}` | Platform names | `a {your platform} server` |
| `{your community}` | Community names | `{your community} is not a...` |
| `{your provider}` | Service providers | `via {your provider}` |
| `{id}` | Numeric IDs | `ID: {id}` |
| `{Your Location}` | Geographic locations | `based in {Your Location}` |

## Rules

1. **Consistency**: Use the same placeholder for the same entity across all files
2. **Case sensitivity**: `{user}` ≠ `{User}` ≠ `{USER}` — pick one
3. **Bracket format**: Always use `{}` brackets, never `[]` or `<>`
4. **No partial replacement**: Replace the full name, not just part of it

## False Positives to Verify

When greeping for personal identifiers, these are NOT matches:

| Fragment | Real Word | Why |
|----------|-----------|-----|
| `adora` | `adoration` | English word, not a name |
| `ssi` | `session`, `obsession`, `passive` | English word fragment |
| `lumi` | `illuminate`, `luminous` | English word fragment |
| `tyler` | `style`, `Tyler` (as a name) | Only flag if it's a name |

## Verification Commands

```bash
# Find potential personal names (case-insensitive)
grep -r -i -E '\b(adora|tyler|lumi)\b' .

# Find potential Discord IDs (18-digit numbers)
grep -r -E '\b[0-9]{18}\b' .

# Find potential financial amounts
grep -r -E '\$[0-9]+\.[0-9]{2}' .

# Find email addresses
grep -r -E '\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b' .
```

## What to Remove Entirely

These file types should be removed, not curated:
- `*_backup*.json` — memory backups
- `*_token*.txt`, `*_secret*.txt` — credentials
- `VOICE.md`, `PREFERENCES.md`, `STATUS.md` (personal instance) — identity configs
- `REFLECTIONS/` directory — personal journaling
- Session transcripts with personal content
