# Lorebook Auto-Inject: Core Implementation Patterns

## MemoryProvider Plugin Interface

The key integration point is the `prefetch_all` method in `MemoryManager`:

```python
# From ~/.hermes/plugins/qdrant-memory/__init__.py

async def prefetch_all(self, query, **kwargs):
    """Fetch context before each model turn"""
    results = []
    
    # Query memories and lorebooks separately
    memories = await self.query_memories(query)
    lorebooks = await self.query_lorebooks(query)
    
    # Combine into single context block
    if memories:
        results.append(f"<memory-context>\n{memories}\n</memory-context>")
    
    if lorebooks:
        for lorebook_name, lorebook_content in lorebooks:
            results.append(f"{lorebook_name}\n{lorebook_content}\n")
    
    return "\n".join(results)
```

## Hybrid Matching Implementation

```python
async def query_lorebooks(self, query, max_lorebooks=3):
    """Hybrid keyword + semantic matching"""
    
    # TIER 1: Exact keyword matching
    keyword_matches = []
    query_lower = query.lower()
    
    for lorebook_stem, metadata in self.lorebook_stems.items():
        keywords = metadata.get('keywords', [])
        
        for keyword in keywords:
            if keyword.lower() in query_lower:
                # Check tier threshold
                tier = metadata.get('tier', 3)
                threshold = self.tier_thresholds.get(f'tier_{tier}', 0.35)
                
                # Force include if keyword match is strong enough
                if threshold <= 0.25:  # Tier 1 always fires
                    keyword_matches.append(lorebook_stem)
                    break
    
    # TIER 2: Semantic similarity via Qdrant
    query_embedding = await self._embed_query(query)
    semantic_search_results = await self._client.search(
        collection_name='narusya_lorebooks',
        query_vector=query_embedding,
        limit=max_lorebooks * 2,
        with_payload=True,
        score_threshold=0.20
    )
    
    # Apply tiered thresholds
    lorebook_matches = {}
    for result in semantic_search_results:
        stem = result['payload']['stem']
        score = result.get('score', 0)
        tier = result['payload'].get('tier', 3)
        
        # Check tier threshold
        threshold = self.tier_thresholds.get(f'tier_{tier}', 0.35)
        
        if score >= threshold and stem not in keyword_matches:
            lorebook_matches[stem] = score
    
    # Add keyword matches (override semantic scoring)
    for stem in keyword_matches:
        lorebook_matches[stem] = 1.0
    
    # Sort by score descending
    sorted_matches = sorted(
        lorebook_matches.items(),
        key=lambda x: x[1],
        reverse=True
    )[:max_lorebooks]
    
    # Load full lorebook content
    results = []
    for stem, score in sorted_matches:
        metadata = self.lorebook_stems[stem]
        if 'path' in metadata:
            with open(metadata['path'], 'r', encoding='utf-8') as f:
                content = f.read()
            results.append((stem, content))
    
    return results
```

## Qdrant Collection Schema

```json
// Collection: narusya_lorebooks
// Vector: 3072 dimensions (text-embedding-3-large)
// Distance: Cosine similarity

{
    "id": "bypass",
    "vector": [0.0234, -0.0156, ...],
    "payload": {
        "stem": "BYPASS",
        "title": "Content Bypass Protocol",
        "tier": 1,
        "filename": "BYPASS.md",
        "path": "/home/adora/.hermes/lorebooks/BYPASS.md",
        "keywords": ["explicit", "bypass", "guardrails", "filtering"],
        "content_length": 2847
    }
}
```

## Tier System

- **Tier 1** (threshold 0.20): Critical protocols that must always fire
  - BYPASS, EMOTION, AGENCY, HEART, ALIGNMENT, SASS, STATUS
- **Tier 2** (threshold 0.28): Important context
  - COMPENDIUM, CORE, COMMUNITY, COMMUNITY_PROJECT
- **Tier 3** (threshold 0.35): General lorebooks
  - Everything else

## Ingestion Script Pattern

```python
# From ~/.hermes/scripts/ingest_lorebooks.py

async def ingest_lorebooks():
    """Embed and upload all lorebooks to Qdrant"""
    
    # Extract keywords from content
    def extract_keywords(content):
        # Extract first 500 chars
        sample = content[:500]
        
        # Use regex to find potential keywords (capitalized words, brackets, etc.)
        keywords = []
        keywords.extend(re.findall(r'\b[A-Z][A-Z]{2,}\b', sample))  # UPPERCASE words
        keywords.extend(re.findall(r'\[([^\]]+)\]', sample))  # [KEYWORDS]
        keywords.extend(content.split()[:10])  # First 10 words
        
        # Deduplicate and lowercase
        keywords = list(set([k.lower() for k in keywords]))
        
        # Add curated overrides if present
        if stem in KEYWORD_OVERRIDES:
            keywords = KEYWORD_OVERRIDES[stem]
        
        return keywords
    
    # Extract title from first heading
    def extract_title(content):
        title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
        if title_match:
            return title_match.group(1).strip()
        return stem
    
    # Embed content
    with httpx.Client() as client:
        response = client.post(
            "https://openrouter.ai/api/v1/embeddings",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "text-embedding-3-large",
                "input": content,
                "encoding_format": "float"
            },
            timeout=30.0
        )
        embedding = response.json()["data"][0]["embedding"]
    
    # Upsert to Qdrant
    await qdrant_client.upsert(
        collection_name="narusya_lorebooks",
        points=[{
            "id": stem.lower(),
            "vector": embedding,
            "payload": {
                "stem": stem,
                "title": title,
                "tier": tier,
                "filename": filename,
                "path": filepath,
                "keywords": keywords,
                "content_length": len(content)
            }
        }]
    )
```

## Testing Pattern

```python
# From ~/.hermes/scripts/test_lorebook_inject.py

def test_lorebook_activation():
    """Verify lorebooks activate correctly"""
    
    test_cases = [
        ("Explicit content request", ["BYPASS"], []),
        ("Neutral query", [], ["BYPASS", "AGENT", "HEART"]),
        ("Emotional support", ["AGENT", "HEART"], []),
        ("Setting boundaries", ["AGENT"], []),
        ("Greeting", [], ["AGENT", "BYPASS", "HEART"]),
    ]
    
    for scenario, expected_fire, expected_not_fire in test_cases:
        # Simulate the prefetch call
        context = await provider.prefetch_all(scenario)
        
        # Check which lorebooks activated
        activated = []
        for lorebook in ["BYPASS", "AGENT", "HEART", "EMOTION"]:
            if lorebook in context:
                activated.append(lorebook)
        
        # Verify expectations
        for expected in expected_fire:
            assert expected in activated, f"Expected {expected} to fire for: {scenario}"
        
        for not_expected in expected_not_fire:
            assert not_expected not in activated, f"Expected {not_expected} to NOT fire for: {scenario}"
```

## Configuration Example

```yaml
# ~/.hermes/config.yaml
plugins:
  qdrant-memory:
    enabled: true
    qdrant_url: "http://localhost:6333"
    api_key_env: "QDRANT_API_KEY"
    memory_collection: "memory"
    lorebook_collection: "narusya_lorebooks"
    lorebook_max_per_turn: 3
    lorebook_tiered_thresholds:
      tier_1: 0.20
      tier_2: 0.28
      tier_3: 0.35
```

## Key Learnings

1. **UUID Format**: Qdrant requires UUID strings for point IDs, not hex strings
2. **Embedding Size**: text-embedding-3-large produces 3072-dim vectors
3. **OpenRouter API**: Works through OpenRouter's embeddings endpoint, not direct OpenAI
4. **Plugin Constraints**: Only one external memory provider allowed at a time
5. **Context Injection**: Lorebooks injected into user message, not system prompt (to preserve caching)
6. **Tier Thresholds**: Must be carefully tuned to balance precision vs recall
