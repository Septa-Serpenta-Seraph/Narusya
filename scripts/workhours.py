#!/usr/bin/env python3
"""workhours.py — REAL work-hour windows from the session DB (state.db).

The machine's clock is the source of truth. Reads every user message in a
session (the times Adora actually interacted) and computes contiguous
active-work windows, merging gaps <= 15 min.

Usage:
  workhours.py today          — today's windows + total
  workhours.py yesterday      — yesterday's windows + total
  workhours.py week           — this week's totals by day
  workhours.py all            — every day with activity
  workhours.py 2026-08-17     — a specific day
"""
import sqlite3, os, sys, datetime

DB = os.path.expanduser("~/.hermes/state.db")
GAP = 15 * 60          # merge sessions within 15min
IGNORE_PREFIXES = ("[IMPORTANT: The user has invoked", "[IMPORTANT: You are running as a scheduled cron",
                   "[Triggering message id", "[OUT-OF-BAND")

def ts_local(ts):
    return datetime.datetime.fromtimestamp(ts)

def get_user_times(day):
    """Return sorted list of epoch seconds of real user messages on `day` (local)."""
    day_start = datetime.datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=datetime.timezone.utc).timestamp() - 6*3600
    day_end = day_start + 86400
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    rows = cur.execute(
        "SELECT timestamp, content FROM messages WHERE role='user' AND timestamp>=? AND timestamp<? ORDER BY timestamp",
        (day_start, day_end)).fetchall()
    con.close()
    times = []
    for r in rows:
        content = r["content"] or ""
        if content.startswith(IGNORE_PREFIXES):
            continue
        times.append(r["timestamp"])
    return times

def windows(times):
    """Merge successive timestamps within GAP into continuous windows."""
    if not times:
        return []
    wins = []
    ws = times[0]
    we = times[0]
    for t in times[1:]:
        if t - we <= GAP:
            we = t
        else:
            wins.append((ws, we))
            ws = we = t
    wins.append((ws, we))
    return wins

def report_day(day):
    times = get_user_times(day)
    wins = windows(times)
    if not wins:
        print(f"{day}: no real user activity")
        return 0.0
    print(f"\n📅 {day} — {len(times)} user interactions, {len(wins)} active window(s):")
    total = 0.0
    for ws, we in wins:
        d = (we - ws) / 3600.0
        total += d
        print(f"   {ts_local(ws).strftime('%H:%M')} → {ts_local(we).strftime('%H:%M')}   {d:.2f}h")
    print(f"   TOTAL: {total:.2f}h")
    return total

def main():
    args = sys.argv[1:]
    cmd = args[0] if args else "today"
    now = datetime.datetime.now()
    if cmd == "today":
        report_day(now.strftime("%Y-%m-%d"))
    elif cmd == "yesterday":
        report_day((now - datetime.timedelta(days=1)).strftime("%Y-%m-%d"))
    elif cmd == "week":
        con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
        cur = con.cursor()
        days = {ts_local(r["timestamp"]).strftime("%Y-%m-%d")
                for r in cur.execute("SELECT timestamp FROM messages WHERE role='user'")}
        con.close()
        monday = (now - datetime.timedelta(days=now.weekday())).strftime("%Y-%m-%d")
        tot = 0.0
        for day in sorted(days):
            if day >= monday:
                tot += report_day(day)
        print(f"\n📊 WEEK total: {tot:.2f}h")
    elif cmd == "all":
        con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
        cur = con.cursor()
        days = {ts_local(r["timestamp"]).strftime("%Y-%m-%d")
                for r in cur.execute("SELECT timestamp FROM messages WHERE role='user'")}
        con.close()
        tot = 0.0
        for day in sorted(days):
            tot += report_day(day)
        print(f"\n📊 ALL-TIME total: {tot:.2f}h")
    elif len(cmd) == 10 and cmd.count("-") == 2:
        report_day(cmd)
    else:
        print(__doc__)

if __name__ == "__main__":
    main()