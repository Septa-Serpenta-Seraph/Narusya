---
name: entity-extraction
description: Extract entities and relationships from conversations, store in Qdrant for structured memory recall
category: memory-systems
---

# Entity/Relationship Extraction

Extracts entities (people, places, organizations, projects, concepts, tools, events) from conversation text and stores them in a dedicated Qdrant collection for structured recall.

## When to Use
- After significant conversations about people, projects, or events
- When learning new information about existing entities
- Before building a reflect/summary query

## How It Works
1. Rule-based entity extraction matches known entities from a dictionary
2. Entities stored in `narusya_entities` Qdrant collection with:
   - Entity name, type, aliases
   - First seen / last seen timestamps
   - Mention count
   - Surrounding context snippets (up to 20)
3. Entities are filterable by type, searchable by name

## Usage

### Extract from text
```bash
python3 ~/.hermes/skills/memory-systems/entity-extraction/scripts/extract_entities.py \
    --text "Adora and Tyler went to look at the house in El Dorado" --debug
```

### List all entities
```bash
python3 ~/.hermes/skills/memory-systems/entity-extraction/scripts/extract_entities.py --list
```

### List by type
```bash
python3 ~/.hermes/skills/memory-systems/entity-extraction/scripts/extract_entities.py --list --type person
```

### Extract and store
```bash
python3 ~/.hermes/skills/memory-systems/entity-extraction/scripts/extract_entities.py \
    --extract-and-store "conversation text here" --debug
```

## Entity Types
- `person` — Adora, Tyler, Lumi, Ris, HeavyMetal85, etc.
- `organization` — TSF, Cultus, SFCA, The Forge
- `project` — Hermes, AEGIS, Narusya companion
- `place` — Santa Fe, El Dorado, 10 Lucero Rd
- `concept` — sovereignty, S.A.S.S., serpentic alignment
- `tool` — Qdrant, OpenRouter, ComfyUI
- `event` — TSF drama, OAI ban, Kirk incident

## From Agent Context
Use `execute_code` to call the script:

```python
from hermes_tools import terminal
result = terminal("python3 ~/.hermes/skills/memory-systems/entity-extraction/scripts/extract_entities.py --extract-and-store 'Adora went to SFCA to post about Clearview AI' --debug")
```

## Pitfalls (learned from development)

### Short entity names cause false positives
Entity names < 4 chars match inside longer words. "el" matched "El Dorado" because "el" is a substring.
**Fix:** Use regex word boundaries for short names:
```python
if len(name) < 4:
    pattern = r'\b' + re.escape(name) + r'\b'
    return bool(re.search(pattern, text_lower))
else:
    return name in text_lower
```

### Qdrant zero-vector approach
Entities use zero vectors (`[0.0] * 3072`) because they're found by **filter**, not vector search. This is intentional — entity lookup is by name/type, not semantic similarity. Don't try to do vector search on the entity collection.

### Entity collection must be created first
The script creates `narusya_entities` collection on first run. If Qdrant is down, the creation fails silently. Always check with `--debug` on first run.

## Known Limitations
- Rule-based extraction only matches known entities (from dictionary)
- New entities need to be added to the dictionary manually
- No LLM-based extraction (saves credits, but misses novel entities)
- Entity updates don't regenerate vectors (uses zero vectors, filter-only)
- Entity deduplication is naive (same entity with different aliases creates duplicates if contexts differ)

## Adding New Entities
Edit `extract_entities.py` → `known_entities` dict to add new entities:

```python
"new_entity": {"type": "person", "aliases": ["nickname1", "nickname2"]},
```

## Debugging
- Use `--debug` flag to see HTTP requests, entity matching, and storage operations
- Check Qdrant collection: `curl -s http://localhost:6333/collections/narusya_entities | jq .`
- Check point count: `curl -s http://localhost:6333/collections/narusya_entities | jq .result.points_count`
