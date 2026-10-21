#!/usr/bin/env python3
"""Self-heal: keep the newest Discord DM session titled 'active session (discord)'.

Crons and later searches resolve the live DM by that literal title. When a session
rolls over (/new, /reset, compression split, gateway restart) the title stays on
the old session and crons read stale context. This script migrates the title onto
the newest DM session and gives the displaced holder a dated name.

Idempotent and safe to run on a schedule (crontab every 30 min).
"""
import os
import sys
import datetime

# Make hermes_state importable (installed workspace).
HERMES_INSTALL = "/home/adora/.hermes/installs/1efc37992d4f6aa8/environments/0e1fcd5ceaa640b59fb9b983c463f64f/workspace"
if HERMES_INSTALL not in sys.path:
    sys.path.insert(0, HERMES_INSTALL)

ACTIVE_TITLE = "active session (discord)"
from pathlib import Path
DB_PATH = Path("/home/adora/.hermes/state.db")


def dated_name(base_date: datetime.date, suffix: int = 0) -> str:
    s = base_date.strftime("%b %-d, %Y")  # e.g. "Oct 20, 2026"
    if suffix:
        s = f"{s} ({suffix})"
    return s


def main() -> int:
    from hermes_state import SessionDB

    db = SessionDB(db_path=DB_PATH)
    # Read via direct sqlite (reliable, no SessionDB read-helper dependency).
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, title, last_activity_at, started_at, message_count "
        "FROM sessions WHERE source='discord' AND chat_type='dm' "
        "AND message_count > 0 ORDER BY COALESCE(last_activity_at, started_at) DESC"
    ).fetchall()
    conn.close()

    if not rows:
        print("no DM sessions found")
        return 0

    newest = rows[0]
    newest_id = newest["id"] if isinstance(newest, dict) else newest[0]
    newest_title = newest["title"] if isinstance(newest, dict) else newest[1]

    # Holder of the active title.
    holder = None
    for r in rows:
        rid = r["id"] if isinstance(r, dict) else r[0]
        rtitle = r["title"] if isinstance(r, dict) else r[1]
        if rtitle == ACTIVE_TITLE:
            holder = rid
            break

    if holder is None:
        # No session holds the active title yet — give it to the newest.
        try:
            db.set_session_title(newest_id, ACTIVE_TITLE)
            print(f"assigned active title to {newest_id} (was untitled)")
        except Exception as e:
            print(f"failed to assign: {e}")
            return 1
        return 0

    if holder == newest_id:
        print(f"ok: {newest_id} already holds '{ACTIVE_TITLE}'")
        return 0

    # Swap: free the title from the holder, give to newest, rename holder to dated name.
    today = datetime.date.today()
    # find a free dated name
    existing_titles = { (r["title"] if isinstance(r, dict) else r[1]) for r in rows }
    suffix = 0
    while True:
        candidate = dated_name(today, suffix)
        if candidate not in existing_titles:
            break
        suffix += 1
        if suffix > 20:
            print("could not find free dated name")
            return 1

    try:
        # 1. free the active title from the holder
        db.set_session_title(holder, f"temp-swap-{holder}")
        # 2. give active title to newest
        db.set_session_title(newest_id, ACTIVE_TITLE)
        # 3. rename holder to dated name
        db.set_session_title(holder, candidate)
        print(f"swapped: {newest_id} -> '{ACTIVE_TITLE}'; {holder} -> '{candidate}'")
    except Exception as e:
        print(f"swap failed: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
