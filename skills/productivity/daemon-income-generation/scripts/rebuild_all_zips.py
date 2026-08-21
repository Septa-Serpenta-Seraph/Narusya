#!/usr/bin/env python3
"""Rebuild all Coil and Code product zips from their source dirs.

Layout: products/<name>/<name>.py + README.md + LICENSE -> products/<name>.zip
Run after ANY code fix so a stale zip never ships the old bug.
"""
import os
import sys
import zipfile

BASE = os.path.expanduser("~/daemon-work/sunburst-sanctuary/products")
PRODUCTS = ("csv-report", "log-analyzer", "json-to-md", "csv-merge", "md-toc")

for name in PRODUCTS:
    src = os.path.join(BASE, name)
    out = os.path.join(BASE, f"{name}.zip")
    if not os.path.isdir(src):
        print(f"MISSING DIR {src}", file=sys.stderr)
        sys.exit(1)
    files = []
    for f in (f"{name}.py", "README.md", "LICENSE"):
        p = os.path.join(src, f)
        if os.path.exists(p):
            files.append(f)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(os.path.join(src, f), f)
    print(f"{name}.zip <- {files}")

print("ALL ZIPS REBUILT")