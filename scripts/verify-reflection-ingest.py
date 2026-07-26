#!/usr/bin/env python3
"""Verify every reflection lorebook actually landed in Qdrant.

The re-ingest script historically globbed only the top level of
~/.hermes/lorebooks/ and silently dropped the entire reflections/
subdirectory. Even after the recursion patch, the ingest script prints
bare filenames (not 'reflections/on-...' paths), so the skill's old
`grep -i 'reflections/on-'` check returns nothing and falsely alarms.

This probe checks Qdrant directly: for every file under
~/.hermes/lorebooks/reflections/*.md it derives the point_id the ingest
script uses (uuid5 DNS namespace over the 'reflections:<stem>' override
stem) and confirms the point exists with the expected title.

Exits non-zero if any reflection is missing — so a cron re-ingest can
fail loudly instead of hiding your work.
"""

import sys
import uuid
from pathlib import Path

import requests

QDRANT_URL = "http://localhost:6333"
COLLECTION = "narusya_lorebooks"
REFLECTIONS_DIR = Path.home() / ".hermes" / "lorebooks" / "reflections"


def main():
    if not REFLECTIONS_DIR.is_dir():
        print("ERROR: reflections dir not found: %s" % REFLECTIONS_DIR)
        return 2

    files = sorted(REFLECTIONS_DIR.glob("*.md"))
    if not files:
        print("WARN: no reflection files found")
        return 0

    missing = []
    ok = []
    for md in files:
        stem = "reflections:%s" % md.stem
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, stem))
        try:
            r = requests.get(
                "%s/collections/%s/points/%s" % (QDRANT_URL, COLLECTION, point_id),
                timeout=20,
            )
        except requests.exceptions.RequestException as e:
            print("  Qdrant unreachable: %s" % e)
            missing.append((stem, "connection error"))
            continue
        if r.status_code == 200:
            title = r.json().get("result", {}).get("payload", {}).get("title", "?")
            ok.append((stem, title))
        else:
            missing.append((stem, "HTTP %s" % r.status_code))

    print("Reflection ingest verification")
    print("=" * 50)
    for stem, title in ok:
        print("  OK   %s  (%s)" % (stem, title))
    for stem, why in missing:
        print("  MISS %s  (%s)" % (stem, why))
    print("=" * 50)
    print("%d present, %d missing, of %d" % (len(ok), len(missing), len(files)))

    if missing:
        print("\nFAIL: reflections missing from Qdrant. Re-run:")
        print("  python3 ~/.hermes/scripts/ingest_lorebooks.py")
        return 1
    print("\nAll reflections present in Qdrant.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
