"""
Step 1: Create the narusya_lorebooks Qdrant collection
"""
import requests
import json
import sys

QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "narusya_lorebooks"
VECTOR_SIZE = 3072
DISTANCE = "Cosine"

# Create collection payload
create_payload = {
    "vectors": {
        "size": VECTOR_SIZE,
        "distance": DISTANCE
    },
    "optimizers_config": {
        "indexing_threshold": 20
    },
    "replication_factor": 1
}

try:
    # Check if collection exists
    check = requests.get(f"{QDRANT_URL}/collections/{COLLECTION_NAME}", timeout=5)
    if check.status_code == 200:
        print(f"Collection '{COLLECTION_NAME}' already exists")
    else:
        # Create new collection
        response = requests.put(
            f"{QDRANT_URL}/collections/{COLLECTION_NAME}",
            json=create_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        response.raise_for_status()
        print(f"✅ Created collection '{COLLECTION_NAME}'")
        
    # Verify
    info = requests.get(f"{QDRANT_URL}/collections/{COLLECTION_NAME}", timeout=5)
    info.raise_for_status()
    result = info.json()["result"]
    print(f"   Vectors: {result.get('vectors_count', 0)}")
    print(f"   Status: {result.get('status')}")
    print(f"\n✅ Step 1 complete — collection ready")
    
except Exception as e:
    print(f"❌ Failed to create collection: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)
