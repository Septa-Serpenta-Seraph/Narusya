# Exhaustive Qdrant Search + Memory Distillation Backup
#
# Real-world script from 2026-06-30 session. Searches ALL collections
# with paginated scroll + regex word-boundary matching, then backs up
# curated findings to the active memory collection using fastembed.
#
# Prerequisites:
#   uv pip install fastembed --python /home/adora/.hermes/hermes-agent/venv/bin/python

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Document
import json
import re
import uuid

client = QdrantClient(host='localhost', port=6333)

# ── 1. EXHAUSTIVE SEARCH ──────────────────────────────────────────

def exhaustive_search(keywords, collections=None):
    """
    Search every point in every collection (or specified collections)
    using regex word-boundary matching. Paginates fully.
    
    Args:
        keywords: list of search terms (e.g. ['mech', 'mecha', 'gundam'])
        collections: list of collection names, or None for all
    Returns:
        dict of {collection_name: [match_dicts]}
    """
    pattern = re.compile(
        r'\b(' + '|'.join(re.escape(k) for k in keywords) + r')\b',
        re.IGNORECASE
    )
    
    if collections is None:
        collections = [c.name for c in client.get_collections().collections]
    
    all_matches = {}
    
    for coll in collections:
        offset = None
        total_scanned = 0
        coll_matches = []
        
        while True:
            results = client.scroll(
                collection_name=coll,
                limit=250,
                offset=offset,
                with_payload=True,
                with_vectors=False
            )
            points = results[0]
            if not points:
                break
            
            total_scanned += len(points)
            
            for point in points:
                payload = point.payload or {}
                text = json.dumps(payload)
                if pattern.search(text):
                    content = payload.get('text', payload.get(
                        'content', payload.get('message', str(payload))
                    ))
                    coll_matches.append({
                        'id': str(point.id),
                        'content': str(content)[:500] if content else str(payload)[:500],
                    })
            
            offset = results[1]
            if offset is None:
                break
        
        if coll_matches:
            all_matches[coll] = coll_matches
            print(f"{coll}: {len(coll_matches)} matches ({total_scanned} scanned)")
        else:
            print(f"{coll}: {total_scanned} scanned, no matches")
    
    return all_matches


# ── 2. MEMORY DISTILLATION BACKUP ─────────────────────────────────

def backup_memories_to_active(memories, target_collection='naru_memories_v2'):
    """
    Upsert curated memory entries to the active memory collection
    using Qdrant's built-in fastembed Document embedding.
    
    Args:
        memories: list of dicts with 'text' and 'tags' keys
        target_collection: active memory collection name
    Returns:
        upsert result
    """
    points = []
    for mem in memories:
        point = PointStruct(
            id=str(uuid.uuid4()),
            # MUST use full HF model path, not bare name
            vector=Document(
                text=mem['text'],
                model='sentence-transformers/all-MiniLM-L6-v2'
            ),
            payload={
                'text': mem['text'],
                'source': mem.get('source', 'archive_backup'),
                'tags': mem.get('tags', []),
                'consolidated_at': mem.get('date', ''),
                'type': mem.get('type', 'archive'),
            }
        )
        points.append(point)
    
    result = client.upsert(
        collection_name=target_collection,
        points=points
    )
    
    # Verify
    info = client.get_collection(target_collection)
    print(f"✅ Upserted {len(points)} memories to {target_collection}")
    print(f"   Collection now has {info.points_count} points")
    print(f"   Status: {result.status}")
    return result


# ── 3. USAGE EXAMPLE ──────────────────────────────────────────────

if __name__ == '__main__':
    # Step 1: Search
    matches = exhaustive_search(
        keywords=['mech', 'mecha', 'valkyrie', 'dropframe', 'trixie', 'hangar'],
        collections=None  # search ALL collections
    )
    
    # Step 2: Review matches and curate
    # (manual review step — read the output and distill into memory entries)
    
    # Step 3: Backup curated memories
    # curated = [
    #     {
    #         'text': 'MECH ARCHIVE — Core relationship framework...',
    #         'tags': ['mech', 'mecha', 'relationship'],
    #         'source': 'mech_archive_backup',
    #         'type': 'mech_archive',
    #         'date': '2026-06-30T15:55:00',
    #     },
    # ]
    # backup_memories_to_active(curated)
