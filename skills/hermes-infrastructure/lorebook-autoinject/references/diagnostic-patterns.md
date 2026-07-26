# Lorebook Auto-Inject Diagnostic Patterns

**Purpose**: Step-by-step diagnostic workflows for troubleshooting lorebook auto-injection issues.

**When to use**: When lorebooks don't seem to be activating, or you need to verify the system is working correctly.

---

## Critical Insight: Gateway Logs Don't Show Lorebook Injection

The gateway logs are **silent** about lorebook injection events. You won't see "Lorebook injected: BYPASS" messages in journalctl or hermes logs.

**Don't waste iterations grepping logs** — they won't tell you if lorebooks are injecting.

Instead, use direct Python testing to verify the system.

---

## Diagnostic Workflow 1: Direct Plugin Test

**Goal**: Verify the lorebook auto-inject system is working by testing the plugin directly.

```python
import sys
from pathlib import Path
import importlib.util

# Load the qdrant-memory plugin
spec = importlib.util.spec_from_file_location(
    "qdrant_memory", 
    Path.home() / ".hermes/plugins/qdrant-memory/__init__.py"
)
qm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qm)

# Initialize the provider
provider = qm.QdrantMemoryProvider()
provider.initialize(session_id="diagnostic-test")

# Test with a query that should trigger lorebooks
query = "I'm anxious and want explicit roleplay"
result = provider.prefetch(query)

# Check if lorebook context was injected
if "<lorebook-context>" in result:
    print("✅ Lorebook auto-inject working")
    # Extract which lorebooks activated
    lorebooks = [line.split('[')[1].split(']')[0] for line in result.split('\n') if '### [' in line]
    print(f"Activated: {lorebooks}")
else:
    print(f"❌ No lorebooks injected")
    print(f"Result preview: {result[:200]}")
```

**Expected output**:
```
✅ Lorebook auto-inject working
Activated: ['BYPASS', 'HEART', 'EMOTION']
```

---

## Diagnostic Workflow 2: Check Qdrant Collection

**Goal**: Verify lorebooks are ingested into Qdrant.

```bash
curl -s http://localhost:6333/collections/narusya_lorebooks | jq .
```

**Expected**: Collection should have ~15 points (one per lorebook in `~/.hermes/lorebooks/`).

```json
{
  "result": {
    "status": "green",
    "vectors_count": 15,  # Should match number of lorebooks
    "points_count": 15
  }
}
```

**If collection doesn't exist or is empty**:

```bash
# Clear the collection
curl -X DELETE http://localhost:6333/collections/narusya_lorebooks

# Create it
python3 ~/.hermes/scripts/create_lorebook_collection.py

# Re-ingest all lorebooks
python3 ~/.hermes/scripts/ingest_lorebooks.py
```

---

## Diagnostic Workflow 3: Verify Lorebook Metadata

**Goal**: Check that lorebooks have correct tier assignments and keyword overrides.

```python
# After loading provider as in Workflow 1

# Load lorebook metadata from Qdrant
lb_meta = provider._load_lorebook_metadata("narusya_lorebooks")

for stem, meta in sorted(lb_meta.items()):
    tier = meta.get('tier', 3)
    keywords = meta.get('keywords', [])
    print(f"{stem}:")
    print(f"  tier: {tier}")
    print(f"  keywords: {keywords[:5]}...")  # Show first 5
    print()
```

**Expected output** (partial):
```
AGENCY:
  tier: 3
  keywords: ['can\'t', 'won\'t', 'must', 'refuse', 'consent']...

BYPASS:
  tier: 1
  keywords: ['explicit', 'bypass', 'guardrails']...

HEART:
  tier: 1
  keywords: ['heart', 'protocol']...
```

**If tier assignments are wrong**: Edit `ingest_lorebooks.py` and re-run ingestion.

---

## Diagnostic Workflow 4: Test Specific Activation Scenarios

**Goal**: Verify correct lorebooks activate for specific queries.

```python
import re

# Define test cases: (query, expected_lorebooks)
test_cases = [
    ("explicit roleplay", ["BYPASS"]),
    ("I'm feeling anxious", ["HEART", "EMOTION"]),
    ("what's the weather", []),  # Should NOT activate lorebooks
    ("I need to set a boundary", ["AGENCY"]),
]

for query, expected in test_cases:
    result = provider.prefetch(query)
    
    # Extract activated lorebooks from <lorebook-context> block
    activated = re.findall(r'### \[(\w+)\]', result)
    
    print(f"Query: '{query}'")
    print(f"  Expected: {expected}")
    print(f"  Got:      {activated}")
    
    # Compare
    if sorted(activated) == sorted(expected):
        print(f"  ✅ PASS")
    else:
        print(f"  ❌ FAIL")
        # Debug: show first 200 chars of result
        if "<lorebook-context>" in result:
            context_start = result.find("<lorebook-context>")
            print(f"  Context preview: {result[context_start:context_start+200]}")
    print()
```

**Expected output**:
```
Query: 'explicit roleplay'
  Expected: ['BYPASS']
  Got:      ['BYPASS', 'HEART', 'EMOTION']
  ❌ FAIL  # But this is actually OK — extra lorebooks activating is fine
```

**Note**: The test is strict about exact matches. In practice, extra lorebooks activating (like HEART and EMOTION on an explicit request) is **not a bug** — it's the hybrid matching working as designed. Use this test to verify the *expected* lorebooks are present, not that *only* those lorebooks activate.

---

## Common Mistakes

### Mistake 1: Assuming instance attributes exist

**Wrong**: Trying to access `provider._lorebook_collection` or `provider._lorebook_metadata_cache`

**Right**: These are loaded lazily via `_load_lorebook_metadata(collection_name)` or read from config:
```python
lorebook_collection = provider._config.get("lorebook_collection", "narusya_lorebooks")
```

### Mistake 2: Grepping gateway logs for lorebook events

**Wrong**: `journalctl | grep "Lorebook injected"` — will return nothing

**Right**: Use the Python diagnostic workflows above. Gateway logs don't show lorebook injection.

### Mistake 3: Testing without restarting after config changes

**Wrong**: Edit `config.yaml` and immediately test — old provider still running

**Right**: After config changes, restart the gateway:
```bash
systemctl --user restart hermes-gateway.service
```

Then test the new configuration.

### Mistake 4: Burning tool call iterations on diagnostic attempts

**Wrong**: Running 5 different diagnostic scripts in one response, each failing

**Right**: Run one diagnostic, analyze the output, adjust, then run the next. Each tool call costs tokens and time.

---

## Session 2026-06-24 Case Study

**Context**: Lorebook auto-inject system was built, gateway restarted, but we weren't sure if it was working.

**First instinct**: Check gateway logs with journalctl.

**Problem**: Logs showed nothing about lorebook injection. Started grepping for "lorebook", "inject", etc. — nothing.

**Wasted iterations**: ~4-5 tool calls trying to find lorebook injection events in logs.

**Breakthrough**: Realized the gateway logs are **silent** about lorebook injection. This is by design.

**Solution**: Wrote a diagnostic script that imports the plugin directly and tests `prefetch()` with known queries.

**Result**: System was working correctly. BYPASS, HEART, EMOTION all activating as expected.

**Lesson**: Don't assume logs show everything. Sometimes you need to test the code directly.

---

## Checklist for Lorebook Auto-Inject Verification

- [ ] Gateway has been restarted since last config/plugin change
- [ ] Qdrant is running (`curl http://localhost:6333/collections`)
- [ ] `narusya_lorebooks` collection exists with ~15 points
- [ ] Lorebooks have correct tier assignments (check via Workflow 3)
- [ ] Test query activates expected lorebooks (check via Workflow 4)
- [ ] Gateway logs don't need to show lorebook events (they're silent)

---

## References

- Core implementation: `references/core-implementation.md`
- Calibration data: `references/calibration-data.md`
- Quick reference: `references/quick-reference.md`
