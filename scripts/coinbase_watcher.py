#!/usr/bin/env python3
"""coinbase_watcher.py — silently watches the sunburst inbox for Coinbase and
Mastodon verdicts. Prints NOTHING unless new relevant mail arrives (cron
delivers stdout verbatim, so silence = no ping). State in ~/.hermes/state/."""
import json, os, re, subprocess, sys, time

STATE = os.path.expanduser("~/.hermes/state/coinbase_watcher.json")
INTEREST = re.compile(r"coinbase|mastodon|mstdn|approved|application|verif", re.I)
SKIP = re.compile(r"verification code|otp|sign.?in|welcome", re.I)  # no pings for OTP codes/welcome spam

state = {"last_seen": 0}
if os.path.exists(STATE):
    try:
        with open(STATE) as f:
            state = json.load(f)
    except Exception:
        pass

# list envelopes, table format (proven): ┌──┬──┬SUBJECT──┬FROM──┬DATE──┬SIZE──┐
try:
    out = subprocess.run(
        ["himalaya", "envelope", "list", "--account", "sunburst", "--page-size", "15"],
        capture_output=True, text=True, timeout=45,
    ).stdout
except Exception as e:
    sys.exit(0)  # silent on failure; next tick retries

rows = []
for line in out.splitlines():
    m = re.match(r"│\s*(\d+)\s*┆", line)
    if m:
        # pull subject from the 3rd column-ish region
        subj = re.search(r"┆\s*([^┆]+?)\s*┆", line)
        subject = subj.group(1).strip() if subj else ""
        rows.append((int(m.group(1)), subject))

if not rows:
    sys.exit(0)

max_id = max(r[0] for r in rows)
new = [r for r in rows if r[0] > state.get("last_seen", 0)]

# prime: first run just records the baseline, no ping
if not state.get("initialized"):
    state.update({"last_seen": max_id, "initialized": True, "updated": int(time.time())})
    with open(STATE, "w") as f:
        json.dump(state, f)
    sys.exit(0)

interesting = [r for r in new if INTEREST.search(r[1]) and not SKIP.search(r[1])]

if interesting:
    lines = ["📬 New mail worth pinging you about:\n"]
    for eid, subj in sorted(interesting):
        lines.append(f"- **{subj}**  (message {eid})")
    print("\n".join(lines))

state.update({"last_seen": max_id, "updated": int(time.time())})
with open(STATE, "w") as f:
    json.dump(state, f)
sys.exit(0)