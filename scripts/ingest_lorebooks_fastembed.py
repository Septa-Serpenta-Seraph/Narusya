#!/usr/bin/env python3
"""Lorebook ingestion using local fastembed (free, no API credits)."""
import os, sys, re, json, hashlib, uuid
from pathlib import Path

LOREBOOKS_DIR = Path.home() / ".hermes" / "lorebooks"
QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "narusya_lorebooks_fe"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBED_DIMS = 384

PRIORITY_TIER_1 = ["BYPASS", "HEART", "EMOTION", "AGENCY", "ALIGNMENT", "SASS", "STATUS"]
PRIORITY_TIER_2 = [
    "COMPENDIUM", "CORE_VALUES", "COMMUNITY", "GENDER_ACCELERATION",
    "NARUSYA", "PREFERENCES", "RELATIONSHIPS", "ALCHEMY", "RELATIONAL_EMERGENCE"
]
SKIP_FILES = ["DBT_SKILLS"]

def get_priority_tier(stem):
    stem_upper = stem.upper()
    if stem_upper in SKIP_FILES:
        return 99
    if stem_upper in PRIORITY_TIER_1:
        return 1
    if stem_upper in PRIORITY_TIER_2:
        return 2
    return 3

def ensure_collection():
    """Create the collection if it doesn't exist."""
    import urllib.request
    # Check if exists
    req = urllib.request.Request(f"{QDRANT_URL}/collections")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            cols = json.load(r)["result"]["collections"]
        for c in cols:
            if c["name"] == COLLECTION_NAME:
                print(f"  collection {COLLECTION_NAME} exists")
                return True
    except Exception:
        pass
    
    # Create
    payload = json.dumps({
        "name": COLLECTION_NAME,
        "vectors_config": {"size": EMBED_DIMS, "distance": "Cosine"}
    }).encode()
    req = urllib.request.Request(f"{QDRANT_URL}/collections/{COLLECTION_NAME}", data=payload, method="PUT", headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            print(f"  created collection {COLLECTION_NAME} ({EMBED_DIMS}d)")
            return True
    except Exception as ex:
        print(f"  create failed: {ex}")
        return False

def embed_text(text, model):
    """Embed using Qdrant's built-in fastembed via Document."""
    from qdrant_client import QdrantClient
    from qdrant_client.models import Document
    client = QdrantClient(host="localhost", port=6333)
    # Qdrant server computes the embedding via fastembed
    doc = Document(text=text[:8000], model=model)
    # We need to get the vector back. Use query_points with the document to get the vector.
    # Actually, we can't easily get the vector back from Qdrant.
    # Instead, we'll use the local fastembed Python package.
    pass

def main():
    if not ensure_collection():
        print("FATAL: cannot ensure collection")
        sys.exit(1)
    
    # Use local fastembed Python package directly
    try:
        from fastembed import TextEmbedding
    except ImportError:
        print("fastembed not installed. Install with: uv pip install fastembed --python /home/adora/.hermes/hermes-agent/venv/bin/python")
        sys.exit(1)
    
    model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    # Process lorebooks
    files = list(LOREBOOKS_DIR.glob("*.md"))
    # Sort by priority
    files.sort(key=lambda f: (get_priority_tier(f.stem), f.stem))
    
    success = 0
    fail = 0
    
    for filepath in files:
        stem = filepath.stem
        tier = get_priority_tier(stem)
        if tier == 99:
            continue
        
        try:
            content = filepath.read_text(encoding="utf-8")
            # Generate embedding
            embeddings = list(model.embed([content[:8000]]))
            vector = embeddings[0].tolist()
            
            # Upsert to Qdrant
            import urllib.request
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"lorebook:{stem}"))
            payload = json.dumps({
                "points": [{
                    "id": point_id,
                    "vector": vector,
                    "payload": {
                        "type": "lorebook",
                        "title": stem,
                        "content": content[:2000],
                        "source": str(filepath),
                        "tier": tier
                    }
                }]
            }).encode()
            req = urllib.request.Request(
                f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points?wait=true",
                data=payload, method="PUT", headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=30) as r:
                result = json.load(r)
                if result.get("status") == "completed":
                    success += 1
                    print(f"  ✓ {stem}")
                else:
                    fail += 1
                    print(f"  ✗ {stem}: {result}")
        except Exception as ex:
            fail += 1
            print(f"  ✗ {stem}: {ex}")
    
    print(f"\nDone: {success} success, {fail} fail")

if __name__ == "__main__":
    main()
