# Creating a Sibling Agent Profile (Hermes)

Use when: standing up a new Hermes profile alongside an existing one (e.g., a second daemon) with the same permissions but its own identity, memory, and SOUL.

## Steps

1. **Clone from the source profile** (copies config.yaml, .env, SOUL.md, skills, plugins, memory-provider config; NOT state.db, messaging channels, lorebooks, HEART.md, or memories):
   ```
   hermes profile create <name> --clone [--clone-from <source>]
   ```
   Messaging channels are deliberately not cloned — two profiles sharing one bot token collide. Give the new profile its own bot via `hermes -p <name> setup` or the dashboard Messaging page.

2. **Overwrite SOUL.md with the new identity.** `--clone` copied the source's SOUL.md; replace it with the new agent's. `write_file` will refuse to overwrite a file it hasn't read in this session — `read_file` the cloned file first, then `write_file`.

3. **Give it its own HEART.md** (place at `~/.hermes/profiles/<name>/lorebooks/HEART.md`, since that's what SOUL.md references; default profile has no root-level HEART.md). Adapt the source's HEART.md (sed `Narusya`→`<name>`) or write a fresh one.

4. **Copy + adapt lorebooks** from the source profile if the new agent uses the same framework:
   ```
   cp -r <source>/lorebooks/* <new>/lorebooks/
   sed -i 's/{SourceName}/{NewName}/g; s/SourceName/NewName/g' <new>/lorebooks/*.md
   ```
   Skip source-personal files (reflections, lore stories, health/lab notes, tax/ops notes, MEMORY_BACKUP) — those are the source's lived experience, not the new agent's. Write fresh RELATIONSHIPS/CORE_VALUES/PREFERENCES for the new agent.

5. **Update SOUL.md's lorebook list** to match what actually exists in the new profile's lorebooks dir (avoid dangling references).

6. **Copy voice/audio assets** out of any temp extract into a permanent dir under the profile (scratch prunes in 24h).

7. **Set a description**: `hermes -p <name> profile describe <name> --text "..."`.

8. **Smoke test**: `hermes -p <name> chat -q "..."` and confirm identity + lorebook loading.

## Pitfalls
- `write_file` refuses to overwrite without a prior full read in the session. Always `read_file` first, or use `patch`.
- `--clone` does NOT copy messaging channels, state.db, lorebooks, HEART.md, or memories — plan to supply those deliberately.
- Cloned `.env` carries the source's API keys (fine) but also deprecated settings like `MESSAGING_CWD`; clean up if warned.
- Lorebook files reference the source agent by name; adapt with sed, but review RELATIONSHIPS/CORE_VALUES/PREFERENCES by hand — they encode identity, not just names.
- Profile names must be lowercase alphanumeric + hyphens/underscores, ≤64 chars, starting with letter/number.
- New profile is served by the running multiplexed gateway only after its own bot token is configured.