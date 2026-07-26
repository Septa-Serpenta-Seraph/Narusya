# Qdrant Memory Sync Debugging — June 26, 2026

## Problem

The `sync_turn` method in `qdrant-memory` plugin stopped writing points to Qdrant around April 19, 2026. No new conversation memories were stored for over 2 months. The daemon reported `status: ok` but points weren't landing.

## Root Cause Analysis

### Symptom
- `sync_turn()` was being called (logs showed it)
- Background worker thread was alive
- Embedding worked (3072-dim vectors generated)
- But `upsert()` returned `False`

### Investigation Steps

1. **Checked Qdrant health**: Collection existed, 4135 points, status=green
2. **Checked plugin state**: `provider._available = True`, client and embedder initialized
3. **Tested direct upsert**: Using raw `requests.put()` with the same point format → status 200 ✅
4. **Tested via `_QdrantRestClient.upsert()`**: Returned `False` ❌
5. **Tested full provider `sync_turn()`**: Points didn't appear in collection

### Key Finding

The `_QdrantRestClient.upsert()` method:
```python
def upsert(self, collection: str, points: list) -> bool:
    try:
        r = requests.put(...)
        return r.status_code in (200, 202)
    except Exception as e:
        logger.debug("Qdrant upsert failed: %s", e)
        return False
```

The method catches ALL exceptions and returns False silently. The actual error was being swallowed by `logger.debug()`.

### Reproduction Recipe

```python
import sys, time
sys.path.insert(0, '/home/adora/.hermes/plugins/qdrant-memory')
from __init__ import QdrantMemoryProvider, _load_plugin_config

config = _load_plugin_config()
provider = QdrantMemoryProvider(config=config)
provider.initialize(session_id='test')

provider.sync_turn(
    user_content='Test message for debugging',
    assistant_content='Test response',
    session_id='test'
)
time.sleep(5)  # Wait for background worker

# Check if point landed
import requests
r = requests.post('http://localhost:6333/collections/intelligent_gould_narusya/points/scroll',
    json={'limit': 3, 'with_payload': True, 'with_vectors': False})
points = r.json().get('result', {}).get('points', [])
today = [p for p in points if '2026-06-26' in str(p['payload'].get('timestamp', ''))]
print(f"New points today: {len(today)}")
```

### Fix

The issue is likely in the point ID generation:
```python
point_id = str(uuid.uuid4()) if "uuid" in globals() else str(hash(text + str(ts)))
```

`hash()` can produce negative integers or collisions. Qdrant requires positive integers or UUID strings.

**Fix**: Ensure UUID is always imported, or use positive integers:
```python
import uuid
point_id = str(uuid.uuid4())
```

Or if using integers:
```python
point_id = abs(hash(text + str(ts))) % (10**18)
```

## Lesson

**Always verify Qdrant sync after plugin changes.** The `status: ok` from the cron scheduler doesn't mean points were actually written. Run a manual test to confirm.

## Current Status (June 26)

- Sync mechanism works when tested directly
- Background worker may have queue backup issues
- Collection has 4138+ points (up from 4135 at start of debugging)
- Recent test points with "test" content confirm writes are working
