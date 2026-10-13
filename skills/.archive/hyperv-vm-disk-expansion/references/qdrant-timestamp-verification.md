# Verifying Memory Integrity After Disk Expansion

After expanding VM storage, Qdrant should continue working normally.
If timestamps look wrong, follow this diagnostic.

## Check Collection Health
```bash
curl -s http://localhost:6333/collections | python3 -m json.tool
```

## Sample Points and Inspect Timestamps
```bash
curl -s http://localhost:6333/collections/intelligent_gould_narusya/points/scroll \
  -X POST -H "Content-Type: application/json" \
  -d '{"limit": 10, "with_payload": true, "with_vector": false}'
```

## Interpreting Timestamps

Points have TWO timestamp fields:
1. **Point ID** (Unix ms): The authoritative timestamp. Convert with Python:
```python
from datetime import datetime, timezone
dt = datetime.fromtimestamp(point_id / 1000, tz=timezone.utc)
print(dt.isoformat())
```

2. **Content text**: Often contains "[YYYY-MM-DD]" prefix in the stored text.
   This is metadata embedded in the content, NOT authoritative.
   Can be wrong if the embedding model hallucinated a date or if
   content was copied from a different session.

**Rule:** If the Unix timestamp says 2025 but the content says [2026-...],
the Unix timestamp is correct. Trust the machine, not the text.

## Verify No Data Loss
```bash
# Count total points
curl -s http://localhost:6333/collections/intelligent_gould_narusya | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['result']['points_count'])"
```
This number should match the last known count. If it dropped, investigate.
