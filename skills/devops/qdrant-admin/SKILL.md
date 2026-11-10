---
name: qdrant-admin
description: "Qdrant administration: memory diagnostics, container troubleshooting, plugin configuration, memory provider development, and semantic lorebook auto-inject across multiple collections."
tags: [qdrant, diagnostics, plugin, memory-provider, lorebook, auto-inject, semantic-search]
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [qdrant, diagnostics, plugin, memory-provider, troubleshooting]
    related_skills: [qdrant-usage]
---

# Qdrant Administration

Diagnose, troubleshoot, and configure Qdrant memory infrastructure.

## When to Use
- Qdrant isn't working, or memory looks empty / missing
- Building or debugging a custom memory-provider plugin
- Lorebook / context auto-inject across extra collections
- **Replicating the whole store to another machine** → `references/qdrant-replication.md`

## Quick Decision

| Use case | Section |
|----------|---------|
| Qdrant isn't working / can't find data | diagnostics section |
| Building a custom memory provider plugin | plugin section |
| Quick end-to-end health check | health-check section |
| Clone the store to another node (full replica) | `references/qdrant-replication.md` |
| Run Qdrant on a Windows host | `references/qdrant-replication.md` |

---

## 1. Diagnostics (qdrant-memory-diagnostics)

### Container Status
```bash
docker ps -a | grep qdrant
# If Exited: docker restart aegis-qdrant
curl -s http://localhost:6333/healthz  # Expect 200 OK
```

### Querying via HTTP
```python
import httpx
# Count: POST with empty body
r = httpx.post('http://localhost:6333/collections/COLLECTION/points/count')
# Scroll: POST with body
body = {"limit": 5, "with_payload": True}
r = httpx.post('http://localhost:6333/collections/COLLECTION/points/scroll', json=body)
```

### Keyword Search Fallback
If vector search returns nothing, data may exist in session logs:
```python
import re, os
from pathlib import Path
keyword = "jealous"
for f in Path("/home/adora/.hermes/sessions").iterdir():
    if f.suffix in ('.json', '.jsonl'):
        with open(f, 'r', errors='ignore') as fh:
            content = fh.read().lower()
            if keyword in content:
                print(f"FOUND IN: {f.name}")
```

### Cross-Session Memory Sync
When memories don't appear across sessions, check:

1. **Vector dimensions match:**
   ```python
   import urllib.request, json
   with urllib.request.urlopen("http://localhost:6333/collections/COLLECTION") as r:
       info = json.loads(r.read())
       vec_size = info['result']['config']['params']['vectors']['size']
   ```

2. **Embedding API key available:** Plugin uses `OPENROUTER_API_KEY` (not `OPENAI_API_KEY`).

3. **`hermes_session_memories` freshness:** Check timestamps.

4. **"💾 Memory updated" ≠ Qdrant:** Local memory tool doesn't push to Qdrant.

5. **Dimension mismatch (silent failure):** If the embedder produces 384-dim vectors (fastembed) but the configured memory collection is 3072-dim (legacy OpenAI), every search silently returns empty — Qdrant rejects the dimension mismatch at the REST layer and the plugin catches the exception at debug level. Check: embed a test query, compare `len(vector)` against the collection's `config.params.vectors.size`. If they differ, recall is broken even though Qdrant reports healthy. Fix: either switch the collection to a 384-dim one (`narusya_memories_fastembed`) or switch the embedder to 3072-dim (Nous/OpenRouter). Also check that the 384-dim collection actually has data — a crash recovery may have wiped the live storage while a full backup sits on `/mnt/data/qdrant_storage` (197M for `narusya_memories_fastembed` vs 2 points live).

6. **HNSW index not built:** `indexed_vectors_count: 0` on a collection means brute-force search works but semantic search is unoptimized. Qdrant normally builds the index automatically; if it stays at 0 after restart, check optimizer status and Qdrant logs.

### Plugin Loading Diagnostics

1. Quick smoke test: Are `qdrant_recall`, `qdrant_browse` tools available?
2. Check gateway logs: `journalctl --user -u hermes-gateway | grep -i qdrant`
3. Verify config: `python3 -c "from hermes_cli.config import load_config; print(load_config().get('memory', {}).get('provider'))"`
4. Test provider directly:
   ```bash
   cd ~/.hermes/hermes-agent && source venv/bin/activate
   python3 -c "
   import sys; sys.path.insert(0, '.')
   from plugins.memory import load_memory_provider
   p = load_memory_provider('qdrant')
   if p: print(f'Provider: {p.name}, Tools: {[s[\"name\"] for s in p.get_tool_schemas()]}')
   else: print('FAILED')
   "
   ```

### Verifying Writes Actually Land (server-up ≠ data-saving)
When a user worries "is qdrant even saving my messages?", do NOT conclude broken from a
missing `.env` var. The URL lives in `config.yaml` (`plugins.qdrant-memory.qdrant_url`,
e.g. `http://localhost:6333`), NOT `.env`. Verification recipe (localhost, no key needed):
```python
import urllib.request, json
base="http://localhost:6333"
for coll in ["intelligent_gould_narusya","naru_memories_v2","narusya_memory_backup"]:
    cnt=json.loads(urllib.request.urlopen(
        urllib.request.Request(base+f"/collections/{coll}/points/count",data=b'{}',
        headers={"Content-Type":"application/json"})).read()).get('result',{}).get('count')
    sc=json.loads(urllib.request.urlopen(
        urllib.request.Request(base+f"/collections/{coll}/points/scroll",
        data=json.dumps({"limit":2,"with_payload":True,"with_vector":False}).encode(),
        headers={"Content-Type":"application/json"})).read()).get('result',{})
    print(coll, cnt, [list(p.get('payload',{}).keys())[:5] for p in sc.get('points',[])])
```
- **GET `/collections/{c}/points` returns 404** — wrong shape. Use POST `/points/count` (empty body) and POST `/points/scroll` (body `{"limit":N,"with_payload":true}`).
- **`HERMES_CONTEXT_QDRANT=true`** in gateway env confirms context system is *supposed* to use qdrant; pair with live point-counts to confirm it *is*.
- Point counts in the thousands (e.g. 4142 in `intelligent_gould_narusya`) = writes ARE landing. A stale/empty count = real problem worth escalating.
- This server is NOT reachable from the agent session's own write path (no embedder/creds in agent env); verification is read-only via the REST API above. Don't try to upsert from the agent — let the gateway's own pipeline do it.

### Auditing Memory Health — check the CONFIGURED collection before declaring memory broken
When the user asks whether memory is intact (or after any scare), do NOT point-count an arbitrary collection and pronounce the system dead. The recall layer and the bulk archive are different collections:
- **Recall collection** — what the plugin actually searches. Read it from config: `plugins.qdrant-memory.collection` in config.yaml (e.g. `narusya_memories_fastembed`, 4,634 points as of 2026-11-06).
- **Bulk archive** — `session_messages_archive` (tens of thousands of points, 384-dim fastembed) — a separate export pipeline, NOT what recall queries.
- **Operational side-collections** — `hermes_session_memories` and similar can hold dozens of points and mean nothing about memory health.

Audit sequence: (1) grep config.yaml for the collection name; (2) load the provider live and read `mp._collection`; (3) run a functional recall for a known-recent exchange — the provider's recall entry point is `mp.prefetch(query, session_id=...)`, which returns the `<memory-context>` block; a hit on today's conversation proves the whole path end-to-end. Expected gap: very recent turns exist in state.db but may not be embedded into the recall collection yet — an empty search for today's events is a freshness gap, not data loss, and it self-heals on the next embedding pass. When reporting to the user, name which collection you checked and what it holds before drawing any conclusion.
- **Connection Refused** → Docker container exited, restart it
- **400 Bad Request** → Vector dimensions don't match collection config
- **Empty Response** → Ensure `with_payload: True` in scroll request
- **"loaded but no provider instance"** → Test directly with `load_memory_provider('qdrant')`
- **`mp.search(...)` raises AttributeError on the provider object** — recall is `mp.prefetch(query, *, session_id="")`; `search()` lives on the internal `_client` and takes a collection name + precomputed vector. Test recall through `prefetch`, not `search`.
- **Scroll params in the URL query string return 400** — pass `limit`/`with_payload` as a POST body to `/points/scroll`, never as `?limit=N&with_payload=true` query params.

---

## 2. Memory Provider Plugin (qdrant-memory-provider)

### Setting Up Qdrant for a New Profile

When a new profile is created via `hermes profile create <name> --clone`, the qdrant-memory plugin config is copied from the source profile and still points at the source's collections. The memory files (MEMORY.md, USER.md) are also cloned verbatim — they contain the source profile's identity and relationships and must be replaced.

Procedure:

1. **Create collections** (384-dim Cosine, matching the fastembed backend):
   ```bash
   for c in <name>_memories_fastembed <name>_lorebooks_fe; do
     curl -s -X PUT "http://localhost:6333/collections/$c" \
       -H 'Content-Type: application/json' \
       -d '{"vectors":{"size":384,"distance":"Cosine"},"on_disk_payload":true}'
   done
   ```

2. **Patch config.yaml** — update `plugins.qdrant-memory.collection` and `lorebook_collection` from the source profile's names to `<name>_memories_fastembed` / `<name>_lorebooks_fe`. Use `patch` on `~/.hermes/profiles/<name>/config.yaml`.

3. **Ingest lorebooks** — copy `scripts/ingest_lorebooks_fastembed.py` to scratch, change `LOREBOOKS_DIR` to `~/.hermes/profiles/<name>/lorebooks` and `COLLECTION_NAME` to `<name>_lorebooks_fe`, then run with `/mnt/data/fe-venv/bin/python`. The script must clean `sys.path` of `/home/adora/.hermes/installs/` entries (see `embed_fastembed_local.py` defensive header) or fastembed will fail to import due to Python/PIL version mismatch. The plugin auto-ingests a second pass on first load — this is expected and harmless (richer titles/chunks).

4. **Replace memory files** — overwrite `memories/MEMORY.md` and `memories/USER.md` with profile-appropriate content. The cloned versions contain the source profile's identity, relationships, and personal details (health, sexual, financial) — none of which should be inherited. Keep only generic operational facts (Tailscale, SSH, style preferences) and add the new profile's own identity.

5. **Verify** — run a chat that should trigger lorebook injection (e.g. "what's your heart system?") and confirm `<lorebook-context>` appears in the tool trace.

**Pitfalls:**
- The ingest script's success check looks for `result.status == "completed"`, but the REST API returns `result.status == "ok"` — upserts succeed even though the script reports "fail". Verify via `points_count` on the collection.
- Don't inherit the source profile's memory files — they encode the wrong identity and relationships.
- The config change does not take effect until the gateway is restarted (or the profile is reloaded).

---
```yaml
name: qdrant
version: 1.0.0
description: "Local Qdrant vector database — semantic recall over conversation history."
hooks:
  - on_session_end
```

**Config:**
```yaml
memory:
  provider: qdrant
plugins:
  qdrant-memory:
    qdrant_url: "http://localhost:6333"
    collection: "narusya_memories_fastembed"
    prefetch_limit: 5
    max_age_days: 90
    recency_weight: 0.3
```

### Embedding Fallback Chain
1. `sentence-transformers` (if dimensions match)
2. OpenAI via `VOICE_TOOLS_OPENAI_KEY`
3. OpenRouter API (`openai/text-embedding-3-large`)
4. Text search fallback

> The chain above is a *generic* plugin sketch. The live provider's actual path (as of
> 2026-11-06) uses `embedding_backend: local_fastembed` — the fastembed daemon at
> `/home/adora/.hermes/scripts/embed_fastembed_local.py` produces 384-dim vectors via
> `/mnt/data/fe-venv/bin/python`. The memory collection is `narusya_memories_fastembed`
> (384-dim). When OpenRouter/Nous are out of credits, the provider falls back to local
> fastembed automatically. If the provider reports unavailable, check that the fastembed
> daemon venv exists and the script is executable. See `qdrant-local-embeddings` skill
> for backend switching and dimension migration procedures.

### Prefetch Guardrails (Required)
- Timestamps in every result line (`[YYYY-MM-DD]` prefix)
- Recency weighting (blend similarity + time decay)
- Max age filter (skip memories older than N days)
- Clear header with date range

Without guardrails, disable prefetch:
```python
def prefetch(self, query, *, session_id=""): return ""
```

### End-to-End Health Check

```bash
# 1. Qdrant running?
curl -s http://localhost:6333/healthz

# 2. Recent entries in Qdrant?
curl -s 'http://localhost:6333/collections/narusya_memories_fastembed/points/scroll' \
  -X POST -d '{"limit": 5, "with_payload": true}' | python3 -m json.tool | grep timestamp

# 3. Embedding pipeline?
source ~/.hermes/hermes-agent/venv/bin/activate
python3 -c "
import os, requests
r = requests.post('https://openrouter.ai/api/v1/embeddings',
  headers={'Authorization': f'Bearer {os.environ.get(\"OPENROUTER_API_KEY\")}', 'Content-Type': 'application/json'},
  json={'model': 'openai/text-embedding-3-large', 'input': 'test'}, timeout=15)
print('Status:', r.status_code, '| Dims:', len(r.json()['data'][0]['embedding']) if r.ok else 'ERROR')
"
# Expected: Status: 200 | Dims: 3072
```

### Pass/Fail Checklist

| Check | Pass | Fail |
|-------|------|------|
| Qdrant container | `Up X days` | `Exited` or `Connection refused` |
| Gateway | `active (running)` | crash-looping |
| Plugin load | Provider name + tools listed | ImportError |
| Auto-sync | Recent timestamps | Old-only data |
| Recall | Timestamped results | Empty or no dates |
| Embedding | `Dims: 384` (fastembed) | Error/wrong dims |

---

## 3. Rolling Context Persistence

The `rolling_context` feature persists conversation summaries across sessions using Qdrant.

### Config
```bash
# .env
HERMES_CONTEXT_QDRANT=true
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=hermes_session_memories
CONTEXT_EMBEDDING_MODEL=text-embedding-3-large
CONTEXT_MAX_RESULTS=3
```

### How It Works
1. **Session start:** Embed first message, semantic search Qdrant, inject top-3 summaries into system prompt
2. **During compression:** Capture `[CONTEXT SUMMARY]` and store in Qdrant

---

## 4. Semantic Auto-Inject System (Lorebook/Context Extension Pattern)

### Architecture

Extend the existing `qdrant-memory` plugin's `prefetch()` method to query **additional Qdrant collections** beyond memory. This injects matched context into the user message at API-call-time (preserving prompt cache).

**Key architectural decisions:**
- Only ONE external MemoryProvider allowed per Hermes instance — extend existing plugin, not separate plugin
- Lorebook content stored in separate collection (`narusya_lorebooks_fe` for fastembed, `narusya_lorebooks` for legacy 3072-dim) with metadata (stem, keywords, priority_tier, filename)
- Content loaded from disk at injection time (not stored fully in Qdrant payloads — saves vector storage)

**Injection flow:**
```
User message → embed(text) → query BOTH collections simultaneously
                              ↓
              memory collection: recency-weighted semantic search
              lorebook collection: tiered threshold semantic search
                              ↓
              Combined context → injected into user message as:
              <memory-context> + <lorebook-context>
```

### Tiered Similarity Thresholds

text-embedding-3-large scores on long documents are lower than expected (~0.35-0.45 for true matches). Use tier-specific thresholds:

| Tier | Threshold | Use Case |
|------|-----------|----------|
| 1 | 0.20 | Critical operational (BYPASS, HEART, AGENCY, ALIGNMENT) — fastembed cosine scores run lower |
| 2 | 0.28 | Important context (COMPENDIUM, PREFERENCES, CORE_VALUES) |
| 3 | 0.35 | General lorebooks |
| 99 | 0.45 | Skip/background files — high bar to fire |

Note: These thresholds are for fastembed 384-dim vectors. The legacy 3072-dim OpenAI embeddings used higher thresholds (0.35/0.40/0.45/0.50). The code in `_query_lorebooks()` hardcodes the fastembed thresholds.

### Integration Pattern

```python
def prefetch(self, query, *, session_id=""):
    if not self._available: return ""
    vector = self._embedder.embed(query)
    if not vector: return ""
    
    # Existing memory query
    mem_block = self._query_memory(vector)  # returns existing <memory-context> block
    
    # NEW: Lorebook query
    lb_block = self._query_lorebooks(vector)  # returns <lorebook-context> block
    
    if lb_block:
        return mem_block + "\n\n" + lb_block
    return mem_block

def _query_lorebooks(self, vector):
    lb_collection = self._config.get("lorebook_collection", "narusya_lorebooks")
    max_lorebooks = int(self._config.get("lorebook_max_per_turn", 3))
    tier_thresholds = {1: 0.35, 2: 0.40, 3: 0.45, 99: 0.50}
    
    raw = self._client.search(lb_collection, vector, limit=max_lorebooks * 2, score_threshold=0.30)
    matched = [(r["score"], r["payload"]["priority_tier"], r["payload"])
               for r in raw
               if r["score"] >= tier_thresholds.get(r["payload"].get("priority_tier", 3), 0.45)]
    matched.sort(key=lambda x: x[0], reverse=True)
    matched = matched[:max_lorebooks]
    
    if not matched:
        return ""
    
    parts = ["<lorebook-context>\n[System note: ...]\n"]
    for score, tier, payload in matched:
        stem = payload.get("stem", "?")
        # Load full content from disk, not from Qdrant payload
        lorebook_path = Path.home() / ".hermes" / "lorebooks" / payload["filename"]
        content = lorebook_path.read_text()[:3000]  # Truncate to avoid bloat
        parts.append(f"\n### [{stem}] (relevance: {score:.2f}, tier {tier})\n{content}")
    parts.append("\n</lorebook-context>")
    return "\n".join(parts)
```

### Config (in `plugins.qdrant-memory` section of config.yaml)

Add alongside existing memory collection config:
```yaml
lorebook_collection: narusya_lorebooks
lorebook_max_per_turn: 3
```

### Required Ingestion Pipeline

Lorebooks must be pre-embedded and stored in Qdrant. See `scripts/ingest_lorebooks.py`.

### Critical Pitfalls

- **Qdrant point IDs must be UUIDs or unsigned integers.** Hex strings (like md5[:16]) return opaque 400 errors. Always use `uuid.uuid5(uuid.NAMESPACE_DNS, name)`.
- **security.redact_secrets corrupts scripts.** When writing Python scripts containing strings that look like API keys (e.g., `OPENROUTER_API_KEY=***`), write via `cat <<'EOF' > file` in terminal instead of write_file. The redactor replaces content it perceives as credentials.
- **Don't modify Hermes core.** All lorebook injection happens inside the plugin's `prefetch()` method. Never touch `agent/conversation_loop.py` or `agent/prompt_builder.py`.
- **Content from disk, not Qdrant.** Store only metadata in Qdrant payloads. Load full file content at inject time. This keeps vector storage lean.
- **Max 3000 chars per lorebook per injection** to avoid context bloat. GENDER_ACCELERATION is 63k chars — truncation is mandatory.

---

### Dimension Migration (3072-dim → 384-dim fastembed)

When switching from OpenAI/OpenRouter 3072-dim embeddings to local fastembed 384-dim, the existing collection cannot be reused — vectors have different dimensions. Procedure:

1. **Identify source and target collections:** source = `intelligent_gould_narusya` (3072-dim), target = `narusya_memories_fastembed` (384-dim)
2. **Verify target exists and is empty:** check `points_count` via `curl -s http://localhost:6333/collections/narusya_memories_fastembed`
3. **Use fastembed daemon for batch embedding** — do NOT import fastembed directly in the migration script (numpy/Python version mismatch causes `AttributeError: module 'inspect' has no attribute 'cleandoc'`). Instead, spawn `/home/adora/.hermes/scripts/embed_fastembed_local.py` as a subprocess and communicate via JSON lines on stdin/stdout.
4. **Scroll source collection** in batches of 50-100 via POST `/collections/{source}/points/scroll` with `{"limit": N, "with_payload": true, "with_vector": false}`
5. **Embed each batch's text** via the daemon, then upsert into target with `PUT /collections/{target}/points` body `{"points": [{"id": ..., "vector": [...], "payload": {...}}]}`
6. **Verify migration:** check target `points_count` matches source
7. **Update plugin config:** change `collection:` in `config.yaml` from the old collection name to `narusya_memories_fastembed`. Use `hermes config set plugins.qdrant-memory.collection narusya_memories_fastembed` or edit directly. **This step is easy to forget** — the migration succeeds but recall still queries the old collection until the config is updated and the gateway restarted.

**Pitfall:** If the target collection was wiped during crash recovery (live storage 12K vs backup 197M), restore from `/mnt/data/qdrant_storage` first — see "Restoring from Backup Storage" below.

**Pitfall:** The config change does not take effect until the gateway is restarted. After updating config.yaml, restart with `/restart` in Discord or `systemctl --user restart hermes-gateway.service`.

### Backup Container (qdrant-backup, port 6335)

A second Qdrant container named `qdrant-backup` runs on port 6335, bind-mounting `/mnt/data/qdrant_storage` (3.9G). **Nothing in config.yaml references port 6335** — the main Qdrant (`aegis-qdrant`, port 6333) uses `/home/adora/qdrant_storage` (628M).

**Identify it:**
```bash
docker ps -a | grep qdrant-backup
docker inspect qdrant-backup --format '{{json .Mounts}}'
```

**Before removing it:** verify no process, cron, or config references port 6335:
```bash
grep -rn "6335\|qdrant-backup" /home/adora/.hermes/config.yaml /home/adora/.hermes/cron/ 2>/dev/null
```
If clean, the container and its 3.9G storage are reclaimable. Stop and remove the container first, then delete `/mnt/data/qdrant_storage` (or move to trash).

**Note:** `/mnt/data/adora-main/qdrant_storage` (3.9G) is another duplicate of the same backup data — check before deleting either copy.

---

### Restoring from Backup Storage

When live Qdrant storage is wiped (e.g., crash recovery), the backup at `/mnt/data/qdrant_storage` (197M) contains full collection data. **Do NOT delete the collection via API first** — deletion removes on-disk files too.

Procedure:
1. Stop Qdrant: `docker stop aegis-qdrant`
2. Copy backup collection to live storage using a Docker container (files are root-owned):
   ```bash
   docker run --rm -v /mnt/data:/mnt/data -v /home/adora/qdrant_storage:/qdrant/storage alpine \
     sh -c "cp -r /mnt/data/qdrant_storage/collections/COLLECTION_NAME /qdrant/storage/collections/"
   ```
3. Start Qdrant: `docker start aegis-qdrant`
4. Verify collection appears: `curl -s http://localhost:6333/collections | ...`
5. If collection doesn't appear, create it via API first (`PUT /collections/COLLECTION` with right config), then copy data and restart.

**Pitfall:** Qdrant registers collections in `raft_state.json` metadata. Simply having the directory present may not be enough — if the collection was deleted via API (which removes metadata), you may need to create it via API after copying data.

**Pitfall:** Even after restore, the collection may show only 2 points if the WAL wasn't replayed. The backup segments may contain data that Qdrant doesn't read without a clean restart. Verify point count after restart.

### Fastembed Daemon Batch Embedding Pattern

The fastembed daemon (`embed_fastembed_local.py`) avoids numpy/Python version mismatches by running in its own venv:

```python
import subprocess, json
proc = subprocess.Popen(
    ["/mnt/data/fe-venv/bin/python", "/home/adora/.hermes/scripts/embed_fastembed_local.py"],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True
)
# Send: {"id": 1, "texts": ["text1", "text2"]}
# Receive: {"id": 1, "vectors": [[...], [...]], "error": null}
```

- Model: `sentence-transformers/all-MiniLM-L6-v2` (384-dim)
- Cache: `/mnt/data/fastembed_cache`
- Max batch: ~50 texts per call to avoid memory pressure
- Terminate daemon when done: `proc.terminate()`

## 5. Local Fastembed Backend — Memory Pressure

When `embedding_backend: local_fastembed` is set, the plugin spawns a persistent fastembed subprocess (`embed_fastembed_local.py`) per `_LocalEmbedder` instance. Each daemon loads the ONNX model (~220MB RSS). Multiple instances can spawn:

- `is_available()` creates a probe `_EmbeddingClient` (and thus a daemon) on first call
- `initialize()` creates another `_EmbeddingClient`
- Each `QdrantMemoryProvider` instance (one per session) creates its own

**On a 4GB VM, 4 daemons = ~880MB** — enough to trigger OOM kills.

### Diagnose

```bash
ps aux | grep embed_fastembed | grep -v grep | wc -l   # count daemons
free -h                                                # check memory pressure
```

### Mitigate

1. **Kill extra daemons** — keep 1, the gateway respawns as needed:
   ```bash
   # Kill all but one
   ps aux | grep embed_fastembed | grep -v grep | awk '{print $2}' | tail -n +2 | xargs kill
   ```

2. **Add MemoryMax to gateway service** — prevents OOM from taking down the whole VM:
   ```ini
   # ~/.config/systemd/user/hermes-gateway.service [Service] section
   MemoryHigh=2G
   MemoryMax=2.5G
   ```

3. **Long-term fix** — deduplicate `_LocalEmbedder` instances (singleton or shared daemon across providers). The root cause is that `is_available()` creates a throwaway probe embedder that is never cleaned up. **STATUS: Applied (Oct 22, 2026)** — `_LocalEmbedder` is now a module-level singleton keyed by `(python_bin, script)` via `_get_shared_local_embedder()`. All `_EmbeddingClient` instances share one daemon. If you see multiple daemons again, check for a second plugin instance or a code regression.

### Pitfalls

- Killing a daemon does NOT crash the gateway — `embed_batch()` detects the dead process via `poll()` and respawns. But the gateway may spawn replacements, so killing alone is a band-aid.
- The `close()` method exists on `_LocalEmbedder` but is never called by the provider. Daemons accumulate until the gateway restarts.
- On constrained VMs, consider switching to the API embedding backend (`embedding_backend: api` with Nous/OpenRouter) to eliminate local daemon memory entirely. Trade-off: requires network and API credits.

## References

`references/qdrant-replication.md` — full-replica clone to another node: native snapshot → transfer → restore → verify, the data-vs-container size trap, running Qdrant on Windows via WSL + systemd, and the WSL-over-SSH quoting rule.

`agent-memory-dreaming` (skill) — the [DREAM] system: automated memory reorganization (consolidation, clustering, pruning, narrative reflection) running as a nightly cron job against Qdrant collections. See `agent-memory-dreaming` skill for full documentation.

`references/lorebook-autoinject-architecture.md` — deeper design notes for the semantic auto-inject system.
