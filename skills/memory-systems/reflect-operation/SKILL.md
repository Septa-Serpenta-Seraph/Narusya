---
name: reflect-operation
description: Cross-memory synthesis — search Qdrant, entities, and persistent memory to find connections around a topic
category: memory-systems
---

# Reflect Operation

Cross-memory synthesis that searches across all of Narusya's memory sources (Qdrant conversations, entity store, persistent MEMORY) and returns structured findings for the agent to synthesize.

## When to Use
- User asks "what do you know about X?" or "remember when we talked about X?"
- Need to connect dots across multiple conversations/sessions
- Building context before responding to a complex question
- Investigating entity relationships (who knows who, what's connected to what)

## How It Works
1. **Conversation search** — Scrolls Qdrant main collection, text-matches topic keywords
2. **Entity search** — Looks up entities related to the topic
3. **Connection mapping** — Finds co-occurring entities (who/what appears together)
4. **Memory section scan** — Reads persistent MEMORY for relevant entries
5. Returns structured findings for agent synthesis

## Usage

### Reflect on a topic
```bash
python3 ~/.hermes/skills/memory-systems/reflect-operation/scripts/reflect.py \
    --topic "Adora's relationship with Tyler" --verbose
```

### Look up an entity
```bash
python3 ~/.hermes/skills/memory-systems/reflect-operation/scripts/reflect.py \
    --entity "adora"
```

### Show entity connections
```bash
python3 ~/.hermes/skills/memory-systems/reflect-operation/scripts/reflect.py \
    --entity "adora" --connections
```

### JSON output (for programmatic use)
```bash
python3 ~/.hermes/skills/memory-systems/reflect-operation/scripts/reflect.py \
    --topic "SFCA" --json
```

### Debug mode
```bash
python3 ~/.hermes/skills/memory-systems/reflect-operation/scripts/reflect.py \
    --topic "house" --debug --verbose
```

## From Agent Context
Use `execute_code` to call the script:

```python
from hermes_tools import terminal
result = terminal("python3 ~/.hermes/skills/memory-systems/reflect-operation/scripts/reflect.py --topic 'Clearview AI' --verbose")
```

## Output Structure
```json
{
    "topic": "query topic",
    "timestamp": "ISO timestamp",
    "conversations": [{"id", "text", "timestamp", "speakers", "match_score"}],
    "entities": [{"name", "type", "mentions", "first_seen", "last_seen", "contexts"}],
    "related_entities": [{"name", "type", "co_occurrences"}],
    "memory_entries": ["relevant lines from MEMORY section"]
}
```

## Pitfalls (learned from development)

### Qdrant `order_by` requires a range index
Using `order_by: {key: "timestamp"}` in scroll requests fails with:
```
Wrong input: No range index for `order_by` key: `timestamp`. Please create one.
```
**Fix:** Don't use `order_by` unless you've created a payload index. Instead, paginate with `offset` and sort results in Python.

### Pagination approach
```python
all_points = []
next_offset = None
while True:
    data = {"limit": 100, "with_payload": True}
    if next_offset:
        data["offset"] = next_offset
    response = qdrant_request("POST", f"/collections/{col}/points/scroll", data)
    points = response.get("result", {}).get("points", [])
    all_points.extend(points)
    next_offset = response.get("result", {}).get("next_page_offset")
    if not next_offset or not points:
        break
```

### Timestamp field can be int or string
Qdrant timestamps might be stored as Unix epoch (int) or ISO string. When displaying, always convert to string first:
```python
ts = str(c['timestamp'])[:10]  # Not c['timestamp'][:10]
```

### Memory file path is environment-specific
The persistent MEMORY is in the system prompt, not a file. The script checks `~/.hermes/memory/active.md` and falls back to the memory directory. If neither exists, memory search returns empty — this is expected, not an error.

### Text matching vs semantic search
The reflect script does text-based matching (keyword presence), not semantic similarity. For semantic search, the agent must use the `qdrant_search` tool separately and merge results.

## Limitations
- **No semantic search** — Uses text matching, not embeddings. For semantic search, use `qdrant_search` tool directly from agent context.
- **Limited scroll** — Default 5 pages × 100 = 500 points. Increase `max_pages` for broader search.
- **Memory file may not exist** — Falls back to checking memory directory.

## Combining with Other Tools
Best results come from combining reflect with:
- `qdrant_search` — For semantic similarity (agent tool, needs credits)
- `session_search` — For cross-session keyword search (agent tool)
- `memory` tool — For reading persistent MEMORY section (agent tool)

The reflect script handles the Qdrant text-search and entity lookup; the agent handles semantic search and final synthesis.

## Debugging
- `--debug` shows all HTTP requests to Qdrant
- `--verbose` shows full content of found items
- Check Qdrant health: `curl -s http://localhost:6333/collections | jq .`
- Check entity collection: `curl -s http://localhost:6333/collections/narusya_entities | jq .result.points_count`
