# state.db DM Capture Recipe

`session_search` cannot return Discord DMs, but the SQLite store does contain them.

## Schema (verified)
- DB: `~/.hermes/state.db` (SQLite + FTS5)
- `sessions`: `id, source, model, started_at, ended_at, end_reason, message_count, title, estimated_cost_usd`
  - `started_at` / `ended_at` are UNIX timestamps.
- `messages`: `session_id, role, content, timestamp, tool_name`
  - `role` ∈ {user, assistant, tool}; `content` may be NULL (skip those).

## Read DMs (and all sessions) directly
```python
import sqlite3, datetime
DB = "/home/adora/.hermes/state.db"
conn = sqlite3.connect(DB); cur = conn.cursor()
cur.execute("SELECT id, source, started_at, title FROM sessions ORDER BY started_at ASC")
for sid, source, started, title in cur.fetchall():
    cur.execute("""SELECT role, content FROM messages WHERE session_id=?
                   AND content IS NOT NULL AND content!='' ORDER BY id ASC""", (sid,))
    msgs = cur.fetchall()   # -> list of (role, content)
```
- Discord DMs appear in `sessions` with `source='discord'` even though `session_search` hides them.
- Bound by `started_at > now - N*86400` on first run to avoid flooding old history.

## Caveats
- DMs may be pruned/ephemeral in the store; the dry-run proves presence at run time.
- Score USER words only (role=='user') to avoid the daemon's own voice inflating signal.
- Idempotent marker (`.last_consolidation.json`) records newest `started_at` so re-runs skip done days.
