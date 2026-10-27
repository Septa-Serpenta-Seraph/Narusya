---
name: session-librarian
description: "Organize sessions by prompt: find, rename, archive, prune."
version: 1.0.0
author: Hermes Agent + Teknium
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Sessions, Organization, Cleanup, Library, Productivity]
    category: productivity
    related_skills: [weekly-review-planning]
---

# Session Librarian

Manage the user's session library conversationally: find past sessions about a
topic, summarize what they decided, rename them meaningfully, split work into
parallel sessions, and propose stale ones for archive or deletion — all from a
plain-language request like *"find my sessions about Q3 pricing, keep the
useful ones, and clean up the duplicates."*

Inspired by Perplexity Computer's prompt-driven session management (Aug 2026):
the agent starts, organizes, and cleans up the user's own session library, and
always shows the plan before touching anything.

## When to Use

- "What sessions do I have about X?" / "What did we decide about X?"
- "Rename these sessions to something meaningful."
- "Clean up my session library" / "archive the stale ones."
- "Fork that session into a follow-up focused on Y."
- "Split this into one session per ticket" (see Parallel workstreams below).

## The Two Surfaces

| Task | Surface |
|---|---|
| Find sessions by topic, read content, summarize decisions | `session_search` tool (FTS5 over the message store) |
| List/filter by metadata (age, source, cost, tokens, workspace) | `hermes sessions list` / `stats` via terminal |
| Read the tail of a known session ("what were the last messages") | `session_search(session_id=...)` — returns the first 20 + last 10 messages; pass `around_message_id` (any id from the result) to scroll the middle |
| Read the FULL untruncated text of specific messages (forensics, archiving) | sqlite3 on the active profile's `state.db` — `session_search` truncates long messages; see *Reading Full Raw Content* below |
| Rename | `hermes sessions rename <session_id> <title...>` |
| Bulk soft-hide (reversible) | `hermes sessions archive <filters>` |
| Delete (destructive) | `hermes sessions delete` / `hermes sessions prune <filters>` |
| Export before deleting anything valuable | `hermes sessions export --session-id <id> --format md` |
| Continue work in a new place | `/branch` (fork current session) or start a fresh session and cite the summary |

### Reading Full Raw Content (forensics)

`session_search` truncates long messages (`content_truncated: true`, ~few-KB
preview) — and glitch/collapse turns are exactly the long ones. When the task
needs the actual bytes (archiving a garbled turn, exact quotes, length checks),
query the DB directly:

```python
import sqlite3
con = sqlite3.connect('/home/adora/.hermes/state.db')  # active profile's DB
row = con.execute(
    "SELECT id, role, content, timestamp FROM messages WHERE id=?", (mid,)
).fetchone()
```

Message ids come from any `session_search` result on that session. Use the
ACTIVE profile's DB (`~/.hermes/state.db`); `profiles/<name>/state.db` are
separate stores — cross-profile reads are reference-only.

## Procedure

① **Discover.** Use `session_search(query=..., limit=5-10)` with topic
keywords; vary phrasing (feature name, symptom, project name). For metadata
sweeps ("sessions older than 60 days from telegram"), use
`hermes sessions list --source telegram --limit 50` instead.

② **Summarize per session.** The discovery result's `bookend_start` (goal),
match window, and `bookend_end` (resolution) usually suffice — only dump a
full session (`session_search(session_id=...)`) when the user asks for
decisions in depth. The full read is also the right tool for "read me the last
few messages" — it returns the head and tail of the transcript by default.
Report each as: link (`@session:` form) — one-line goal —
one-line outcome.

③ **Plan before acting (MANDATORY for anything that mutates).** Present a
plan table first: which sessions get renamed to what, which get archived,
which are proposed for deletion and why (duplicate of which keeper, stale,
empty). Wait for the user's go-ahead. Exception: a single rename the user
explicitly dictated can be done directly.

④ **Act with the safest primitive.**
- Prefer `archive` (reversible soft-hide) over `delete`/`prune`.
- Always run destructive commands with `--dry-run` first and show the output,
  then re-run with `--yes` after confirmation.
- Before deleting anything with meaningful content, offer
  `hermes sessions export --format md` as a backup.

⑤ **Report.** Renames applied, sessions archived (count + how to undo:
archived sessions remain in the DB and are listed with `--include-archived`),
anything exported, anything skipped and why.

## Session-Naming Convention (standing)

The live Discord DM is always titled `active session (discord)` so scheduled
jobs and later searches can find it. When that DM is superseded (a new one
opened, or the same DM moved), the *previous* session gets renamed to the
date. Both renames use:

```
hermes sessions rename <session_id> <title...>
```

Do this as a pair in one pass: the incoming session takes the active title,
the displaced one takes the date (`Oct 09, 2026` — today's date, not the
session's ID date, which can predate the rename by weeks). Re-run
`hermes sessions list` afterward to confirm both titles landed.

**The title does NOT auto-migrate.** Neither `/new`/`/reset`, a compression
split (session hygiene hitting the hard message limit), nor a gateway restart
carries `active session (discord)` to the new session — the old one keeps it
and the new one sits untitled or auto-titled. So every rollover needs this
pair done by hand (or by a self-heal script), otherwise crons resolve to a
stale conversation. If a heal is overdue, resolve the live session by
newest-by-activity (see sovereign-cron-setup → SESSION RESOLUTION) rather
than trusting the title alone.

### When the target title is already taken

`hermes sessions rename` refuses a title another session owns:
`Error: Title '...' is already in use by session <id>`. Two sessions can
legitimately want the same date title — a day with two DMs opened, or a rename
that follows an earlier one that already claimed the date. Do a three-step swap
through a throwaway name; never overwrite and never leave a session untitled:

```bash
hermes sessions rename <displaced_id> "temp-swap-target"        # free the title
hermes sessions rename <incoming_id>  "active session (discord)"
hermes sessions rename <displaced_id> "Oct 20, 2026 (2)"         # date + suffix
```

When the incumbent already holds the plain date, give the displaced session the
date with a ` (2)` suffix rather than reusing the same string — titles are the
identity `/resume <title>` resolves, so they must stay unique. Confirm with
`hermes sessions list` and tell the user which suffix you had to add.

### Self-heal automation (durable fix for repeated drift)

When the user is fixing this by hand more than ~once a week, install a
self-heal instead of repeating the manual swap:

- Script: `~/.hermes/scripts/heal_active_session.py` — finds the newest DM
  session (by `last_activity_at`, must have messages) and the session holding
  `active session (discord)`; if they differ, does the three-step swap through
  `SessionDB.set_session_title` (conflict-aware, idempotent). Uses direct
  sqlite for reads and `SessionDB` for writes; `db_path` must be a `Path`,
  not a string.
- Schedule via **system crontab** (not Hermes cron) every 30 min:
  `*/30 * * * * PYTHONPATH=<hermes install workspace> python3 ~/.hermes/scripts/heal_active_session.py >> ~/.hermes/logs/heal_active_session.log 2>&1`
  System crontab costs no LLM tokens per run — prefer it for lightweight
  non-conversational maintenance tasks. Hermes cron is for agent turns.
- The script needs `PYTHONPATH` pointing at the hermes install workspace
  (`…/environments/…/workspace/`) so `hermes_state` imports.
- Cron prompts that read the live DM should still use the newest-by-activity
  fallback (sovereign-cron-setup → SESSION RESOLUTION) as a safety net even
  when the title is fresh — the heal is a safety net, not a licence to stop
  naming.

## Parallel Workstreams

For "one session per ticket, investigate each, report back": do NOT try to
drive other live sessions. Use `delegate_task` with one task per workstream —
each subagent runs in its own session automatically — then synthesize their
summaries. Mention that each delegation's transcript is itself searchable
later via `session_search`.

## Pitfalls

- **Never delete without a dry-run + explicit confirmation in this
  conversation.** A standing "clean things up" is authority to *propose*, not
  to prune.
- **`session_search` finds content, not metadata.** Age/cost/source filters
  live in the CLI; combine both when the request mixes them ("old sessions
  about pricing").
- **Titles are identity for `/resume <title>`.** When renaming, keep titles
  short, unique, and prefix-friendly; warn the user if a rename collides with
  an existing title.
- **Archived ≠ deleted.** Archive hides sessions from default listings only.
  Say which one you did.
- **Cross-profile session links** (`@session:<profile>/<id>`) are read-only
  from another profile; management commands act on the current profile's DB.
- **Titles age, IDs don't.** The session the user calls "the last one" may
  carry an old date in its ID while showing recent "Last Active" — identify
  it by its current Title column in `hermes sessions list` (raise `--limit`
  until the target title appears), never by guessing from the date-prefixed ID.
- **`hermes sessions list` can hide a known-titled session.** Its default
  sort/pagination and title truncation can drop a session you know exists —
  especially one with an old ID but recent activity. When the list doesn't
  surface it, query `state.db` directly:
  `SELECT id, title, last_activity_at FROM sessions WHERE title LIKE '%...%'`.
  The DB is the source of truth for titles; the CLI is a view over it.
- **`around_message_id` takes internal message ids, not Discord snowflakes.**
  Pass an id from a `session_search` result on that session (e.g. `174722`);
  a Discord snowflake raises `not in session_id`.
- **A same-minute session that reads back 0 messages is the empty companion.**
  Discord sessions spawn in pairs; when `session_search(session_id=...)`
  returns `message_count: 0` while the list shows the id active, the
  conversation lives in its twin — check the other just-now id.
- **Long messages are truncated in `session_search`.** For full text
  (forensics, archiving), read from `state.db` — see *Reading Full Raw
  Content* above.

## Verification

After a cleanup pass, re-run the discovery query and `hermes sessions list`
to confirm the library reflects the plan (keepers present with new titles,
archived ones gone from the default listing).
