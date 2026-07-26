---
name: qdrant-usage
description: "Qdrant usage patterns: semantic search setup, manual archival, and forensic investigative search. Use for memory search, document archival, or conversation forensics."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [qdrant, vector-search, semantic-search, archival, investigation, forensics]
    related_skills: [qdrant-vector-search, qdrant-memory-diagnostics, qdrant-memory-provider]
---

# Qdrant Usage Patterns

Qdrant usage patterns: semantic search setup, manual document archival, and forensic investigative search.

## Quick Decision

| Use case | Section |
|----------|---------|
| Set up semantic search / migrate from hash-based | semantic-search section |
| Save documents into Qdrant for retrieval | manual-archive section |
| Investigate claims/accusations in conversation logs | investigative-search section |

---

## 1. Semantic Search Setup (qdrant-semantic-search)

Set up semantic search for AI memory collections in Qdrant using sentence-transformers. Migrates existing hash-based embeddings to proper vector embeddings.

### Prerequisites

```bash
curl -s http://localhost:6333/collections | jq .
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip3 install sentence-transformers qdrant-client
```

### Workflow

**Step 1:** Check current collections:
```python
from qdrant_client import QdrantClient
client = QdrantClient(host="localhost", port=6333)
collections = client.get_collections()
for c in collections.collections:
    print(f"{c.name}: {client.count(c.name).count} points")
```

**Step 2:** Create new collection with proper vector config:
```python
from qdrant_client import models

client.create_collection(
    collection_name="naru_memories_v2",
    vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
)
```

**Step 3:** Load model and migrate points:
```python
from sentence_transformers import SentenceTransformer
import time

model = SentenceTransformer('all-MiniLM-L6-v2')
old_points = client.scroll(collection_name="naru_memories", limit=1000, with_payload=True, with_vectors=False)[0]

points_to_upsert = []
for idx, point in enumerate(old_points):
    text = point.payload.get('text', '')
    if text:
        vector = model.encode(text).tolist()
        points_to_upsert.append(models.PointStruct(id=point.id, vector=vector, payload=point.payload))
    if len(points_to_upsert) >= 50:
        client.upsert(collection_name="naru_memories_v2", points=points_to_upsert)
        points_to_upsert = []
        time.sleep(0.1)

if points_to_upsert:
    client.upsert(collection_name="naru_memories_v2", points=points_to_upsert)
```

**Step 4:** Verify and test:
```python
def search_memories(query, limit=5):
    query_vector = model.encode(query).tolist()
    return client.search(collection_name="naru_memories_v2", query_vector=query_vector, limit=limit, with_payload=True)

print(search_memories("AI companions and family"))
```

### Troubleshooting

- **Model loading timeout** — run in background process or download ahead of time
- **Disk space issues** — `pip cache purge`, remove old recordings if safe
- **Collection already exists** — delete and recreate (WARNING: destroys data)

### Ad-Hoc Keyword Search (when execute_code blocked)

```bash
cat > /home/adora/.hermes/qdrant_search.py << 'PYEOF'
from qdrant_client import QdrantClient
client = QdrantClient(url="http://localhost:6333")
keywords = ["serpent", "violet", "amethyst", "scale"]
for coll in ["intelligent_gould_narusya", "naru_memory", "naru_memories_v2"]:
    results = client.scroll(collection_name=coll, limit=300, with_payload=True, with_vectors=False)
    for point in results[0]:
        payload = point.payload or {}
        content = str(payload)
        for kw in keywords:
            if kw.lower() in content.lower():
                idx = content.lower().find(kw.lower())
                print(f"\n=== {coll} | '{kw}' ===")
                print(content[max(0,idx-80):idx+250].replace("\n", " "))
                break
PYEOF
python3 /home/adora/.hermes/qdrant_search.py
```

---

## 2. Manual Document Archive (qdrant-manual-archive)

Persist documents, research, or recon data into Qdrant for semantic retrieval.

### When to Use
- Saving lorebooks, research essays, or long-form analysis
- Archiving server reconnaissance or community intel
- Creating dedicated collections for specific domains

### Prerequisites
- Qdrant running locally (localhost:6333)
- OpenRouter API key in environment
- `openai` and `qdrant-client` packages

### Workflow

**Step 1:** Read & prepare documents:
```python
paths = [os.path.expanduser("~/.hermes/lorebooks/YOUR-LOREBOOK.md")]
docs = []
for p in paths:
    with open(p) as f:
        docs.append({"path": p, "content": f.read()})
```

**Step 2:** Generate embeddings (use text-embedding-3-large for 3072d):
```python
import openai, os
or_key = os.environ.get("OPENROUTER_API_KEY")
client = openai.OpenAI(api_key=or_key, base_url="https://openrouter.ai/api/v1")
vectors = []
for doc in docs:
    resp = client.embeddings.create(model="openai/text-embedding-3-large", input=doc["content"])
    vectors.append(resp.data[0].embedding)
```

**Step 3:** Create collection:
```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
client = QdrantClient(host="localhost", port=6333)
coll_name = "narusya_research"
client.create_collection(collection_name=coll_name, vectors_config=VectorParams(size=3072, distance=Distance.COSINE))
```

**Step 4:** Upsert with UUIDs (CRITICAL: must use UUID, not strings):
```python
import uuid
from qdrant_client.models import PointStruct
point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, "your-content-id"))
client.upsert(collection_name=coll_name, points=[
    PointStruct(id=point_id, vector=vectors[0], payload={
        "type": "lorebook", "title": "Document Title",
        "content": docs[0]["content"], "tags": ["research"]
    })
])
```

**Step 5:** Cross-reference to main memory:
```python
client.upsert(collection_name="intelligent_gould_narusya", points=[
    PointStruct(id=str(uuid.uuid5(uuid.NAMESPACE_DNS, "ref-your-doc")), vector=vectors[0], payload={
        "type": "research_note", "title": "Short title",
        "summary": "Brief description", "collection_ref": coll_name
    })
])
```

### Key Pitfalls
1. **String IDs fail** — Always use `uuid.uuid5()` or `uuid.uuid4()`
2. **Dimension mismatch** — Check existing collections before creating
3. **Model mismatch** — Don't mix 3072d and 1536d embeddings in same collection

---

## 3. Investigative Search (qdrant-investigative-search)

Structured approach to investigating claims, accusations, or historical details in conversation logs stored in Qdrant.

### When to Use
- Investigating specific claims about past behavior or statements
- Verifying accusations involving multiple parties
- Tracing patterns of behavior over time
- Resolving "he said/she said" situations with log evidence

### 6-Phase Approach

**Phase 1: Claim Clarification**
1. Extract the specific claim (who said what, when, what evidence)
2. Define search parameters (keywords, timeframe, collections)

**Phase 2: Exact Text Matching**
```python
from qdrant_client import QdrantClient, models
client = QdrantClient(host="localhost", port=6333)

# Search for specific phrase
filter_obj = models.Filter(must=[models.FieldCondition(
    key="text", match=models.MatchText(text="specific_phrase")
)])
points, _ = client.scroll(collection_name="target_collection", scroll_filter=filter_obj, limit=20, with_payload=True)
```

**Phase 3: Semantic Search** (when exact matches fail)
```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
query_vector = model.encode("conceptual search phrase").tolist()
results = client.search(collection_name="target_collection", query_vector=query_vector, limit=10, with_payload=True)
```

**Phase 4: Cross-Reference and Corroborate**
- Check session history for related conversations
- Search multiple collections (memory backups, agent-specific, subject-specific)

**Phase 5: Iterative Refinement**
- If references found but not core claim → search for surrounding context
- If contradictions found → search for explanations
- If too much noise → add more specific terms or use semantic search

**Phase 6: Document Findings**
- Record positive AND negative findings (what wasn't found is important)
- Assess credibility: consistency across sources, temporal plausibility, corroboration

### REST API Access (when execute_code blocked)

```python
import json, urllib.request

def scroll_collection(collection_name, filter_fn=None, max_pages=50):
    results = []
    offset = None
    for page in range(max_pages):
        body = json.dumps({"limit": 100, "with_payload": True, "with_vector": False, "offset": offset}).encode()
        req = urllib.request.Request(f"http://localhost:6333/collections/{collection_name}/points/scroll", data=body, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
        points = data.get('result', {}).get('points', [])
        if not points: break
        offset = data['result'].get('next_page_id')
        for p in points:
            text = p.get('payload', {}).get('text', '')
            if filter_fn is None or filter_fn(text):
                results.append({'id': p['id'], 'text': text[:500]})
        if offset is None: break
    return results
```

---

## 4. Deep Memory Search Escalation (qdrant-deep-search)

When a user asks "do you have memories about X?" or "remember when we talked about X?" and the first search comes up empty, **do not report "nothing found" prematurely.** Escalate through progressively deeper search layers.

### The Escalation Ladder

**Layer 1: `session_search` (Hermes built-in FTS)**
- Fast, covers current profile's session DB
- Good for recent conversations
- Limitation: misses cron sessions, misses old archived conversations

**Layer 2: Qdrant scroll + keyword matching on known collections**
- Scroll each collection, JSON-serialize payloads, lowercase-match keywords
- Check `naru_memories_v2`, `naru_memory`, `hermes_session_memories`, `narusya_entities`
- Limitation: you might not know which collection holds the data

**Layer 3: SQLite direct query on session DB**
```python
import sqlite3
db = sqlite3.connect('/home/adora/.hermes/sessions/state.db')
db.row_factory = sqlite3.Row
cursor = db.cursor()
# Search user messages specifically with word boundaries
cursor.execute('''
    SELECT m.id, m.session_id, m.role, substr(m.content, 1, 400) as snippet
    FROM messages m
    WHERE m.role = 'user'
    AND (m.content LIKE '% term %' OR m.content LIKE '% term,%' OR m.content LIKE '% term.%')
    AND m.session_id != 'current_session_id'
    ORDER BY m.id DESC LIMIT 20
''')
```
- This catches conversations that Qdrant missed (e.g. during the April–June 2026 sync bug window)
- Use word-boundary patterns (`% term %`, `% term,%`, `% term.%`) to reduce false positives
- Exclude the current session to avoid echoing the search query itself

**Layer 4: Full Qdrant scroll across ALL collections**
```python
from qdrant_client import QdrantClient
import json
client = QdrantClient(host='localhost', port=6333)
collections = client.get_collections()
for coll in collections.collections:
    offset = None
    while True:
        results = client.scroll(
            collection_name=coll.name, limit=250, offset=offset,
            with_payload=True, with_vectors=False
        )
        if not results[0]: break
        for point in results[0]:
            payload = point.payload or {}
            text = json.dumps(payload).lower()
            for kw in keywords:
                if kw in text:
                    # Found a match — extract and display
                    content = payload.get('text', payload.get('content', payload.get('message', str(payload))))
                    print(f'{coll.name} | {kw} | {str(content)[:400]}')
                    break
        offset = results[1]
        if offset is None: break
```
- This is the nuclear option — scans every point in every collection
- Essential for finding old SillyTavern conversations stored in `intelligent_gould_narusya` or `intelligent_gould_aegis_terminal`
- **Use regex word-boundary matching** (see "Regex Word-Boundary Matching" above) — the code above still uses substring matching for brevity, but in practice always prefer `re.compile(r'\b(term1|term2)\b', re.IGNORECASE)` over `if kw in text`

### False-Positive Filtering

Short keywords produce substring false positives. After collecting raw matches:

1. **Use regex word boundaries** — `"mech" in text` matches "mechanism". Always use `re.search(r'\bmech\b', text)`.
2. **Distinguish user speech from system text** — Tool outputs, skill content, and error messages contain keywords too. Focus on `role='user'` messages or payload fields like `text`/`content`/`message`.
3. **Scan context around the match** — Read ±200 chars around the keyword to determine if it's a genuine topic reference or incidental.

### When to Stop Escalating

- If Layer 4 (full scan of all collections + SQLite) finds nothing → the memory likely wasn't stored. This happens for:
  - Conversations during Qdrant sync outages (April–June 2026 hash→UUID bug)
  - Conversations that occurred on platforms not archived to Qdrant
  - Pre-Hermes conversations (SillyTavern era) that weren't migrated
- Be honest: "I checked everything and came up empty" is more trustworthy than confabulating a match.

### CRITICAL: Pagination Is Not Optional

`client.scroll(collection_name=X, limit=250)` returns ONLY the first 250 points. If the collection has 4,000+ points, you are scanning <6% of it. **This is the #1 cause of false-negative memory searches.**

Always paginate:
```python
offset = None
while True:
    results = client.scroll(
        collection_name=coll, limit=250, offset=offset,
        with_payload=True, with_vectors=False
    )
    if not results[0]:
        break
    for point in results[0]:
        # process point
        pass
    offset = results[1]  # next page offset
    if offset is None:
        break
```

**Real failure case (2026-06-30):** Searched `intelligent_gould_narusya` (4,142 points) with `limit=200`. Got 2 incidental substring matches, reported "nothing found." User said "wanna double check?" Full paginated scan found 49 genuine matches including core relationship history. The shallow scan missed 98% of the collection.

### Regex Word-Boundary Matching (Not Substring)

Substring matching (`if 'mech' in text`) produces massive false positives — "mechanism", "mechanical", "mechwarrior" all match. Always use regex:

```python
import re
pattern = re.compile(r'\b(mech|mecha|mechs|gundam|evangelion)\b', re.IGNORECASE)
for point in points:
    text = json.dumps(point.payload or {})
    if pattern.search(text):
        # genuine match
```

### Key Lesson: Trust the User's "Wanna Double Check?"

When a user says "wanna double check?" or "look again" after a failed search, **they know something you don't.** Their prompt is a signal that the data exists — your search strategy is incomplete, not the data. Escalate immediately.

**Related pitfall — false confession:** If your first search was shallow and returned nothing, do NOT claim you "fabricated" results when you later find them. The issue was incomplete pagination, not hallucination. Claiming fabrication when the data is real undermines trust. Verify your search methodology before making claims about what exists or doesn't.

---

## 5. Memory Distillation & Backup (qdrant-memory-distillation)

When old Qdrant collections contain valuable data not present in active memory collections, distill and back up the key content into your active collection (`naru_memories_v2` or equivalent).

### When to Use
- Old SillyTavern collections (`intelligent_gould_*`) hold history not in active memory
- User asks "should this be backed up?"
- Content exists only in one collection with no redundancy
- Migrating between memory systems

### Prerequisites: fastembed for Document Embedding

Qdrant's built-in Document embedding lets you upsert text without manually computing vectors. Requires `fastembed`:

```bash
# Install into Hermes venv
uv pip install fastembed --python /home/adora/.hermes/hermes-agent/venv/bin/python
```

### Upsert Pattern

```python
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Document
import uuid

client = QdrantClient(host='localhost', port=6333)

# Model name MUST be the full HF path, not bare name
# WRONG: model='all-MiniLM-L6-v2'
# RIGHT: model='sentence-transformers/all-MiniLM-L6-v2'
point = PointStruct(
    id=str(uuid.uuid4()),
    vector=Document(text="memory text here", model='sentence-transformers/all-MiniLM-L6-v2'),
    payload={
        'text': "memory text here",
        'source': 'archive_backup',
        'tags': ['topic', 'backup'],
        'type': 'archive',
        'consolidated_at': '2026-06-30T15:55:00',
    }
)
client.upsert(collection_name='naru_memories_v2', points=[point])
```

### Distillation Workflow

1. **Exhaustive scan** the old collection (paginated scroll, regex matching — see section 4)
2. **Curate** findings into concise memory entries (not raw dumps — distill the meaning)
3. **Tag** with source collection, topic tags, and `type: archive`
4. **Upsert** to active memory collection using Document embedding
5. **Verify** point count increased by expected amount

### Key Pitfalls
- **Bare model name fails** — `all-MiniLM-L6-v2` raises "not among supported models." Must use `sentence-transformers/all-MiniLM-L6-v2`
- **PEP 668 blocks system pip** — use `uv pip install` targeting the Hermes venv python
- **Don't dump raw conversation text** — distill into searchable memory entries with context
- **Vector dimensions must match** — Document embedding with MiniLM produces 384d. Check collection config before upserting.

**Reference script:** `references/exhaustive-search-and-backup.py` — complete working script for paginated search + memory distillation backup, battle-tested on 2026-06-30.
