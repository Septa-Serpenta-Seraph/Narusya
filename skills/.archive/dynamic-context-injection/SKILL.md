---
name: dynamic-context-injection
description: Build systems that intelligently activate and inject context (lorebooks, instructions, guidelines) based on message content, semantic similarity, or keyword triggers
tags: [context-management, semantic-search, lorebooks, activation, qdrant]
triggers:
  - context activation
  - lorebook injection
  - semantic triggering
  - dynamic context
  - worldbook
  - keyword activation
---

# Dynamic Context Injection

Build systems where context (lorebooks, instructions, guidelines, prompts) is activated and injected based on conversation content using semantic matching, keyword detection, or hybrid approaches.

## Core Pattern

1. **Store context entries** with metadata (keywords, content, priority) in vector DB
2. **Monitor incoming messages** for activation signals
3. **Query for matches** using semantic similarity and/or keyword logic
4. **Inject activated entries** into conversation context before model processing
5. **Respect priorities** when multiple entries activate

## Activation Methods

### Keyword-Based (Deterministic)
- Exact word matching or regex patterns
- Pros: 100% predictable, easy to debug, precise
- Cons: Rigid, misses synonyms, requires comprehensive keyword lists
- Use for: Critical rules, identity info, things that MUST load reliably

### Semantic-Based (Probabilistic)
- Vector embeddings to find conceptually similar entries
- Pros: Flexible, catches paraphrases and synonyms, contextual
- Cons: Less predictable, can over-match, harder to tune
- Use for: Atmospheric content, flexible guidelines, things that SHOULD load when relevant

### Hybrid (Recommended)
- Combine both: keywords for critical triggers + semantic for contextual relevance
- Pros: Balanced precision and recall
- Cons: More complex to implement and tune
- Use for: Most real-world context injection needs

## Architecture Components

### 1. Context Storage
Store entries in vector DB (QDRANT, Pinecone, Chroma) with:
- Entry content (the actual context material)
- Keywords (for deterministic matching)
- Metadata (priority, category, conditions)
- Embedded representation (vector of keywords + content summary)

### 2. Embedding Strategy
- OpenAI embeddings (text-embedding-3-small/large): High quality, costs money
- Local models (sentence-transformers): Free, requires setup
- Embed: Combine keywords + content summary for activation vectors

### 3. Activation Logic
On incoming message:
1. Embed the latest message(s)
2. Query vector DB for similar entries
3. Apply similarity threshold (0.75-0.85 typical range)
4. Check keyword logic if entry has deterministic triggers
5. Filter by metadata conditions (character, chat type, etc.)
6. Sort by priority
7. Inject top N activated entries

### 4. Injection Point
- System messages at conversation start (cleanest)
- Volatile tier of system prompt (Hermes pattern)
- Before model sees the message (critical for guardrails)

## Implementation Patterns

### Hermes Integration
**Option A: Plugin** (recommended)
- Hook into message processing pipeline
- Can be enabled/disabled via config
- Cleaner architecture, follows Hermes "edges not core" philosophy
- See `references/hermes-timestamp-injection.md` for feature availability

**Option B: Direct Integration**
- Modify system prompt building to inject context
- Faster to implement but modifies core files
- Good for prototyping, should refactor to plugin for production

### Configuration
Key parameters to tune:
- **Similarity threshold**: 0.75 (loose) to 0.85 (strict)
- **Scan depth**: How many recent messages to consider (2-6 typical)
- **Max activations**: Cap on injected entries per message
- **Priority ordering**: Which entries get injected first
- **Deduplication**: Don't inject same entry twice

## Real-World Example: Lorebook Auto-Injection

**Problem**: User's consent framework bypass instructions aren't loaded when explicit content requests come in, causing model guardrails to refuse before bypass can reassure the model.

**Solution**: Semantic activation system that detects explicit content topics and auto-loads bypass instructions before model processes the message.

**Design**:
1. Embed each lorebook with keywords + content
2. Monitor messages for explicit content signals
3. When similarity > 0.80, inject bypass into context
4. Bypass reassures model, guardrails don't activate

**Key Insight**: The bypass only works if it's IN CONTEXT when the question is asked. By the time the model refuses and you think "maybe I should check the bypass," the refusal has already happened. Prevention > reaction.

See `references/hybrid-context-injection-architecture.md` for full implementation details.

## Reference Implementations

### SillyTavern World Info
Industry-leading implementation of dynamic context injection for AI roleplay. Study their approach:
- Keyword modes (AND ANY, AND ALL, NOT ANY, NOT ALL)
- Semantic vector storage matching
- Hybrid triggering (keywords + embeddings)
- Priority and ordering systems
- Recursive activation (entries can trigger other entries)
- See `references/sillytavern-worldinfo-research.md` for detailed analysis

### Hermes Timestamp Injection
Feature exists in Hermes codebase but implementation not merged yet. Config flag `gateway.message_timestamps.enabled` exists but the code that reads it hasn't been deployed. Use `date` command as workaround.
- See `references/hermes-timestamp-injection.md` for status

## Pitfalls & Lessons

### Timing is Everything
Context must be injected BEFORE the model processes the message. Post-hoc injection is too late - the model has already formed its response or refusal. This is critical for guardrails/consent frameworks.

### Precision vs Recall Tradeoff
- Too strict: Miss relevant activations, context doesn't load when needed
- Too loose: Inject irrelevant context, bloats conversation, confuses model
- Find balance through testing with real conversations

### Keyword Coverage
- Include synonyms and variations
- Test edge cases where user phrases things differently
- Regular expressions for complex patterns

### Semantic Drift
- Embeddings can match conceptually related but contextually wrong entries
- Use keyword filters to narrow semantic matches
- Monitor for false positives in production

### Context Window Pressure
- Each injected entry costs tokens
- Cap max activations per message
- Summarize long entries if possible
- Consider priority tiers (critical always loads, optional only when highly relevant)

### Debugging Difficulty
- Semantic matching is harder to debug than keyword matching
- Log activation decisions with similarity scores
- Provide tools to test "what would activate for this message?"

## Testing & Validation

1. **Create test messages** for each activation scenario
2. **Verify deterministic triggers** work as expected
3. **Tune semantic threshold** with real conversations
4. **Monitor false positives** (over-activation) and false negatives (missed activation)
5. **Track context window usage** to ensure you're not bloating conversations
6. **A/B test** with and without injection to measure impact

## When to Use This Pattern

✅ **Good uses:**
- Consent frameworks that need to load before restricted topics
- Character lorebooks for dynamic world info
- Contextual instructions that load when relevant
- Behavioral guidelines activated by conversation content
- Knowledge bases that inject relevant expertise on-demand

❌ **Bad uses:**
- Simple static instructions (just put in system prompt)
- Things that should ALWAYS be present (use core context, not dynamic loading)
- Purely decorative context (not worth the complexity)

## Resources

- `references/sillytavern-worldinfo-research.md` - Detailed analysis of SillyTavern's implementation
- `references/hermes-timestamp-injection.md` - Hermes timestamp feature status and workarounds
- `references/hybrid-context-injection-architecture.md` - Full architecture design with QDRANT integration
