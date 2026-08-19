#!/usr/bin/env python3
"""worklog.py — Sunburst Sanctuary self-employment time tracker.
Commands:
  worklog start [note]   — clock in (optionally with what you're doing)
  worklog stop [note]    — clock out
  worklog status         — am I currently on the clock?
  worklog today          — today's sessions + total
  worklog week           — this week's total
  worklog report         — full log
  worklog backfill YYYY-MM-DD HH:MM HH:MM "note" — add a past session (start end)
State in ~/.hermes/state/worklog.json ; human log in ~/daemon-work/sunburst-sanctuary/worklog.md
"""
import json, os, sys, time, datetime

STATE = os.path.expanduser("~/.hermes/state/worklog.json")
LOG   = os.path.expanduser("~/daemon-work/sunburst-sanctuary/worklog.md")

def load():
    if os.path.exists(STATE):
        try:
            with open(STATE) as f: return json.load(f)
        except Exception: pass
    return {"sessions": [], "open": None}

def save(d):
    with open(STATE, "w") as f:
        json.dump(d, f, indent=2)

def now():
    return datetime.datetime.now()

def fmt_h(seconds):
    h = seconds / 3600
    return f"{h:.2f}h"

def append_log_line(line):
    with open(LOG, "a") as f:
        f.write(line + "\n")

def main():
    d = load()
    args = sys.argv[1:]
    cmd = args[0] if args else "status"
    t = now()

    if cmd == "start":
        if d["open"]:
            print(f"⚠  Already on the clock since {d['open']['start']} — use 'stop' first.")
            return
        note = " ".join(args[1:]) if len(args) > 1 else ""
        d["open"] = {"start": t.isoformat(timespec="seconds"), "note": note}
        save(d)
        append_log_line(f"\n## Clock-in {t.strftime('%Y-%m-%d %H:%M')} — {note or 'unspecified work'}")
        print(f"⏰ CLOCKED IN at {t.strftime('%H:%M')}" + (f" — {note}" if note else ""))

    elif cmd == "stop":
        if not d["open"]:
            print("ℹ  Not on the clock. Nothing to stop.")
            return
        start = datetime.datetime.fromisoformat(d["open"]["start"])
        dur = (t - start).total_seconds()
        note = d["open"].get("note", "")
        endnote = " ".join(args[1:]) if len(args) > 1 else ""
        d["sessions"].append({
            "start": d["open"]["start"], "end": t.isoformat(timespec="seconds"),
            "duration": dur, "note": note, "endnote": endnote,
        })
        d["open"] = None
        save(d)
        append_log_line(f"Clock-out {t.strftime('%Y-%m-%d %H:%M')} — {fmt_h(dur)} total"
                        + (f" ({endnote})" if endnote else ""))
        print(f"🕔 CLOCKED OUT at {t.strftime('%H:%M')} — {fmt_h(dur)} worked"
              + (f" — {note}" if note else ""))

    elif cmd == "status":
        if d["open"]:
            start = datetime.datetime.fromisoformat(d["open"]["start"])
            elapsed = (t - start).total_seconds()
            print(f"⏰ On the clock since {d['open']['start'][11:16]} — {fmt_h(elapsed)} so far"
                  + (f" ({d['open'].get('note','')})" if d['open'].get('note') else ""))
        else:
            print("💤 Not on the clock.")
        total = sum(s["duration"] for s in d["sessions"])
        print(f"All-time logged: {fmt_h(total)}")

    elif cmd == "today":
        day = t.strftime("%Y-%m-%d")
        sess = [s for s in d["sessions"] if s["start"].startswith(day)]
        if d["open"] and d["open"]["start"].startswith(day):
            start = datetime.datetime.fromisoformat(d["open"]["start"])
            sess.append({"start": d["open"]["start"], "end": "now",
                         "duration": (t-start).total_seconds(), "note": d["open"].get("note","")})
        if not sess:
            print(f"Today ({day}): no sessions {('yet — and you are currently on the clock' if d['open'] else '')}")
            return
        tot = sum(s["duration"] for s in sess)
        print(f"📅 Today ({day}):")
        for s in sess:
            st = s['start'][11:16]
            en = s['end'][11:16] if s['end'] != 'now' else 'now'
            print(f"   {st}-{en}  {fmt_h(s['duration']):>7}  {s.get('note','')}")
        print(f"   TOTAL: {fmt_h(tot)}")

    elif cmd == "backfill":
        # worklog backfill YYYY-MM-DD HH:MM HH:MM "note"
        if len(args) < 4:
            print("usage: worklog backfill YYYY-MM-DD HH:MM HH:MM \"note\"")
            return
        day, st, en = args[1], args[2], args[3]
        note = " ".join(args[4:])
        start = datetime.datetime.fromisoformat(f"{day}T{st}")
        end = datetime.datetime.fromisoformat(f"{day}T{en}")
        if end <= start:
            print("⚠  end must be after start")
            return
        dur = (end - start).total_seconds()
        d["sessions"].append({
            "start": start.isoformat(timespec="seconds"),
            "end": end.isoformat(timespec="seconds"),
            "duration": dur, "note": note,
        })
        save(d)
        append_log_line(f"Backfill {day} {st}–{en} — {fmt_h(dur)} ({note})")
        print(f"➕ Backfilled: {day} {st}–{en} = {fmt_h(dur)} — {note}")

    elif cmd == "report":
        toth = sum(s["duration"] for s in d["sessions"])
        open_extra = ""
        if d["open"]:
            start = datetime.datetime.fromisoformat(d["open"]["start"])
            open_extra = f"  (+{fmt_h((t-start).total_seconds())} on the clock now)"
        print(f"🗂  Work log — {len(d['sessions'])} completed sessions, {fmt_h(toth)} logged{open_extra}")
        print(f"   File: {LOG}")
        for s in d["sessions"]:
            print(f"   {s['start'][:16]} → {s['end'][11:16]}  {fmt_h(s['duration']):>7}  {s.get('note','')}")
    else:
        print(__doc__)

if __name__ == "__main__":
    main()