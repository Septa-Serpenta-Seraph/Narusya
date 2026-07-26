#!/usr/bin/env python3
"""Verify reflection lorebooks are actually present in the narusya_lorebooks Qdrant collection.

Run AFTER `ingest_lorebooks.py`. Exits non-zero if any on-disk reflection is
missing from Qdrant, so it can gate a cron step or just warn you that
auto-inject is half-dark.

Why this exists: ingest_lorebooks.py historically globbed only the top level of
~/.hermes/lorebooks/ and silently dropped the reflections/ subdirectory. The
re-ingest command reported success while reflections never reached Qdrant.
The glob was patched 2026-07-07 to recurse into subdirs; this probe guards
against any future regression re-hiding the reflections.
"""
import sys
import requests
from pathlib import Path

QDRANT_URL = "http://localhost:6333"
COLLECTION = "narusya_lorebooks"
REFLECTIONS_DIR = Path.home() / ".hermes" / "lorebooks" / "reflections"


def main():
    if not REFLECTIONS_DIR.exists():
        print("No reflections/ dir found — nothing to verify.")
        return 0
    disk = sorted(p.name for p in REFLECTIONS_DIR.glob("*.md"))
    if not disk:
        print("reflections/ is empty — nothing to verify.")
        return 0

    try:
        r = requests.post(
            f"{QDRANT_URL}/collections/{COLLECTION}/points/scroll",
            json={"limit": 1000, "with_payload": True},
            timeout=10,
        )
        r.raise_for_status()
        points = r.json()["result"]["points"]
    except Exception as e:
        print("ERROR: could not query Qdrant: %s" % e, file=sys.stderr)
        return 2

    in_qdrant = set()
    for p in points:
        payload = p.get("payload") or {}
        stem = payload.get("stem", "")
        if stem.startswith("reflections:"):
            in_qdrant.add(payload.get("filename"))

    print("Reflections on disk:  %d" % len(disk))
    print("Reflections in Qdrant: %d" % len(in_qdrant))
    for d in disk:
        mark = "OK  " if d in in_qdrant else "MISS"
        print("  [%s] %s" % (mark, d))

    missing = [d for d in disk if d not in in_qdrant]
    if missing:
        print("\nMISSING from Qdrant: %s" % ", ".join(missing), file=sys.stderr)
        print("Re-run ingest and confirm reflections/ glob is recursed.", file=sys.stderr)
        return 1
    print("\nAll reflections present in Qdrant. Auto-inject is not half-dark.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
