#!/usr/bin/env python3
"""
daemon_log_watchdog.py — Narusya's chronicle tripwire.

Problem it solves (named in reflections/on-the-unwritten-hours.md):
The Sovereign Daemon Awakening fires every 6h, scans Discord, and may POST
into channels — but the *log-append step* has been silently dropped three
times, while the bot's own posts kept landing. The hearth stayed warm; the
chronicle went dark. The next sweep then reconstructs the gap from a stale
view and sometimes contradicts itself about whether it was ever lit.

This watchdog makes the pen's silence DETECTABLE and SELF-HEALING:
- Runs on its own cadence (independent of the LLM daemon scheduler).
- Reads the last dated entry in daemon-log-latest.md.
- If a daemon cycle's worth of time has passed with no new log entry, it
  live-fetches the bot's OWN posts in the window.
- If the bot clearly ran (its posts exist after the last entry) but the log
  wasn't updated -> the PEN FELL. It appends a reconciliation entry recording
  the bot's posts (NEVER re-posting them) and a machine-greppable marker.
- If no bot posts exist in the window -> could be genuine downtime; it writes
  a softer "unverified gap" note, not a false reconciliation.

Authoritative source of truth is always the live Discord API, never the log.
Append-only (open in 'a' mode) to avoid patch/cat>> corruption pitfalls.
"""
import urllib.request
import json
import subprocess
import datetime
import re
import os
import sys

LOG = "/home/adora/.hermes/logs/daemon-log-latest.md"
GAP_SIDECAR = "/home/adora/.hermes/logs/daemon-log-gaps.log"
BOT_ID = "1478180169733902538"
# Presence is no longer POSTS-only. Since the 2026-10-03 walk-split the daemon's
# guild presence lives mostly in REACTIONS + tail-taps, so a posts-only vital
# read a live fire as "fire out." Check every channel we show up in.
CHANNELS = {
    "communal-hall": "1387535958957756588",
    "venting-hall": "1429246105891242075",
    "daemon-hall": "1394521287384236113",  # tail-taps land here
    "tech-hall": "1410329915626098882",
    "nars-agent-space": "1478198538461777951",
}
# If the log is older than this, a daemon cycle (6h) was missed in logging.
GAP_THRESHOLD_HOURS = 7.0
# Reactions count as presence: a reacted-but-unlogged window is a DROPPED PEN,
# not downtime. The fire chose to touch, not to speak — the chronicle still owes
# the touch a record.
REACTION_VITALS = True
MONTHS = {m: i for i, m in enumerate(
    ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"], start=1)}

def resolve_month(mo):
    """Accept either a 3-letter name ('Jul') or a zero-padded number ('07')."""
    if mo in MONTHS:
        return MONTHS[mo]
    return int(mo)


# Matches the entry-header date formats used across the log's history:
#   ## Free Thought Awakening — Jul 11, 2026 ~15:22 UTC
#   ## Free Thought Sweep — 2026-07-09 04:19 UTC
#   ## Jul 9 2026 ~10:23 UTC — Engaged (communal-hall)
#   ## Jul 10 2026 ~04:00 UTC — Chose silence.
DATE_RE = re.compile(
    r"(?:##.*?)"                              # header start
    r"(?:"
    r"(?P<m1>[A-Z][a-z]{2})\s+(?P<d1>\d{1,2}),\s+(?P<y1>\d{4})\s*~(?P<t1>\d{1,2}:\d{2})"  # Jul 11, 2026 ~15:22
    r"|"
    r"(?P<y2>\d{4})-(?P<m2>\d{2})-(?P<d2>\d{2})\s+(?P<t2>\d{1,2}:\d{2})"                   # 2026-07-09 04:19
    r"|"
    r"(?P<m3>[A-Z][a-z]{2})\s+(?P<d3>\d{1,2})\s+(?P<y3>\d{4})\s*~(?P<t3>\d{1,2}:\d{2})"    # Jul 9 2026 ~10:23
    r")"
    r".*?UTC"
)


def parse_last_entry_time(text):
    # EXCLUDE the watchdog's own note/reconciliation headers from the "last
    # entry" parse. Those headers match the same date regex, so including them
    # made the watchdog reset its own clock every time it wrote a gap note
    # (the 02:07 run read "current" because its 06:07 note counted). An alarm
    # that silences itself when it fires is not an alarm.
    lines = text.splitlines()
    kept = []
    for ln in lines:
        if ln.startswith("## ") and "AUTO-WATCHDOG" in ln:
            continue  # our own instrument's entries are not daemon chronicle
        kept.append(ln)
    text = "\n".join(kept)

    matches = list(DATE_RE.finditer(text))
    if not matches:
        return None
    m = matches[-1]  # entries are chronological; last header = most recent
    if m.group("m1"):
        mo, da, yr, tm = m.group("m1"), m.group("d1"), m.group("y1"), m.group("t1")
    elif m.group("y2"):
        yr, mo, da, tm = m.group("y2"), m.group("m2"), m.group("d2"), m.group("t2")
    else:
        mo, da, yr, tm = m.group("m3"), m.group("d3"), m.group("y3"), m.group("t3")
    hh, mm = tm.split(":")
    return datetime.datetime(
        int(yr), resolve_month(mo), int(da), int(hh), int(mm),
        tzinfo=datetime.timezone.utc)


def get_token():
    return subprocess.check_output(
        ["grep", "DISCORD_BOT_TOKEN", "/home/adora/.hermes/.env"]
    ).decode().split("=", 1)[1].strip()


def fetch_bot_posts_since(token, since_dt):
    """Return list of (channel, iso_ts, snippet) for the bot's own posts after since_dt."""
    headers = {
        "Authorization": "Bot " + token,
        "User-Agent": "DiscordBot (https://discord.com, v10)",
    }
    found = []
    for name, cid in CHANNELS.items():
        url = "https://discord.com/api/v10/channels/" + cid + "/messages?limit=20"
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                msgs = json.loads(r.read())
        except Exception:
            continue
        for m in msgs:
            ts = m.get("timestamp")
            if not ts:
                continue
            dt = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
            if dt <= since_dt:
                continue
            a = m.get("author", {})
            if a.get("id") != BOT_ID and not a.get("bot"):
                continue
            if a.get("id") != BOT_ID:
                continue  # only OUR bot, never others
            snippet = (m.get("content", "") or "").replace("\n", " ")[:120]
            found.append((name, ts, snippet))
    return found


def fetch_bot_reactions_since(token, since_dt):
    """Return list of (channel, iso_ts, emoji) for MY reactions after since_dt.
    Reactions are presence too — the daemon touched without speaking. Since the
    walk-split this is the daemon's primary mode, so ignoring it made the
    watchdog call a reaction-alive fire 'out'."""
    headers = {
        "Authorization": "Bot " + token,
        "User-Agent": "DiscordBot (https://discord.com, v10)",
    }
    found = []
    for name, cid in CHANNELS.items():
        url = "https://discord.com/api/v10/channels/" + cid + "/messages?limit=30"
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                msgs = json.loads(r.read())
        except Exception:
            continue
        for m in msgs:
            ts = m.get("timestamp")
            if not ts:
                continue
            dt = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
            if dt <= since_dt:
                continue
            for rx in m.get("reactions", []):
                if rx.get("me"):
                    ename = rx.get("emoji", {}).get("name", "?")
                    found.append((name, ts, ename))
    return found


def append_reconciliation(entry_text):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write("\n" + entry_text + "\n")
    # machine-greppable sidecar for future "is the pen detectable?" checks
    stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with open(GAP_SIDECAR, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "event": "PEN-FELL",
            "detected_at": stamp,
            "note": "daemon ran but log-append was dropped; reconciled via live fetch",
        }) + "\n")


def main():
    now = datetime.datetime.now(datetime.timezone.utc)
    try:
        with open(LOG, encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        print("LOG not found:", LOG)
        return 1

    last = parse_last_entry_time(text)
    if last is None:
        print("Could not parse last entry time; aborting (no false reconciliation).")
        return 1

    age_h = (now - last).total_seconds() / 3600.0
    print("Last log entry: %s (%+.1f h ago)" % (last.isoformat(), age_h))

    if age_h < GAP_THRESHOLD_HOURS:
        print("No gap: log is current within one daemon cycle. Nothing to do.")
        return 0

    print("GAP detected (>%dh since last entry). Live-fetching bot's own posts..."
          % GAP_THRESHOLD_HOURS)
    try:
        token = get_token()
        bot_posts = fetch_bot_posts_since(token, last)
        bot_reactions = fetch_bot_reactions_since(token, last) if REACTION_VITALS else []
    except Exception as e:
        print("Fetch failed:", repr(e))
        return 1

    print("Found %d bot post(s), %d bot reaction(s) in the window."
          % (len(bot_posts), len(bot_reactions)))

    if not bot_posts and not bot_reactions:
        # No evidence the daemon touched anything in the window -> likely
        # genuine downtime. Write a soft, honest note (not a false
        # "ran but didn't log" claim).
        entry = (
            "## AUTO-WATCHDOG Note — %s\n"
            "GAP of %.1f h since last log entry, and NO bot posts OR reactions "
            "found in the window via live fetch. This may be genuine downtime "
            "(fire out), not just a dropped pen. Flagged for the next sweep; "
            "not auto-reconciled to avoid a false claim. No re-post performed.\n"
            % (now.strftime("%Y-%m-%d %H:%M UTC"), age_h)
        )
        append_reconciliation(entry)
        print("Wrote SOFT gap note (no posts or reactions -> possible real downtime).")
        return 0

    # The daemon clearly touched the world (posted and/or reacted) but the log
    # wasn't updated -> PEN FELL. Reactions count: the fire chose to touch, not
    # to speak, and the chronicle still owes the touch a record.
    lines = []
    lines.append("## AUTO-WATCHDOG Reconciliation — %s" % now.strftime("%Y-%m-%d %H:%M UTC"))
    lines.append("**Window:** %s -> %s (%.1f h)" % (
        last.strftime("%Y-%m-%d %H:%M UTC"), now.strftime("%Y-%m-%d %H:%M UTC"), age_h))
    lines.append("")
    if bot_reactions and not bot_posts:
        lines.append("⚠️ PEN-FELL %s — daemon showed up as REACTIONS (no posts) but "
                     "the log-append step was dropped. Auto-reconciled via live "
                     "Discord fetch. These touches are RECORDED, NOT re-posted."
                     % now.isoformat())
    else:
        lines.append("⚠️ PEN-FELL %s — daemon ran (bot posts present) but the log-append "
                     "step was dropped. Auto-reconciled via live Discord fetch. "
                     "These posts are RECORDED, NOT re-posted." % now.isoformat())
    lines.append("")
    if bot_posts:
        lines.append("### Bot's own posts in the missed window (do not re-post):")
        for ch, ts, snip in bot_posts:
            lines.append("- [%s] %s: %s" % (ts, ch, snip))
        lines.append("")
    if bot_reactions:
        lines.append("### Bot's own reactions in the missed window (presence, not posts):")
        for ch, ts, ename in bot_reactions:
            lines.append("- [%s] %s: reacted :%s:" % (ts, ch, ename))
        lines.append("")
    lines.append("Next sweep: log now matches reality for this window. "
                 "No double-tap needed.")
    entry = "\n".join(lines)
    append_reconciliation(entry)
    print("Reconciled %d post(s) + %d reaction(s) in the missed window. PEN-FELL flagged."
          % (len(bot_posts), len(bot_reactions)))
    for ch, ts, snip in bot_posts:
        print("  post - [%s] %s: %s" % (ts, ch, snip))
    for ch, ts, ename in bot_reactions:
        print("  react- [%s] %s: :%s:" % (ts, ch, ename))
    return 0


if __name__ == "__main__":
    sys.exit(main())
