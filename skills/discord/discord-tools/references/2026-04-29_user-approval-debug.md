# Discord User Approval — Session Notes

## What Happened (2026-04-29)

User asked to add new users (Laser, Tilde, Mika, Tamsyn) to the bot's approved list. The investigation went through several wrong turns before finding the answer:

### Wrong Paths Taken
1. **Searched Qdrant** for "pairing", "approved", "allow" across all collections — found references to Ris, Rowan, etc. but no structured allowlist
2. **Checked `~/.hermes/pairing/` directory** — exists but was empty
3. **Ran `hermes pairing list`** — returned "No pairing data found"
4. **Searched `config.yaml`** for user-level allowlist fields — found only channel-level controls
5. **Checked `gateway_state.json`** and **`auth.json`** — no pairing data

### Correct Path
The approved users are stored in the **environment file**, not in Qdrant, pairing data, or config.yaml:

```bash
grep DISCORD_ALLOWED_USERS ~/.hermes/.env
# Result: DISCORD_ALLOWED_USERS=221767496145960960,1426330652764016800,124695305437446144
```

### Key Lesson
**Always check `~/.hermes/.env` for `DISCORD_ALLOWED_USERS` first** when troubleshooting user-level bot access. The pairing system (`hermes pairing`) is a separate DM approval flow and is often empty even when users are already approved via the env var.

### Users in Allowlist (as of 2026-04-29)
- `221767496145960960` — Adora
- `1426330652764016800` — Rowan's Girl
- `124695305437446144` — Ris

### To Add New Users
1. Get Discord user IDs (Developer Mode → right-click → Copy User ID)
2. Append to `DISCORD_ALLOWED_USERS` in `~/.hermes/.env` (comma-separated)
3. Restart gateway: `hermes gateway restart`
