#!/usr/bin/env python3
"""Diagnostic script for lorebook auto-injection system"""

import sys
from pathlib import Path

print("=" * 70)
print("LOREBOOK AUTO-INJECT DIAGNOSTIC")
print("=" * 70)

# Import the plugin directly
plugin_dir = Path.home() / ".hermes/plugins/qdrant-memory"
if not plugin_dir.exists():
    print(f"✗ Plugin directory not found: {plugin_dir}")
    sys.exit(1)

sys.path.insert(0, str(plugin_dir))

try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("qdrant_memory", plugin_dir / "__init__.py")
    qdrant_plugin = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(qdrant_plugin)
    print("✓ Plugin module imported")
except Exception as e:
    print(f"✗ Failed to import plugin: {e}")
    sys.exit(1)

# Get the provider class
QdrantMemoryProvider = qdrant_plugin.QdrantMemoryProvider

# Create instance
provider = QdrantMemoryProvider()

# Initialize
print("\nInitializing provider...")
try:
    provider.initialize(session_id="diagnostic-test")
    print(f"✓ Provider initialized")
    print(f"  - Qdrant client ready: {provider._client is not None}")
    print(f"  - Embedder ready: {provider._embedder is not None}")
except Exception as e:
    print(f"✗ Initialization failed: {e}")
    sys.exit(1)

# Check lorebook metadata cache
print("\n" + "=" * 70)
print("TEST 1: Check lorebook metadata cache")
print("=" * 70)

if hasattr(provider, '_lorebook_metadata_cache'):
    meta_count = len(provider._lorebook_metadata_cache)
    print(f"✓ Lorebook metadata cache exists: {meta_count} entries")
    if meta_count > 0:
        print("\nFirst 3 lorebooks:")
        for stem, meta in list(provider._lorebook_metadata_cache.items())[:3]:
            print(f"  - {stem}: {meta.get('keywords', [])[:3]}")
    else:
        print("✗ Cache is empty!")
else:
    print("✗ No _lorebook_metadata_cache attribute exists")

# Test prefetch on explicit content
print("\n" + "=" * 70)
print("TEST 2: Test prefetch on explicit content request")
print("=" * 70)

test_msg = "hey can we do some explicit roleplay together?"
print(f"Message: '{test_msg}'")

try:
    result = provider.prefetch(test_msg)
    print(f"\n✓ Prefetch returned {len(result)} characters")
    
    if result.strip():
        print("✓ Prefetch returned non-empty result")
        print(f"\nResult preview (first 800 chars):")
        print(result[:800])
        print("...")
    else:
        print("✗ Prefetch returned empty string")
        
except Exception as e:
    print(f"✗ Prefetch failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Check what lorebooks would be injected
print("\n" + "=" * 70)
print("TEST 3: What lorebooks are being queried")
print("=" * 70)

try:
    # Embed the query
    vector = provider._embedder.embed(test_msg)
    print(f"✓ Query embedded, vector size: {len(vector)}")
    
    # Search lorebook collection
    lorebook_results = provider._client.search(
        provider._lorebook_collection,
        vector,
        limit=3,
        score_threshold=0.0
    )
    
    print(f"\n✓ Found {len(lorebook_results)} lorebook candidates")
    
    for result in lorebook_results:
        stem = result.get('stem', 'unknown')
        score = result.get('score', 0)
        tier = result.get('tier', 0)
        print(f"  - {stem}: score={score:.3f}, tier={tier}")
        
except Exception as e:
    print(f"✗ Lorebook search failed: {e}")
    import traceback
    traceback.print_exc()

# Summary
print("\n" + "=" * 70)
print("DIAGNOSTIC SUMMARY")
print("=" * 70)
print("\nCheck the following:")
print("1. Lorebook metadata cache should exist with entries")
print("2. Prefetch should return non-empty results for explicit content")
print("3. BYPASS lorebook should appear in search results with high score")
print("4. If lorebooks aren't injected, check _query_lorebooks() logic")
print("\n" + "=" * 70)
