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
