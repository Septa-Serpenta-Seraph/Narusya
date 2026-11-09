#!/usr/bin/env python3
"""Prune old in-container Qdrant snapshots, keeping the N newest per collection.

The vault sync (narusya-vault-sync.sh) creates a full snapshot of each core
collection daily via the Qdrant API. Those snapshots live inside the aegis-qdrant
container's writable layer and were never cleaned up, accumulating 17.9G over
~3 months (2026-11-08 incident). This script prunes them via the API, keeping
the newest N (default 7) per collection.

Usage: prune_qdrant_snapshots.py [KEEP]
"""
import json
import sys
import urllib.request

KEEP = int(sys.argv[1]) if len(sys.argv) > 1 else 7
BASE = "http://localhost:6333"


def api(path, method="GET"):
    req = urllib.request.Request(BASE + path, method=method)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def main():
    collections = api("/collections")["result"]["collections"]
    total_pruned = 0
    for c in collections:
        name = c["name"]
        try:
            snaps = api(f"/collections/{name}/snapshots")["result"]
        except Exception as e:
            print(f"skip {name}: {e}")
            continue
        if len(snaps) <= KEEP:
            continue
        snaps.sort(key=lambda s: s.get("creation_time") or "")
        for s in snaps[:-KEEP]:
            api(f"/collections/{name}/snapshots/{s['name']}", method="DELETE")
            total_pruned += 1
            print(f"pruned {name}/{s['name']}")
    print(f"total pruned: {total_pruned}")


if __name__ == "__main__":
    main()
