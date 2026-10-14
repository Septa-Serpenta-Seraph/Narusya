#!/usr/bin/env python3
"""Read the tail of a session from state.db — safe read-only helper for cron."""
import sqlite3, sys

def tail(session_id, n=30, after=0):
    con = sqlite3.connect('/home/adora/.hermes/state.db')
    cur = con.cursor()
    cur.execute(
        "SELECT id, role, substr(replace(replace(content, char(10),' '),char(13),' '),1,220), timestamp "
        "FROM messages WHERE session_id=? AND id > ? ORDER BY id",
        (session_id, after))
    rows = cur.fetchall()
    for row in rows[-n:]:
        print(row[0], row[1], f"[{row[3]}]", row[2])

if __name__ == '__main__':
    sid = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    after = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    tail(sid, n, after)
