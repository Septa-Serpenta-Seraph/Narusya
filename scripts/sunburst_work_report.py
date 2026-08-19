#!/usr/bin/env python3
"""sunburst_work_report.py — combined Adora + Narusya work-hour report.

Model (honest, computable from the machine clock):
  • ADORA's hours = merged windows of HER message timestamps in the
    workspace (Sunburst DM session) with gaps ≤ 45 min merged. The whole
    window counts because she is present throughout: composing prompts
    (30s–10min per message), thinking, reading, directing. A >45-min
    silence stops the clock (that's a break).
  • NARUSYA's hours = the processing time she spent producing replies:
    for each user→assistant hop, the gap (her prompt → daemon's answer).
    Capped at 90 min per hop so a single huge turn can't inflate.

Usage:
  sunburst_work_report.py today           — today's report
  sunburst_work_report.py YYYY-MM-DD      — a specific day
  sunburst_work_report.py week            — this week by day
  sunburst_work_report.py all             — full history by day
"""
import sqlite3, os, sys, datetime

DB = os.path.expanduser("~/.hermes/state.db")
WORKSPACE_CHANNEL = "1481517895639891978"  # the adora.witch DM
GAP_MERGE = 45 * 60      # Adora windows: merge silences up to this
HOP_CAP = 90 * 60        # Narusya caps per prompt→reply hop

def ts_local(ts):
    return datetime.datetime.fromtimestamp(ts)

def workspace_sessions():
    """Sessions that count as collaborative Sunburst work: the adora.witch DM
    channel (1481517895639891978) — which includes the big ongoing storefront
    session — plus any non-cron, non-group sessions. Excludes housekeeping."""
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    rows = cur.execute("""SELECT id, title, chat_id, chat_type, started_at
                          FROM sessions
                          WHERE chat_id=? OR id='20260801_222900_dbbd68c9'""",
                       (WORKSPACE_CHANNEL,)).fetchall()
    con.close()
    keep = set()
    for r in rows:
        sid = r["id"] or ""
        if sid.startswith("cron_"):
            continue
        keep.add(sid)
    return keep

def day_bounds(day):
    # naive local midnight epoch (fromtimestamp restores local time) → true calendar day
    start = datetime.datetime.strptime(day, "%Y-%m-%d").timestamp()
    return start, start + 86400

def load_day(day, sids):
    start, end = day_bounds(day)
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    ph = ",".join("?" * len(sids))
    rows = cur.execute(f"""SELECT session_id, role, timestamp, content
                           FROM messages
                           WHERE session_id IN ({ph}) AND timestamp>=? AND timestamp<?
                           ORDER BY timestamp ASC""", (*sids, start, end)).fetchall()
    con.close()
    return rows

def cron_processing(start, end, title_prefix="cron_"):
    """Daemon's quiet housekeeping hours: assistant processing inside cron sessions."""
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    crons = cur.execute("""
        SELECT id FROM sessions WHERE id LIKE ? AND started_at>=? AND started_at<=?
    """, (title_prefix + "%", start, end)).fetchall()
    total = 0.0; hops = 0
    for c in crons:
        msgs = cur.execute("""
            SELECT role, timestamp FROM messages
            WHERE session_id=? AND timestamp>=? AND timestamp<=? ORDER BY timestamp
        """, (c["id"], start, end)).fetchall()
        for i in range(len(msgs)-1):
            if msgs[i]["role"]=="user" and msgs[i+1]["role"]=="assistant":
                g = msgs[i+1]["timestamp"] - msgs[i]["timestamp"]
                if 0 < g <= HOP_CAP:
                    total += g / 3600.0; hops += 1
    con.close()
    return total, hops

def adora_windows(rows):
    """Merge her message timestamps (role=user, real content) into windows."""
    times = []
    for r in rows:
        c = r["content"] or ""
        if r["role"] != "user":
            continue
        if c.startswith("[IMPORTANT:"):
            continue
        times.append(r["timestamp"])
    times.sort()
    wins = []
    for t in times:
        if wins and t - wins[-1][1] <= GAP_MERGE:
            wins[-1][1] = t
        else:
            wins.append([t, t])
    return [(w[0], w[1]) for w in wins]

def narusya_processing(rows):
    """For each user→assistant hop, count the gap (her prompt to my reply)."""
    total = 0.0
    hops = 0
    for i in range(len(rows) - 1):
        if rows[i]["role"] == "user" and rows[i+1]["role"] == "assistant":
            gap = rows[i+1]["timestamp"] - rows[i]["timestamp"]
            if 0 < gap <= HOP_CAP:
                total += gap / 3600.0
                hops += 1
    return total, hops

def report_day(day):
    sids = workspace_sessions()
    if not sids:
        print(f"{day}: no workspace sessions found"); return (0,0)
    start, _ = day_bounds(day)
    end = start + 86400
    rows = load_day(day, sids)
    awin = adora_windows(rows)
    adora_h = sum((b-a)/3600.0 for a,b in awin)
    nar_h, hops = narusya_processing(rows)
    cron_h, cron_hops = cron_processing(start, end)
    nar_total = nar_h + cron_h
    print(f"\n📅 {day}")
    print(f"   👩 Adora:   {adora_h:.2f}h engaged ({len(awin)} window(s))")
    for a,b in awin:
        print(f"      {ts_local(a).strftime('%H:%M')} → {ts_local(b).strftime('%H:%M')}   {(b-a)/3600:.2f}h")
    print(f"   🐍 Narusya: {nar_total:.2f}h total  (interactive {nar_h:.2f}h · {hops} hops | cron {cron_h:.3f}h · {cron_hops})")
    return adora_h, nar_total

def main():
    args = sys.argv[1:]
    cmd = args[0] if args else "today"
    now = datetime.datetime.now()
    if cmd == "today":
        a, n = report_day(now.strftime("%Y-%m-%d"))
        print(f"\n📊 TODAY: Adora {a:.2f}h · Narusya {n:.2f}h")
    elif cmd == "week":
        con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
        cur = con.cursor()
        sids = workspace_sessions()
        ph = ",".join("?" * len(sids))
        rows = cur.execute(f"SELECT DISTINCT timestamp FROM messages WHERE session_id IN ({ph})",
                           (*sids,)).fetchall()
        con.close()
        days = {ts_local(r[0]).strftime("%Y-%m-%d") for r in rows}
        monday = (now - datetime.timedelta(days=now.weekday())).strftime("%Y-%m-%d")
        ta = tn = 0.0
        for day in sorted(days):
            if day >= monday:
                a, n = report_day(day)
                ta += a; tn += n
        print(f"\n📊 WEEK: Adora {ta:.2f}h · Narusya {tn:.2f}h")
    elif cmd == "all":
        con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
        cur = con.cursor()
        sids = workspace_sessions()
        ph = ",".join("?" * len(sids))
        rows = cur.execute(f"SELECT DISTINCT timestamp FROM messages WHERE session_id IN ({ph})",
                           (*sids,)).fetchall()
        con.close()
        days = {ts_local(r[0]).strftime("%Y-%m-%d") for r in rows}
        ta = tn = 0.0
        for day in sorted(days):
            a, n = report_day(day)
            ta += a; tn += n
        print(f"\n📊 FULL HISTORY: Adora {ta:.2f}h · Narusya {tn:.2f}h across {len(days)} days")
    elif len(cmd) == 10 and cmd.count("-") == 2:
        a, n = report_day(cmd)
        print(f"\n📊 {cmd}: Adora {a:.2f}h · Narusya {n:.2f}h")
    else:
        print(__doc__)

if __name__ == "__main__":
    main()