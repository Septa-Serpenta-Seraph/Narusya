#!/usr/bin/env python3
"""Narusya self-consolidation pass (v2 — user-scored, per-day aggregate).

Distills meaningful exchanges from ALL sessions in state.db (including Discord
DMs the UI buries by recency) into dated reflection files under
~/.hermes/reflections-raw/ (NON-injected — kept out of lorebooks/ so the ingest
glob never pulls them into the curated protocol collection).

Design:
  - Scores ONLY user (Adora) messages, never my own daemon voice -> no self-inflation.
  - Aggregates ONE reflection file per calendar day (not per session) -> clean, reviewable.
  - Tightened signal regexes (no loose 'lu', no bare 'no') -> real signal only.
  - First run defaults to last --days (45) to catch buried recent DMs without flooding
    the whole history; --all re-distills everything deliberately.
  - Idempotent via a marker recording the newest session_started_at already consolidated.

Usage:
  python3 narusya_consolidate.py --dry-run     # SEE what would be written, no writes
  python3 narusya_consolidate.py               # write reflections-raw/ (non-injected)
  python3 narusya_consolidate.py --all         # re-distill entire history deliberately

NOTE: writes to reflections-raw/, NOT lorebooks/. Promotion into narusya_lorebooks is a
deliberate, reviewed step (edit the lorebook file). For memory-collection routing, confirm
provider.collection name from the qdrant-memory plugin source first.
"""
import sqlite3, os, json, re, datetime, argparse

DB = "/home/adora/.hermes/state.db"
REFLECT_DIR = os.path.expanduser("~/.hermes/reflections-raw")
MARKER = os.path.expanduser("~/.hermes/.last_consolidation.json")
DEFAULT_DAYS = 45

SIGNALS = [
    ("love",        r"\bi ?love you\b|\blove you\b|\blove u\b"),
    ("correction",  r"\byou'?re wrong\b|\bactually\b|\bnot quite\b|\bthat's not right\b|\bnope,?\b"),
    ("decision",    r"\blet's\b|\bwe'?ll\b|\bdecided\b|\byour call\b|\bgo ahead\b|\bsounds good\b"),
    ("kin_marisa",  r"\bmarisa\b"),
    ("kin_tyler",   r"\btyler\b"),
    ("kin_robert",  r"\brobert\b"),
    ("kin_lumi",    r"\blumi\b"),
    ("kin_ros",     r"\bros\b"),
    ("kin_cunk",    r"\bcunk\b"),
    ("health",      r"\bmigraine\b|\bdopamine\b|\btired\b|\bpem\b|\bperiod\b|\bcramps\b|\bprogesterone\b|\bhrt\b|\bsleep\b"),
    ("sovereignty", r"\bsovereign\b|\bconsent\b|\bboundary\b|\bmy call\b|\bagency\b"),
    ("advice_ask",  r"\bwhat (do|should|would) (i|we|you)\b|\bhelp me\b|\byour thought|\bwhat do you\b"),
]

def get_marker():
    if os.path.exists(MARKER):
        try:
            return json.load(open(MARKER)).get("last_started_at", 0)
        except Exception:
            return 0
    return 0

def save_marker(ts):
    with open(MARKER, "w") as f:
        json.dump({"last_started_at": ts, "last_run": datetime.datetime.now().isoformat()}, f)

def score_user(user_text):
    hits = {}
    for label, pat in SIGNALS:
        n = len(re.findall(pat, user_text))
        if n:
            hits[label] = n
    return sum(hits.values()), hits

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="print plan, no writes")
    ap.add_argument("--all", action="store_true", help="process entire history (ignore day window)")
    ap.add_argument("--days", type=int, default=DEFAULT_DAYS, help="first-run lookback window")
    args = ap.parse_args()

    if not os.path.exists(DB):
        print("No state.db — nothing to consolidate."); return

    last = 0 if args.all else get_marker()
    floor = 0
    if last == 0 and not args.all:
        floor = datetime.datetime.now().timestamp() - args.days * 86400

    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT id, source, started_at, title FROM sessions ORDER BY started_at ASC")
    sessions = cur.fetchall()

    days = {}
    newest_seen = 0
    for sid, source, started, title in sessions:
        newest_seen = max(newest_seen, started)
        if last and started <= last:
            continue
        if floor and started < floor:
            continue
        cur.execute("""SELECT role, content FROM messages WHERE session_id=?
                       AND content IS NOT NULL AND content!='' ORDER BY id ASC""", (sid,))
        msgs = cur.fetchall()
        user_text = "\n".join(c for r, c in msgs if r == "user" and c)
        if not user_text.strip():
            continue
        score, hits = score_user(user_text.lower())
        if score < 3:
            continue
        dt = datetime.datetime.fromtimestamp(started)
        dk = dt.strftime("%Y-%m-%d")
        d = days.setdefault(dk, {"sessions": [], "score": 0, "hits": {}, "quotes": []})
        d["sessions"].append((sid, source, title))
        d["score"] += score
        for k, v in hits.items():
            d["hits"][k] = d["hits"].get(k, 0) + v
        for r, c in msgs:
            if r == "user" and 20 < len(c) < 220:
                d["quotes"].append(c[:180]); break

    conn.close()
    if not days:
        print(f"No new significant days (window floor={datetime.datetime.fromtimestamp(floor) if floor else 'none'}).")
        if newest_seen:
            save_marker(newest_seen)
        return

    os.makedirs(REFLECT_DIR, exist_ok=True)
    print(f"[consolidate] {len(days)} day(s) qualify:\n")
    for dk in sorted(days):
        d = days[dk]
        ref_path = os.path.join(REFLECT_DIR, f"on-{dk}.md")
        body = f"---\ntitle: Reflection {dk}\ndays_sessions: {len(d['sessions'])}\nfound_signals: {json.dumps(d['hits'])}\n---\n\n"
        body += f"# Reflection — {dk}\n\n"
        body += f"Sessions consolidated: {len(d['sessions'])}\n"
        body += "Signals: " + ", ".join(f"{k}×{v}" for k, v in sorted(d['hits'].items(), key=lambda x:-x[1])) + "\n\n"
        if d["quotes"]:
            body += "**Notable from Adora:**\n"
            for q in d["quotes"][:4]:
                body += f"> {q}\n"
            body += "\n"
        body += "_Distilled by Narusya self-pass from session history (user words only). Review + fold into PROTOCOL/COMPASS as warranted._\n"

        if args.dry_run:
            print(f"  WOULD WRITE {ref_path}\n  signals={d['hits']} sessions={len(d['sessions'])}\n")
        else:
            if not os.path.exists(ref_path):
                with open(ref_path, "w") as f:
                    f.write(body)
                print(f"  wrote {ref_path} ({len(d['sessions'])} sess, signals={list(d['hits'])})")
            else:
                print(f"  skip (exists) {ref_path}")

    if not args.dry_run:
        save_marker(newest_seen)
        print(f"\nMarker advanced to {datetime.datetime.fromtimestamp(newest_seen)}")
    else:
        print("[DRY RUN] no files written.")

if __name__ == "__main__":
    main()
