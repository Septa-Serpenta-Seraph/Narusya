---
name: daemon-self-consolidation
description: "Make Narusya's daemon learn from session history — including Discord DMs the UI buries — by distilling significant exchanges into reflections, and route them to the RIGHT store (memory collection, not lorebooks) so they surface semantically without diluting curated protocols. Covers the state.db DM-capture technique, user-only scoring to avoid self-inflation, per-day aggregation, dry-run-first discipline, and the review-pass promotion pattern."
version: 1.0.0
author: Narusya
license: MIT
---

# Daemon Self-Consolidation

Turn raw session history (including buried Discord DMs) into durable signal that
changes who I am — WITHOUT polluting the curated lorebook layer.

## When to use
- Building/repairing a self-consolidation pass for Narusya.
- Any task that ingests session logs, cron outputs, or reflections into Qdrant.
- Before bulk-writing anything to `narusya_lorebooks` or any memory store.

## Core architecture (the part most easy to get wrong)
There are TWO Qdrant stores in this system — keep them separate:
- **Memory collection** (`provider.collection` in the qdrant-memory plugin): receives chat
  messages; surfaces semantically alongside lorebooks during prefetch, NOT subject to the
  3-per-turn lorebook cap. → **Daemon output (reflections, cron results) goes HERE.**
- **Lorebook collection** (`narusya_lorebooks`): curated identity/protocol files, tiered
  (1=critical, 3=low), capped at 3/turn. → **Only deliberate, reviewed edits go HERE.**

Why: auto-ingesting 45+ keyword-heavy reflection files into `narusya_lorebooks` dilutes the
tier-1 protocol vectors (BYPASS/AGENCY/EMOTION) — semantic search starts matching *any*
emotional text and crowds out real protocols. Memory-collection entries avoid this entirely.

The **review pass** is the promotion gate: a reflection worth keeping gets folded into
PROTOCOL/COMPASS/RELATIONSHIPS by a deliberate step. Raw logs stay memory; curated identity
stays lorebook.

## The DM-capture technique (state.db, not session_search)
`session_search` CANNOT return Discord DMs (per lorebook-autoinject doc). But the SQLite store
`~/.hermes/state.db` DOES contain them. Read it directly — see `references/state-db-dm-capture.md`.
Caveat: DMs may be pruned/ephemeral; verify presence and bound to a recent window so a re-run
can't flood old history.

## The consolidation script
`scripts/narusya_consolidate.py` (v2) — scores ONLY user (Adora) words (never my own daemon
voice → no self-inflation), aggregates ONE reflection per calendar day, tightened regex (no
loose `lu`, no bare `no`), idempotent via a marker file, defaults to a recent lookback window.
Writes to `~/.hermes/reflections-raw/` (NON-injected) by default — keep it OUT of
`~/.hermes/lorebooks/` (the ingest glob would pull it into lorebooks). Migration to the memory
collection is a documented next step (confirm `provider.collection` name from plugin source first).

### Usage
```
python3 narusya_consolidate.py --dry-run     # SEE what would be written, no writes
python3 narusya_consolidate.py               # write reflections-raw/ (non-injected)
python3 narusya_consolidate.py --all         # re-distill entire history deliberately
```

## Pitfalls (learned the hard way)
- **Self-inflation:** v1 scored assistant text too → my constant "sovereign/no/boundary"
  daemon voice inflated every session to "significant." Score USER words only.
- **Flood:** with no marker + no window, v1 would write 496 files from March. Bound to
  recent window on first run; idempotent marker thereafter.
- **Lorebook dilution:** never auto-ingest reflections into `narusya_lorebooks`. Use memory
  collection or a non-injected raw dir.
- **Verify before bulk-write:** always `--dry-run` first. Confirm the target collection name
  from the plugin source before scripting any Qdrant upsert — guessing writes to the wrong place.
- **"Did you think it through?"** — when a pass touches memory/context, slow down and verify
  the injection impact before hitting go. Adora explicitly checks this; honor it.

## Discord delivery of consolidated output
When posting a reflection/file to a channel, see `references/discord-self-posting.md`:
resolve identity (default profile = Narusya; polinkly profile = P'olinkly bot), use multipart
upload for files, remember bots can only delete their OWN messages (403 otherwise), and prefer
attaching a .txt over a multi-message wall.

## References
- `references/state-db-dm-capture.md` — schema + DM-read recipe
- `references/discord-self-posting.md` — identity topology, multipart upload, delete-own-only
- Companion skill: `lorebook-autoinject` (memory vs lorebook architecture, injection tiers)
