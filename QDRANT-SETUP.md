# Qdrant Memory System Setup Guide

This document describes Narusya's Qdrant-based memory architecture for Hermes Agent. Lumi (and other agents) can replicate this setup.

## Architecture Overview

- **Qdrant**: Running locally on `localhost:6333`
- **Embedding model**: `dunzhang/stella_en_1.5B_v5` (3072d, Cosine similarity)
- **Memory plugin**: `qdrant-memory` (Hermes built-in plugin)
- **Collections**: One per agent, named `intelligent_gould_<agentname>`

## Config.yaml Settings

Add to your `~/.hermes/config.yaml`:

```yaml
memory:
  memory_enabled: true
  user_profile_enabled: true
  memory_char_limit: 4400
  user_char_limit: 2750
  provider: qdrant
  flush_min_turns: 6
  nudge_interval: 10

  qdrant-memory:
    qdrant_url: http://localhost:6333
    collection: intelligent_gould_<YOUR_AGENT_NAME>
    prefetch_limit: 5
    max_age_days: 90
    recency_weight: 0.3
  enabled:
    - qdrant
```

Replace `<YOUR_AGENT_NAME>` with your agent's identifier (e.g., `lumi`).

## Collection Schemas

### Primary Memory Collection (`intelligent_gould_<name>`)

```json
{
  "points_count": "grows over time",
  "vector_size": 3072,
  "distance": "Cosine",
  "on_disk_payload": true
}
```

### Session Archive (`session_messages_archive`)

```json
{
  "vector_size": 384,
  "distance": "Cosine"
}
```

Uses `sentence-transformers/all-MiniLM-L6-v2` for embeddings. This is the "dumb" archive — all messages stored but not semantically rich.

### Entity Collection (`narusya_entities`)

Stores extracted entities and relationships from conversations.

## Setting Up From Scratch

### 1. Install and Run Qdrant

```bash
docker run -d --name qdrant -p 6333:6333 \
  -v ~/.hermes/qdrant:/qdrant/storage \
  qdrant/qdrant
```

### 2. Install the Memory Plugin

The `qdrant-memory` plugin is built into Hermes Agent. Ensure it's enabled in config (`enabled: [qdrant]`).

### 3. Create Your Collection

The collection is created automatically on first use. Or manually:

```python
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance

client = QdrantClient(host='localhost', port=6333)
client.create_collection(
    collection_name='intelligent_gould_lumi',
    vectors_config=VectorParams(size=3072, distance=Distance.COSINE),
)
```

### 4. Populate Initial Data

Use the `narusya-local-archive` skill or manually upsert documents:

```python
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

client = QdrantClient(host='localhost', port=6333)
model = SentenceTransformer('dunzhang/stella_en_1.5B_v5')

text = "Your memory content here..."
vector = model.encode(text).tolist()

client.upsert(
    collection_name='intelligent_gould_lumi',
    points=[{
        'id': 1,
        'vector': vector,
        'payload': {'text': text, 'timestamp': '2026-05-22T00:00:00'}
    }]
)
```

## Files in This Repo

- `config.yaml` — Current Hermes config with Qdrant settings (API keys stripped)
- `qdrant-schemas.json` — Collection schemas for all Narusya/Lumi collections
- `QDRANT-SETUP.md` — This file
- `lorebooks/` — All lorebook markdown files
- `skills/` — Installed skills
- `backup.sh` — Automated backup script

## Notes

- The `stella_en_1.5B_v5` model requires ~6GB VRAM and takes time to load on CPU. Be patient on first use.
- For CPU-only systems, consider running Qdrant in a Docker container with GPU passthrough.
- The `session_messages_archive` (384d, MiniLM) is separate from the main memory collection. Archive all session messages there for completeness, but search the 3072d collection for semantic recall.
- Max age of 90 days prevents the collection from growing infinitely. Older memories resurface through re-embedding in the session archive.
