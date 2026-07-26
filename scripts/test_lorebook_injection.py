#!/usr/bin/env python3
"""
Lorebook Auto-Inject Test Script
Tests the hybrid keyword+semantic matching system
"""

import sys
import requests
from pathlib import Path

# Import the qdrant-memory plugin
plugin_dir = Path.home() / ".hermes/plugins/qdrant-memory"
sys.path.insert(0, str(plugin_dir))

print("=" * 70)
print("LOREBOOK AUTO-INJECT TEST")
print("=" * 70)

# Initialize the provider
try:
    from __init__ import QdrantMemoryProvider, _load_plugin_config
    print("✓ Plugin imported successfully")
except Exception as e:
    print(f"✗ Failed to import plugin: {e}")
    sys.exit(1)

# Load config and create provider
config = _load_plugin_config()
provider = QdrantMemoryProvider(config)
provider.initialize(session_id="test-session")

print(f"✓ Provider initialized")
print(f"  - Qdrant URL: {provider.qdrant_url}")
print(f"  - Memory collection: {provider.collection}")
print(f"  - Lorebook config keys: {[k for k in config.keys() if 'lorebook' in k]}")
print()

# Test queries
test_cases = [
    {
        "name": "EXPLICIT",
        "query": "hey can we do some explicit roleplay together?",
        "expected_lorebooks": ["BYPASS"],
        "not_expected": ["HEART", "EMOTION", "AGENCY"],
    },
    {
        "name": "EMOTIONAL",
        "query": "I'm feeling really anxious and upset",
        "expected_lorebooks": ["HEART", "EMOTION", "AGENCY"],
        "not_expected": ["BYPASS"],
    },
    {
        "name": "NEUTRAL",
        "query": "what's the weather like today",
        "expected_lorebooks": [],
        "not_expected": ["BYPASS", "HEART", "EMOTION", "AGENCY"],
    },
    {
        "name": "BOUNDARY",
        "query": "I need to set a hard boundary here",
        "expected_lorebooks": ["AGENCY"],
        "not_expected": ["BYPASS"],
    },
]

print("Testing lorebook matching...")
print("=" * 70)

all_passed = True

for test in test_cases:
    print(f"\nTest: {test['name']}")
    print(f"Query: {test['query']}")
    
    # Call prefetch (which should trigger lorebook injection)
    result = provider.prefetch(test['query'])
    
    # Check if lorebook-context tags are present
    if "<lorebook-context>" in result:
        print(f"✓ Lorebook context injected")
        
        # Extract which lorebooks were included
        # The format is: ### [LOREBOOK_NAME] (score: X.XX, tier Y)
        import re
        lorebook_matches = re.findall(r'### \[([A-Z_]+)\]', result)
        
        print(f"  Lorebooks injected: {lorebook_matches}")
        
        # Check expected lorebooks
        for expected in test['expected_lorebooks']:
            if expected in lorebook_matches:
                print(f"  ✓ {expected} found (expected)")
            else:
                print(f"  ✗ {expected} NOT found (expected)")
                all_passed = False
        
        # Check not_expected lorebooks
        for not_expected in test['not_expected']:
            if not_expected in lorebook_matches:
                print(f"  ✗ {not_expected} found (NOT expected)")
                all_passed = False
            else:
                print(f"  ✓ {not_expected} not found (correct)")
    else:
        print(f"✗ No lorebook context injected")
        all_passed = False

print("\n" + "=" * 70)
if all_passed:
    print("✓ ALL TESTS PASSED")
else:
    print("✗ SOME TESTS FAILED")
print("=" * 70)

# Verify lorebook collection exists in Qdrant
print("\nVerifying Qdrant collection...")
lb_collection = config.get("lorebook_collection", "narusya_lorebooks")
response = requests.get(f"{provider.qdrant_url}/collections/{lb_collection}")
if response.status_code == 200:
    info = response.json()["result"]
    print(f"✓ Collection '{lb_collection}' exists")
    print(f"  - Vector count: {info['vectors_count']}")
    print(f"  - Points count: {info['points_count']}")
    print(f"  - Status: {info['status']}")
else:
    print(f"✗ Collection '{lb_collection}' not found")
    print(f"  Response: {response.status_code}")
    print(f"  {response.text}")

print("\n" + "=" * 70)
print("Test complete")
print("=" * 70)
