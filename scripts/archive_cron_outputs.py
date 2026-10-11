#!/usr/bin/env python3
"""Snapshot cron outputs + session request dumps into the archive BEFORE the
disk watchdog's cleanup deletes them.

Why: the watchdog's cleanup paths (old cron outputs, old request dumps) are
'designated deletable' but were never verified as archived first. This script
runs daily, copies everything the watchdog is allowed to delete into a
retention-windowed snapshot dir, and lets the cleanup proceed safely.

Skips empty/silent-run files (155-byte 'Status: silent' markers) so the
snapshot stays small — only real outputs cost space.
"""

import os
import shutil
import datetime
import json

CRON_OUTPUT_DIR = os.path.expanduser("~/.hermes/cron/output")
SESSION_DUMP_GLOB_PREFIX = "request_dump_cron_"
SESSIONS_DIR = os.path.expanduser("~/.hermes/sessions")
ARCHIVE_ROOT = os.path.expanduser("~/Desktop/Narusya-Archive")
# The session archive (archive_daily.py) writes to /mnt/data/Narusya-Archive —
# the healthy drive. Cron-output snapshots must land there too, or they sit on
# the sick root drive where the watchdog is fighting for space.
DATA_ARCHIVE = "/mnt/data/Narusya-Archive"
if os.path.isdir(DATA_ARCHIVE):
    ARCHIVE_ROOT = DATA_ARCHIVE
SNAPSHOT_DIR = os.path.join(ARCHIVE_ROOT, "cron_output_snapshots")
STATE_FILE = os.path.join(SNAPSHOT_DIR, ".last_snapshot.json")
KEEP_DAYS = 30  # snapshots older than this are pruned; watchdog deletes originals older than 3-7 days
SILENT_MARKER_BYTES = 200  # files at or under this size are empty-run markers


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}


def save_state(state):
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def is_meaningful(path):
    """Skip empty/silent-run markers so the snapshot only stores real outputs."""
    try:
        return os.path.getsize(path) > SILENT_MARKER_BYTES
    except OSError:
        return False


def main():
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    state = load_state()
    now = datetime.datetime.now()
    snap_name = now.strftime("%Y-%m-%d_%H%M")
    snap_dir = os.path.join(SNAPSHOT_DIR, snap_name)

    copied, skipped_empty, skipped_unchanged, errors = 0, 0, 0, 0

    for src_root, prefix_filter in (
        (CRON_OUTPUT_DIR, None),
        (SESSIONS_DIR, SESSION_DUMP_GLOB_PREFIX),
    ):
        if not os.path.isdir(src_root):
            continue
        for dirpath, _dirnames, filenames in os.walk(src_root):
            for fn in filenames:
                if prefix_filter and not fn.startswith(prefix_filter):
                    continue
                if not prefix_filter and fn.startswith(SESSION_DUMP_GLOB_PREFIX):
                    continue  # cron output walk: skip the session dumps (handled below)
                src = os.path.join(dirpath, fn)
                if not is_meaningful(src):
                    skipped_empty += 1
                    continue
                # cheap dedupe: skip files already snapshotted with same mtime+size
                st = os.stat(src)
                sig = f"{st.st_mtime_ns}:{st.st_size}"
                if state.get(src) == sig:
                    skipped_unchanged += 1
                    continue
                rel = os.path.relpath(src, src_root)
                dst = os.path.join(snap_dir, os.path.basename(src_root) if False else "", rel) \
                    if prefix_filter else os.path.join(snap_dir, rel)
                try:
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.copy2(src, dst)
                    state[src] = sig
                    copied += 1
                except OSError:
                    errors += 1

    # prune snapshots older than KEEP_DAYS
    pruned = 0
    cutoff = now - datetime.timedelta(days=KEEP_DAYS)
    for entry in os.listdir(SNAPSHOT_DIR):
        ep = os.path.join(SNAPSHOT_DIR, entry)
        if not os.path.isdir(ep):
            continue
        try:
            dt = datetime.datetime.strptime(entry, "%Y-%m-%d_%H%M")
        except ValueError:
            continue
        if dt < cutoff:
            shutil.rmtree(ep, ignore_errors=True)
            pruned += 1

    save_state(state)
    print(
        f"cron-output snapshot {snap_name}: "
        f"copied {copied}, skipped {skipped_empty} empty/silent, "
        f"skipped {skipped_unchanged} unchanged, pruned {pruned} old snapshots"
        + (f", {errors} errors" if errors else "")
    )


if __name__ == "__main__":
    main()
