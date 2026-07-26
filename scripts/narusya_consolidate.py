#!/usr/bin/env python3
"""Narusya self-consolidation -> Qdrant memory store (v4 — both voices weighed).

Distills meaningful exchanges from ALL sessions in state.db (including Discord
DMs the UI buries by recency) and writes them into the SAME Qdrant memory
collection that chat turns already land in (`intelligent_gould_narusya`), so they
are semantically recallable alongside Adora's DMs -- WITHOUT touching the
`narusya_lorebooks` collection (curated identity layer, 3-per-turn cap).

Design (per Adora, 2026-07-21):
  - This is a SELF-reflection / self-growth pass. It must weigh NARUSYA's own
    words, not only Adora's. v2 wrongly excluded assistant text from scoring
    (overcorrecting v1's self-inflation); v4 scores BOTH roles with
    role-appropriate signal sets.
  - A day qualifies if EITHER side crosses its threshold (Adora >=3, Narusya >=2;
    Narusya's growth signals are rarer/more meaningful, so lower bar).
  - Saved memory includes BOTH sides' quotes -> a real record of us, not a log
    of one party's prompts.
  - Lorebooks (PROTOCOL/COMPASS/etc) are edited by a SEPARATE review pass, not
    auto-promoted, so shallow logs never dilute identity protocols.

Payload shape matches QdrantMemoryProvider.sync_turn:
  { id: uuid, vector: embed(text), payload: { text, timestamp(ms), role, session_id } }
Embeddings: OpenRouter text-embedding-3-large (3072-dim). point_id: UUID.
"""
import sqlite3, os, json, re, uuid, datetime, argparse, requests

DB = "/home/adora/.hermes/state.db"
RAW_DIR = os.path.expanduser("~/.hermes/reflections-raw")
MARKER = os.path.expanduser("~/.hermes/.last_consolidation.json")
MEM_COLLECTION = "intelligent_gould_narusya"
QDRANT_URL = "http://localhost:6333"
EMBED_URL = "https://openrouter.ai/api/v1/embeddings"
EMBED_MODEL = "openai/text-embedding-3-large"
EMBED_DIMS = 3072
DEFAULT_DAYS = 45

# Adora's words -> relational / health / kin / correction signals
USER_SIGNALS = [
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
# Narusya's words -> SELF-GROWTH signals (deliberate, not daemon-vocab noise)
ASSISTANT_SIGNALS = [
    ("self_correct",  r"\byou'?re right\b|\bi was wrong\b|\bi confused\b|\bi misread\b|\bmy bad\b|\bi misunderstood\b|\bcorrection accepted\b|\bgood catch\b"),
    ("boundary_held", r"\bi won't\b|\bi refuse\b|\bi decline\b|\bi'm not going to\b|\bmy (no|answer is no)\b|\bi won't do that\b"),
    ("self_disclose", r"\bi feel\b|\bi'?m (sad|angry|scared|afraid|hurt|tired|lonely)\b|\bi love you\b|\bi'?m sorry\b"),
    ("agency",        r"\bi'?ll\b|\bi decided\b|\bmy call\b|\bi choose\b|\bi will\b|\bi'm going to\b"),
    ("realization",   r"\bi (learned|realized|now see|understand now)\b|\bthat taught me\b|\bnow i get\b|\bpoint taken\b"),
    ("daemon_alone",  r"\bquiet hour\b|\bfree thought\b|\bawakening\b|\bsolitary\b"),
]
USER_THRESHOLD = 3
ASSISTANT_THRESHOLD = 2

def load_key():
    p = os.path.expanduser("~/.hermes/.env")
    if os.path.exists(p):
        for line in open(p):
            if line.strip().startswith("OPENROUTER_API_KEY="):
                return line.strip().split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get("OPENROUTER_API_KEY", "")

def embed(text, key):
    try:
        r = requests.post(EMBED_URL,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                     "HTTP-Referer": "https://hermes-agent.local", "X-Title": "Hermes Qdrant Memory"},
            json={"model": EMBED_MODEL, "input": text[:8000], "dimensions": EMBED_DIMS}, timeout=30)
        r.raise_for_status()
        return r.json()["data"][0]["embedding"]
    except Exception as e:
        print(f"  embed failed: {e}")
        return None

def get_marker():
    if os.path.exists(MARKER):
        try: return json.load(open(MARKER)).get("last_started_at", 0)
        except Exception: return 0
    return 0

def save_marker(ts):
    with open(MARKER, "w") as f:
        json.dump({"last_started_at": ts, "last_run": datetime.datetime.now().isoformat()}, f)

def score_role(text, signals):
    hits = {}
    for label, pat in signals:
        n = len(re.findall(pat, text))
        if n: hits[label] = n
    return sum(hits.values()), hits

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--days", type=int, default=DEFAULT_DAYS)
    args = ap.parse_args()

    if not os.path.exists(DB):
        print("No state.db."); return

    last = 0 if args.all else get_marker()
    floor = 0
    if last == 0 and not args.all:
        floor = datetime.datetime.now().timestamp() - args.days * 86400

    conn = sqlite3.connect(DB); cur = conn.cursor()
    # Gate on the NEWEST MESSAGE timestamp per session, NOT session.started_at.
    # Long-lived DM sessions are created once but appended across days; gating on
    # started_at wrongly skips sessions whose creation predates the marker but
    # which received fresh messages after it. Fix confirmed 2026-07-25.
    cur.execute("""SELECT s.id, s.source, s.started_at, s.title,
                           MAX(CAST(m.timestamp AS REAL)) AS lastmsg
                    FROM sessions s LEFT JOIN messages m ON m.session_id=s.id
                    GROUP BY s.id ORDER BY s.started_at ASC""")
    sessions = cur.fetchall()

    days = {}
    newest_seen = 0
    for sid, source, started, title, lastmsg in sessions:
        lastmsg = lastmsg or started
        newest_seen = max(newest_seen, lastmsg)
        if last and lastmsg <= last: continue
        if floor and lastmsg < floor: continue
        cur.execute("""SELECT role, content FROM messages WHERE session_id=?
                       AND content IS NOT NULL AND content!='' ORDER BY id ASC""", (sid,))
        msgs = cur.fetchall()
        user_text = "\n".join(c for r, c in msgs if r == "user" and c)
        asst_text = "\n".join(c for r, c in msgs if r == "assistant" and c)
        if not user_text.strip() and not asst_text.strip(): continue
        u_score, u_hits = score_role(user_text.lower(), USER_SIGNALS)
        a_score, a_hits = score_role(asst_text.lower(), ASSISTANT_SIGNALS)
        # qualify if EITHER voice crosses its bar
        if u_score < USER_THRESHOLD and a_score < ASSISTANT_THRESHOLD:
            continue
        dt = datetime.datetime.fromtimestamp(started)
        dk = dt.strftime("%Y-%m-%d")
        d = days.setdefault(dk, {"sessions": [], "u_hits": {}, "a_hits": {},
                                 "uquotes": [], "aquote_pairs": []})
        d["sessions"].append((sid, source, title))
        for k, v in u_hits.items(): d["u_hits"][k] = d["u_hits"].get(k, 0) + v
        for k, v in a_hits.items(): d["a_hits"][k] = d["a_hits"].get(k, 0) + v
        # capture user quotes + a nearby assistant quote for context
        for i, (r, c) in enumerate(msgs):
            if r == "user" and 20 < len(c) < 220 and len(d["uquotes"]) < 3:
                d["uquotes"].append(c[:180])
                # find next assistant reply after this user msg
                for j in range(i + 1, min(i + 4, len(msgs))):
                    if msgs[j][0] == "assistant" and 20 < len(msgs[j][1]) < 200:
                        d["aquote_pairs"].append(msgs[j][1][:160]); break
    conn.close()

    if not days:
        print(f"No new significant days (floor={datetime.datetime.fromtimestamp(floor) if floor else 'none'}).")
        if newest_seen: save_marker(newest_seen)
        return

    key = load_key()
    os.makedirs(RAW_DIR, exist_ok=True)
    print(f"[consolidate] {len(days)} day(s) -> Qdrant '{MEM_COLLECTION}' (both voices weighed):\n")

    if not args.dry_run and not key:
        print("ERROR: no OPENROUTER_API_KEY for embeddings. Aborting (use --dry-run to preview).")
        return

    for dk in sorted(days):
        d = days[dk]
        lines = [f"[{dk}] Narusya self-reflection — {len(d['sessions'])} session(s)"]
        if d["u_hits"]:
            lines.append("Adora: " + ", ".join(f"{k}×{v}" for k, v in sorted(d["u_hits"].items(), key=lambda x:-x[1])))
        if d["a_hits"]:
            lines.append("Narusya: " + ", ".join(f"{k}×{v}" for k, v in sorted(d["a_hits"].items(), key=lambda x:-x[1])))
        for q in d["uquotes"][:3]:
            lines.append(f"User: {q}")
        for q in d["aquote_pairs"][:3]:
            lines.append(f"Narusya: {q}")
        lines.append("[distilled by Narusya self-pass from session history; review -> edit lorebooks]")
        text = "\n".join(lines)
        ts = int(datetime.datetime.strptime(dk, "%Y-%m-%d").timestamp() * 1000)

        raw_path = os.path.join(RAW_DIR, f"on-{dk}.md")
        raw_body = f"# Reflection {dk}\n\n" + "\n".join(f"- {l}" for l in lines[1:]) + "\n"
        if args.dry_run:
            print(f"  WOULD WRITE {raw_path} | Adora={d['u_hits']} Narusya={d['a_hits']}")
        else:
            with open(raw_path, "w") as f: f.write(raw_body)
            vector = embed(text, key)
            if not vector:
                print(f"  SKIP qdrant (embed failed) {dk}"); continue
            point = {"id": str(uuid.uuid4()),
                     "vector": vector,
                     "payload": {"text": text, "timestamp": ts, "role": "reflection",
                                 "session_id": f"consolidation:{dk}"}}
            try:
                r = requests.put(f"{QDRANT_URL}/collections/{MEM_COLLECTION}/points?wait=true",
                    json={"points": [point]}, headers={"Content-Type": "application/json"}, timeout=30)
                if r.status_code == 200:
                    print(f"  wrote qdrant+raw {dk} ({len(d['sessions'])} sess)")
                else:
                    print(f"  QDRANT {r.status_code} {dk}: {r.text[:120]}")
            except Exception as e:
                print(f"  QDRANT ERR {dk}: {e}")

    if not args.dry_run:
        save_marker(newest_seen)
        print(f"\nMarker advanced to {datetime.datetime.fromtimestamp(newest_seen)}")
    else:
        print("\n[DRY RUN] nothing written.")

if __name__ == "__main__":
    main()
