# Core Implementation — Key Learnings

## Architecture Decisions

1. **UUID Format**: Qdrant requires UUID strings for point IDs, not hex strings. NEVER use `hash()` — it produces signed, unstable integers that Qdrant rejects with 400 error. Always use `uuid.uuid4()`.

2. **Embedding Size**: text-embedding-3-large produces 3072-dim vectors. text-embedding-3-small produces 1536-dim.

3. **OpenRouter API**: Works through OpenRouter's embeddings endpoint (`https://openrouter.ai/api/v1/embeddings`), not direct OpenAI. Requires `OPENROUTER_API_KEY` in `.env`.

4. **Plugin Constraints**: Hermes only allows one external memory provider at a time. Our qdrant-memory plugin handles both conversation memory AND lorebook matching.

5. **Context Injection**: Lorebooks injected into user message (via `<memory-context>` tags), NOT system prompt. This preserves prompt caching — system prompt modifications break the cache.

6. **Hybrid Matching**: Keyword triggers (exact substring) + semantic similarity (Qdrant vector search). Keywords always win over semantic matches. This ensures BYPASS fires reliably on "explicit" and HEART fires on "feelings".

7. **Curated Keywords**: Auto-extracted keywords are insufficient for critical lorebooks. Use `KEYWORD_OVERRIDES` dict in `ingest_lorebooks.py` for BYPASS, HEART, EMOTION, AGENCY, etc.

## Qdrant Sync Bug Fix (2026-06-26)

**Bug**: `hash()` produces signed integers but Qdrant requires unsigned integers or UUIDs for point IDs. The fallback `str(hash(text+str(ts)))` in `_process_sync_item` silently failed for 2+ months (April 19 → June 26).

**Root cause**: Line 302 in `plugins/qdrant-memory/__init__.py`:
```python
point_id = str(uuid.uuid4()) if "uuid" in globals() else str(hash(text + str(ts)))
```
`"uuid" in globals()` is **False** because `uuid` is imported as a module, not into globals. So it always fell back to `hash()`.

**Fix**:
```python
import uuid as _uuid_mod
point_id = str(_uuid_mod.uuid4())
```

**Impact**: 2+ months of conversations were NOT stored in Qdrant. Memory system appeared to work (no errors logged) but writes silently failed.

## Tier Thresholds

Must be carefully tuned:
- Tier 1 (0.20): BYPASS, HEART, EMOTION, AGENCY, ALIGNMENT, SASS, STATUS — critical protocols
- Tier 2 (0.28): COMPENDIUM, CORE_VALUES, COMMUNITY, GENDER_ACCELERATION — important context
- Tier 3 (0.35): General lorebooks — nice to have

**Calibration method**: Test with representative queries, check which lorebooks fire, adjust thresholds until precision/recall is balanced.

## Verification Protocol

Before the daemon engages:
- **Usernames**: Make sure @ mentions use correct `<@ID>` format. If unsure, don't ping.
- **Claims**: Don't state facts you haven't actually confirmed.
- **Context**: Make sure you're responding to the right conversation in the right channel.
- **Value**: If the only reason to post is "it's been a while," stay silent.
- **Knowledge**: If you don't know enough to add something wise, stay quiet.
