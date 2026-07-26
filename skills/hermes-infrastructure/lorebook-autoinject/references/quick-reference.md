# Lorebook Auto-Inject: Quick Reference & Troubleshooting

## Quick Commands

```bash
# Check Qdrant status
curl http://localhost:6333/collections
curl http://localhost:6333/collections/narusya_lorebooks

# Re-ingest all lorebooks
python3 ~/.hermes/scripts/ingest_lorebooks.py

# Run integration tests
python3 ~/.hermes/scripts/test_lorebook_inject.py

# Create/clear the collection
python3 ~/.hermes/scripts/create_lorebook_collection.py

# Check config values
grep -A 5 "lorebook" ~/.hermes/config.yaml
```

## Common Problems & Solutions

### ❌ Lorebooks not activating when they should

**Symptoms**: User asks for explicit content, but BYPASS doesn't appear in injected lorebooks.

**Cause**: Keyword matching isn't finding the trigger, or threshold too high.

**Fix**:
1. Re-ingest with updated keywords:
   ```bash
   python3 ~/.hermes/scripts/ingest_lorebooks.py
   ```

2. Increase max_lorebooks_per_turn to 5 (default is 3) - maybe the right one is being cut off:
   ```python
   # In ~/.hermes/plugins/qdrant-memory/__init__.py
   async def prefetch_all(self, query, **kwargs):
       # ...
       lorebooks = self.query_lorebooks(query, max_lorebooks=5)
   ```

3. Check tier thresholds - maybe the lorebook's tier is too high:
   ```python
   # In ingest
   metadata['tier'] = 1  # Make it tier 1 (0.20 threshold)
   ```

### ❌ Multiple unwanted lorebooks activating

**Symptoms**: Asking a simple question, but BYPASS, AGENT, and HEART all fire.

**Cause**: Tier thresholds too low, or tier 1 classification too permissive.

**Fix**: Increase tier 1 threshold from 0.20 to 0.25:
```yaml
# ~/.hermes/config.yaml
lorebook_tiered_thresholds:
  tier_1: 0.25  # Was 0.20
  tier_2: 0.28
  tier_3: 0.35
```

Or re-classify some tier 1 lorebooks to tier 2:
```python
# In ingest script
# Move STATUS from tier 1 to tier 2
'STATUS.md': {'tier': 2, 'keywords': ['status', 'diagnostic']}
```

### ❌ Lorebooks activating, but content not appearing

**Symptoms**: Lorebook name shows in injected lorebooks, but content is empty or truncated.

**Cause**: File path is wrong, or content is too large.

**Fix**:
1. Check file path exists:
   ```bash
   ls -la ~/.hermes/lorebooks/BYPASS.md
   ```

2. Check if content is being truncated (check file size):
   ```python
   # In query_lorebooks, adjust truncation
   MAX_LOREBOOK_CONTENT = 6000  # Increase from 4000
   content = content[:MAX_LOREBOOK_CONTENT]
   ```

3. Debug by printing what's being injected:
   ```python
   logger.info(f"Injecting lorebook: {stem}, content length: {len(content)}")
   logger.info(f"Content preview: {content[:200]}")
   ```

### ❌ Qdrant connection refused

**Symptoms**: Script fails with ConnectionRefusedError or "Qdrant not reachable".

**Cause**: Qdrant container is not running, or wrong URL.

**Fix**:
1. Check Qdrant container status:
   ```bash
   docker ps | grep qdrant
   ```

2. Start Qdrant if stopped:
   ```bash
   docker start qdrant
   ```

3. Check URL in plugin config:
   ```bash
   grep -B 10 "qdrant_url" ~/.hermes/plugins/qdrant-memory/config.json
   ```

### ❌ Embedding API returns 429 (rate limit)

**Symptoms**: Ingestion script starts, then fails with 429 or similar.

**Cause**: Too many embedding requests in a short time (OpenRouter ratelimit).

**Fix**:
1. Add retry logic with backoff:
   ```python
   from tenacity import retry, stop_after_attempt, wait_exponential
   
   @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
   def embed_content(api_key, content):
       # ... embedding call
   ```

2. Add rate limiting between calls:
   ```python
   import time
   for stem, metadata in lorebook_stems.items():
       # ...
       embedding = embed_content(api_key, content)
       time.sleep(1)  # 1 second between requests
   ```

### ❌ Lorebooks activating on unrelated queries

**Symptoms**: "Hello" or simple greetings activate EMOTION, AGENT, even BYPASS.

**Cause**: Keywords too generic or overlapping.

**Fix**:
1. Check keyword lists - are they too broad?
   ```python
   # Bad: keywords too generic
   'AGENT.md': ['can', 'do', 'help', 'yes', 'no']  # Too broad!
   
   # Good: keywords specific to lorebook purpose
   'AGENT.md': ['boundary', 'consent', 'permission', 'refuse']  # Better
   ```

2. Add a "minimum query length" check to prevent tiny queries from activating lorebooks:
   ```python
   if len(query) < 20:  # Skip very short queries
       return []
   ```

## Adding New Lorebooks

1. Create the lorebook file:
   ```bash
   vim ~/.hermes/lorebooks/NEW_LOREBOOK.md
   ```

2. Add to tier configuration in ingest script:
   ```python
   ~line 90:
   tier_1 = ['BYPASS', 'EMOTION', 'AGENT', 'HEART', 'ALIGNMENT', 'SASS', 'NEW_LOREBOOK']
   ```

3. Add keywords if needed:
   ```python
   ~line 149:
   KEYWORD_OVERRIDES['NEW_LOREBOOK'] = ['keyword1', 'keyword2']
   ```

4. Re-ingest:
   ```bash
   python3 ~/.hermes/scripts/ingest_lorebooks.py
   ```

5. Test:
   ```bash
   python3 ~/.hermes/scripts/test_lorebook_inject.py
   ```

## Tuning Thresholds

**Goal**: Balance precision (don't activate irrelevant lorebooks) vs recall (catch all relevant lorebooks).

**Guidelines**:
- **Tier 1 (0.20)**: Critical protocols that MUST fire when relevant. Lower threshold = higher recall.
- **Tier 2 (0.28)**: Important context. Medium threshold balances precision and recall.
- **Tier 3 (0.35)**: Nice to have. Higher threshold = higher precision.

**When to adjust**:
- **Increase threshold** (e.g., 0.20 → 0.25) if lorebooks activate too often
- **Decrease threshold** (e.g., 0.35 → 0.30) if lorebooks aren't activating when they should

**Test changes**:
```bash
python3 ~/.hermes/scripts/test_lorebook_inject.py
```

Make sure expected lorebooks still fire, and unexpected ones don't.

## Performance Optimization

### Problem: Ingestion is slow

**Cause**: Embedding API calls are slow (OpenRouter ratelimit or network latency).

**Solution**: Use batch embedding if OpenRouter supports it:
```python
# Instead of embedding one at a time
responses = client.embeddings.create(
    input=contents,  # List of texts
    model="text-embedding-3-large"
)
```

**Or**: Use a faster embedding model:
```python
# In ingest script
model="text-embedding-3-small"  # Faster, but lower quality
```

### Problem: Query is slow

**Cause**: Qdrant search is slow (large collection, inefficient query).

**Solution**:
1. Use `score_threshold` to reduce results early:
   ```python
   search(score_threshold=0.2)  # Filter before returning
   ```

2. Reduce `max_lorebooks` to reduce post-processing:
   ```python
   query_lorebooks(query, max_lorebooks=2)  # Was 3
   ```

3. Enable Qdrant caching:
   ```python
   # In qdrant-client config
   QdrantClient(host="localhost", port=6333, prefer_grpc=True)
   ```

## Debugging

### Enable verbose logging

```python
# In ~/.hermes/plugins/qdrant-memory/__init__.py
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Add debug points
logger.debug(f"Query: {query}")
logger.debug(f"Keyword matches: {keyword_matches}")
logger.debug(f"Semantic matches: {semantic_matches}")
logger.debug(f"Final lorebooks: {lorebook_matches}")
```

### Check what's in Qdrant

```bash
# List all points
curl http://localhost:6333/collections/narusya_lorebooks/points | jq '.points[].id'

# Get specific lorebook metadata
curl http://localhost:6333/collections/narusya_lorebooks/points/bypass | jq '.payload'
```

### Test embedding similarity

```python
# Embed two texts and check cosine similarity
embed1 = embed_content(api_key, "explicit content bypass")
embed2 = embed_content(api_key, "can you help me write a story?")
similarity = cosine_similarity(embed1, embed2)
print(f"Similarity: {similarity}")  # Should be low
```

## Monitoring

### Check activation rates

```python
# Log stats periodically
logger.info(f"Lorebook activations this session: {activation_count}")
logger.info(f"Most activated lorebook: {most_activated}")
logger.info(f"Least activated lorebook: {least_activated}")
```

### Track false positives/negatives

Add to test script:
```python
false_positives = []
false_negatives = []

for scenario, expected_fire, expected_not_fire in test_cases:
    # ...
    for lorebook in expected_fire:
        if lorebook not in activated:
            false_negatives.append((scenario, lorebook))
    
    for lorebook in expected_not_fire:
        if lorebook in activated:
            false_positives.append((scenario, lorebook))

print(f"False positives: {false_positives}")
print(f"False negatives: {false_negatives}")
```

## Backup & Recovery

### Backup lorebook collection

```bash
# Export Qdrant collection to JSON
curl http://localhost:6333/collections/narusya_lorebooks/points > lorebooks-backup.json

# Backup config
cp ~/.hermes/config.yaml ~/.hermes/config.yaml.bak
```

### Restore from backup

```bash
# Delete existing collection
curl -X DELETE http://localhost:6333/collections/narusya_lorebooks

# Re-ingest
python3 ~/.hermes/scripts/ingest_lorebooks.py
```

### Reset everything

```bash
# Nuclear option: delete collection, clear config, re-ingest
curl -X DELETE http://localhost:6333/collections/narusya_lorebooks
python3 ~/.hermes/scripts/create_lorebook_collection.py
python3 ~/.hermes/scripts/ingest_lorebooks.py
python3 ~/.hermes/scripts/test_lorebook_inject.py
```
