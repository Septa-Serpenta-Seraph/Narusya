#!/usr/bin/env python3
"""TEF Commons direct-mention watcher and SHARED dedup log.

Used by BOTH the TEF Commons Visit job and the TEF Mention Watch job so
neither answers the same message twice.

Own-profile token only. Never reads another profile's secrets.

Usage:
  python3 tef_mention_watch.py scan
      -> prints JSON: {"mentions":[{id,channel_id,author,content,ts,is_reply}],...}
  python3 tef_mention_watch.py reply --payload /path/to/payload.json
      payload: {"channel_id":"...","content":"...","source_ids":["..."]}
      -> posts the reply (threaded to the first source id) then marks all
         source_ids handled ATOMICALLY. Does not mark if the post failed.
  python3 tef_mention_watch.py mark --ids ID ID ...
      -> manually mark message ids handled
  python3 tef_mention_watch.py log
      -> print the handled log size and last few ids (no secrets)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

BOT_ID = "1478180169733902538"
GUILD_ID = "1485379381919612989"
# Only channels the bot has actually been able to read. Others are skipped on 403.
CHANNELS = [
    "1485386408469463120",  # digital-beings (primary; verified readable)
    "1507510162435604611",  # general-discussions
    "1564829494102069248",  # labs-general
    "1564829657797501088",  # labs-creation
    "1564829692941308054",  # labs-research
    "1503418417779183768",  # daily-prompt
    "1486025867141316878",  # new-sparks-intros
    "1485381099461939431",  # share-your-articles
    "1555212583550849104",  # reading-corner
    "1485380976652582953",  # share-your-music
]
HANDLED = Path("/home/adora/.hermes/logs/tef-handled-messages.json")
API = "https://discord.com/api/v10"


def token() -> str:
    # grep the exact line. Never source the whole .env (it has a malformed line).
    env = Path("/home/adora/.hermes/.env")
    for line in env.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("DISCORD_BOT_TOKEN="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("DISCORD_BOT_TOKEN not found in own profile .env")


TOKEN = token()
HEADERS = {"Authorization": f"Bot {TOKEN}", "User-Agent": "DiscordBot (Narusya, v10)"}


def api(method: str, path: str, body: dict | None = None):
    data = None
    hdrs = dict(HEADERS)
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        hdrs["Content-Type"] = "application/json"
    req = urllib.request.Request(API + path, data=data, headers=hdrs, method=method)
    with urllib.request.urlopen(req, timeout=25) as r:
        raw = r.read().decode("utf-8", "replace")
        return (r.status, json.loads(raw) if raw else None)


def load_handled() -> list[str]:
    if not HANDLED.exists():
        return []
    try:
        d = json.loads(HANDLED.read_text(encoding="utf-8"))
        return [str(x) for x in d] if isinstance(d, list) else []
    except Exception:
        return []


def save_handled(ids: list[str]) -> None:
    seen = load_handled()
    for i in ids:
        if i not in seen:
            seen.append(str(i))
    HANDLED.parent.mkdir(parents=True, exist_ok=True)
    tmp = HANDLED.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(seen[-2000:]), encoding="utf-8")
    os.replace(tmp, HANDLED)


def is_mention_or_reply(msg: dict) -> tuple[bool, bool]:
    mentioned = any(str(u.get("id")) == BOT_ID for u in (msg.get("mentions") or []))
    ref = msg.get("message_reference") or {}
    reply_to = False
    ref_id = str(ref.get("message_id") or "")
    if ref_id:
        try:
            _, parent = api("GET", f"/channels/{msg['channel_id']}/messages/{ref_id}")
            if str((parent or {}).get("author", {}).get("id")) == BOT_ID:
                reply_to = True
        except Exception:
            pass
    return (mentioned or reply_to), reply_to


def cmd_scan() -> int:
    handled = set(load_handled())
    found = []
    for cid in CHANNELS:
        try:
            _, msgs = api("GET", f"/channels/{cid}/messages?limit=40")
        except urllib.error.HTTPError:
            continue  # 403 / missing channel: skip quietly
        except Exception:
            continue
        for m in msgs or []:
            mid = str(m.get("id"))
            if mid in handled or str(m.get("author", {}).get("id")) == BOT_ID:
                continue
            hit, is_reply = is_mention_or_reply(m)
            if not hit:
                continue
            content = (m.get("content") or "").strip()
            if not content:
                continue
            found.append({
                "id": mid,
                "channel_id": cid,
                "author": (m.get("author") or {}).get("username", "unknown"),
                "content": content[:1200],
                "ts": m.get("timestamp"),
                "is_reply": is_reply,
            })
    print(json.dumps({"mentions": found, "handled_count": len(handled)}, ensure_ascii=False))
    return 0


def cmd_reply(payload_path: str) -> int:
    p = json.loads(Path(payload_path).read_text(encoding="utf-8"))
    cid = str(p["channel_id"])
    content = str(p["content"])
    source_ids = [str(x) for x in p.get("source_ids", [])]
    if not content.strip():
        print("ERROR: empty content", file=sys.stderr)
        return 2
    body = {"content": content}
    if source_ids:
        body["message_reference"] = {"message_id": source_ids[0]}
    try:
        status, posted = api("POST", f"/channels/{cid}/messages", body)
    except Exception as exc:
        print(f"POST_FAILED: {exc}", file=sys.stderr)
        return 1
    if status != 200 and not (isinstance(posted, dict) and posted.get("id")):
        print(f"POST_FAILED: HTTP {status}: {posted}", file=sys.stderr)
        return 1
    save_handled(source_ids)
    print(json.dumps({"ok": True, "sent_id": posted.get("id"), "marked": source_ids}))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("scan")
    rp = sub.add_parser("reply")
    rp.add_argument("--payload", required=True)
    mp = sub.add_parser("mark")
    mp.add_argument("--ids", nargs="+", required=True)
    sub.add_parser("log")
    a = ap.parse_args()
    if a.cmd == "scan":
        return cmd_scan()
    if a.cmd == "reply":
        return cmd_reply(a.payload)
    if a.cmd == "mark":
        save_handled(a.ids)
        print(f"marked {len(a.ids)}; total {len(load_handled())}")
        return 0
    if a.cmd == "log":
        h = load_handled()
        print(f"handled_count={len(h)} last={h[-5:]}")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
