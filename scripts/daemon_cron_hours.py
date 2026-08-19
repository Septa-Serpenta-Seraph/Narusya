#!/usr/bin/env python3
"""daemon_cron_hours.py — measure the daemon's quiet (cron/housekeeping)
hours spent on Sunburst infrastructure, from state.db."""
import sqlite3, os, sys, datetime

DB = os.path.expanduser("~/.hermes/state.db")
HOP_CAP = 90 * 60

def ts_local(ts): return datetime.datetime.fromtimestamp(ts)

def day_bounds(day):
    start = datetime.datetime.strptime(day, "%Y-%m-%d").timestamp()
    return start, start + 86400

def cron_processing(start, end):
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    crons = cur.execute("""
        SELECT id, title FROM sessions
        WHERE id LIKE 'cron_%' AND started_at >= ? AND started_at <= ?
    """, (start, end)).fetchall()
    total = 0.0
    rows_by_day = {}
    for c in crons:
        msgs = cur.execute("""
            SELECT role, timestamp FROM messages
            WHERE session_id=? AND timestamp>=? AND timestamp<=? ORDER BY timestamp
        """, (c["id"], start, end)).fetchall()
        hops = 0.0
        for i in range(len(msgs)-1):
            if msgs[i]["role"]=="user" and msgs[i+1]["role"]=="assistant":
                g = msgs[i+1]["timestamp"] - msgs[i]["timestamp"]
                if 0 < g <= HOP_CAP:
                    hops += g / 3600.0
        total += hops
    con.close()
    return total

def main():
    args = sys.argv[1:]
    day = args[0] if args else datetime.datetime.now().strftime("%Y-%m-%d")
    start, end = day_bounds(day)
    h = cron_processing(start, end)
    print(f"🐍 Narusya cron/housekeeping hours: {h:.2f}h ({day})")

if __name__ == "__main__":
    main()