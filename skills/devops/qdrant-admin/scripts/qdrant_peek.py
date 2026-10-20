#!/usr/bin/env python3
"""Sample N points from one collection — see what it ACTUALLY holds.

Usage: python3 qdrant_peek.py [collection] [-n 6] [--offset <id>]

Never characterize a collection from a single point: the first one can be a
stray test entry. Run this with -n 6+ before calling anything junk.
"""
import argparse
import json
import os
import urllib.request

BASE = os.environ.get("QDRANT_URL", "http://127.0.0.1:6333")


def post(path, data):
    req = urllib.request.Request(BASE + path, method="POST",
                                 data=json.dumps(data).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=120))


ap = argparse.ArgumentParser()
ap.add_argument("collection", nargs="?", default="")
ap.add_argument("-n", type=int, default=6)
ap.add_argument("--offset", default=None)
args = ap.parse_args()

if not args.collection:
    for c in json.load(urllib.request.urlopen(BASE + "/collections"))["result"]["collections"]:
        print(c["name"])
    raise SystemExit(0)

body = {"limit": args.n, "with_payload": True, "with_vector": False}
if args.offset:
    body["offset"] = args.offset
res = post(f"/collections/{args.collection}/points/scroll", body)
pts = res["result"]["points"]
print(f"### {args.collection} — {len(pts)} sample point(s) ###")
for p in pts:
    pl = p.get("payload") or {}
    print(f"\n--- id={p.get('id')} keys={list(pl.keys())}")
    for k, v in pl.items():
        s = str(v).replace("\n", " ")
        print(f"    {k}: {s[:200]}")
