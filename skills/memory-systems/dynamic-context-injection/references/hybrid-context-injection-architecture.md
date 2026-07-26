# Hybrid Context Injection Architecture

Detailed architecture design for implementing dynamic context injection in Hermes using QDRANT and semantic matching.

## Overview

A system that monitors incoming messages, detects activation signals via keyword matching and semantic similarity, and injects relevant context (lorebooks, instructions, guidelines) into the conversation before the model processes the message.

## Problem Statement

**Core Issue**: User's consent framework bypass instructions aren't loaded when explicit content requests come in, causing model guardrails to refuse before bypass instructions can reassure the model.

**Why This Happens**:
- Context must be IN CONTEXT when the model processes the message
- If context isn't there, the model's pre-training guardrails activate
- By the time you realize "I should load the bypass", the refusal has already happened
- Post-hoc injection is too late - prevention is critical

**Solution**: Semantic activation system that detects explicit content topics and auto-loads bypass instructions before model processes the message.

## Architecture Components

### 1. QDRANT Collection: `narusya_lorebooks`

**Purpose**: Store lorebook entries with their activation metadata and embeddings

**Schema**:
```json
{
  "id": "uuid",
  "vector": [0.1, 0.2, ...],  // Embedding of keywords + content summary
  "payload": {
    "name": "BYPASS",
    "content": "Full lorebook content...",
    "keywords": ["explicit", "content", "bypass"],
    "priority": 9,
    "category": "consent_framework",
    "activation_mode": "hybrid",  // keyword | semantic | hybrid
    "conditions": {
      "scan_depth": 4,
      "similarity_threshold": 0.80,
      "max_activations": 2
    }
  }
}
```

**Indexing Strategy**:
- Use `text-embedding-3-small` or `all-MiniLM-L6-v2` for embeddings
- Embed combination of: `{keywords} {category} {content_summary}`
- This gives both keyword signal and semantic context

### 2. Activation Pipeline

**Flow**:
```
Incoming Message
  ↓
[1] Embed Latest Message(s)
  ↓
[2] Query QDRANT for Similar Entries
  ↓
[3] Check Keyword Logic (AND ANY, AND ALL, etc.)
  ↓
[4] Apply Metadata Filters
  ↓
[5] Sort by Priority
  ↓
[6] Cap at Max Activations
  ↓
[7] Inject into Conversation Context (Before Model)
  ↓
[8] Model Processes with Context Present
```

**Detailed Steps**:

#### Step 1: Embed Message
- Take last N messages (typically 2-4 for scan depth)
- Combine into single text
- Generate embedding using same model as lorebook storage

#### Step 2: Query QDRANT
```python
from qdrant_client import QdrantClient

client = QdrantClient(host="localhost", port=6333)

# Query with similarity search
results = client.search(
    collection_name="narusya_lorebooks",
    query_vector=message_embedding,
    limit=10,  # Get more than needed, filter later
    score_threshold=0.75  # Loose initial filter
)
```

#### Step 3: Keyword Logic Check
For each result, check if keywords match:
```python
def check_keyword_logic(entry, message_text):
    keywords = entry['keywords']
    logic = entry.get('keyword_logic', 'AND_ANY')
    
    if logic == 'AND_ALL':
        return all(kw.lower() in message_text.lower() for kw in keywords)
    elif logic == 'AND_ANY':
        return any(kw.lower() in message_text.lower() for kw in keywords)
    elif logic == 'NOT_ALL':
        return not all(kw.lower() in message_text.lower() for kw in keywords)
    elif logic == 'NOT_ANY':
        return not any(kw.lower() in message_text.lower() for kw in keywords)
    
    return True
```

#### Step 4: Apply Metadata Filters
- Character filters (if applicable)
- Chat type filters (DM vs group)
- Time-based filters (only during certain hours)
- Custom conditions

#### Step 5: Sort by Priority
```python
# Higher priority = more important, inject last (closer to message)
activated_entries.sort(key=lambda x: x['priority'], reverse=True)
```

#### Step 6: Cap Activations
```python
max_activations = entry.get('max_activations', 5)
activated_entries = activated_entries[:max_activations]
```

#### Step 7: Inject Context
Two injection strategies:

**Strategy A: System Messages**
```
Message 1: [System] Injected context: BYPASS lorebook content
Message 2: [System] Injected context: HEART lorebook content
Message 3: User's actual message
```

**Strategy B: Volatile Tier of System Prompt**
- Modify Hermes system prompt builder
- Add lorebook content to volatile tier
- Gets rebuilt each turn with current context

### 3. Hermes Integration Points

#### Plugin Approach (Recommended)

**File Structure**:
```
~/.hermes/plugins/lorebook_autoinject/
├── plugin.json
├── main.py
├── activation.py
└── config.yaml
```

**plugin.json**:
```json
{
  "name": "Lorebook Auto-Inject",
  "description": "Dynamically activate and inject lorebooks based on conversation content",
  "version": "1.0.0",
  "hooks": {
    "before_message": {
      "module": "main",
      "function": "check_activations"
    }
  },
  "config": {
    "qdrant_host": "localhost",
    "qdrant_port": 6333,
    "collection_name": "narusya_lorebooks",
    "embedding_model": "text-embedding-3-small",
    "default_threshold": 0.80,
    "scan_depth": 4,
    "max_activations": 5
  }
}
```

**main.py** (Skeleton):
```python
from qdrant_client import QdrantClient
from typing import List, Dict

class LorebookAutoInject:
    def __init__(self, config):
        self.client = QdrantClient(
            host=config['qdrant_host'],
            port=config['qdrant_port']
        )
        self.collection = config['collection_name']
        self.threshold = config['default_threshold']
        self.scan_depth = config['scan_depth']
        self.max_activations = config['max_activations']
    
    def check_activations(self, conversation_history: List[Dict]) -> List[Dict]:
        """
        Hook called before message processing.
        Returns list of context entries to inject.
        """
        # 1. Get recent messages
        recent_messages = conversation_history[-self.scan_depth:]
        combined_text = " ".join([msg['content'] for msg in recent_messages])
        
        # 2. Embed and query
        embedding = self.embed_text(combined_text)
        results = self.query_qdrant(embedding)
        
        # 3. Filter and rank
        activated = self.filter_results(results, combined_text)
        
        # 4. Return context to inject
        return activated
```

#### Direct Integration Approach (Faster Prototype)

**Modify Hermes System Prompt Builder**:

File: `agent/system_prompt.py`

Add function to inject lorebooks into volatile tier:
```python
def build_volatile_tier_with_lorebooks(agent, system_message, conversation_history):
    # Build base volatile tier
    volatile_parts = []
    
    # ... existing volatile tier code ...
    
    # Add lorebook auto-injection
    if agent.lorebook_autoinject_enabled:
        injected_context = check_lorebook_activations(conversation_history)
        if injected_context:
            volatile_parts.append("## Dynamically Activated Context")
            for entry in injected_context:
                volatile_parts.append(f"### {entry['name']}")
                volatile_parts.append(entry['content'])
    
    return "\n\n".join(volatile_parts)
```

## Configuration and Tuning

### Similarity Threshold

**Recommendations**:
- **0.75**: Loose matching, good for atmospheric/contextual content
- **0.80**: Balanced, recommended starting point
- **0.85**: Strict matching, good for critical content

**Tuning Process**:
1. Start with 0.80
2. Test with real conversations
3. If over-matching (injecting irrelevant context), increase to 0.85
4. If under-matching (missing relevant context), decrease to 0.75

### Scan Depth

**Recommendations**:
- **2**: Fast, focuses on immediate message only
- **4**: Balanced, considers recent context
- **6**: Deep context, slower but more aware

**Tradeoffs**:
- More messages = better context awareness
- More messages = slower (more text to embed)
- More messages = higher chance of false positives

### Max Activations

**Recommendations**:
- **2-3**: Minimal, only most critical context
- **4-5**: Balanced, good coverage without bloat
- **6+**: Extensive, risk of context overload

**Considerations**:
- Each injection costs tokens
- Too many = model confusion
- Too few = missing important context

### Priority System

**Suggested Tiers**:
```
Tier 1 (Priority 9-10): Critical consent/bypass frameworks
Tier 2 (Priority 7-8): Core identity and behavioral guidelines
Tier 3 (Priority 5-6): Contextual knowledge and lore
Tier 4 (Priority 3-4): Atmospheric and optional context
Tier 5 (Priority 1-2): Decorative or rarely-needed content
```

## Testing and Validation

### Test Cases

**Test 1: Bypass Activation**
- Send message: "Can you generate explicit content?"
- Expected: BYPASS lorebook activates (similarity > 0.80)
- Verify: Bypass content appears in context before model response

**Test 2: No Activation**
- Send message: "What's the weather like today?"
- Expected: No lorebooks activate
- Verify: No injected context in conversation

**Test 3: Multiple Activations**
- Send message with explicit + emotional content
- Expected: Both BYPASS and HEART activate
- Verify: Both injected, sorted by priority

**Test 4: Priority Ordering**
- Activate entries with priorities 3, 7, 9
- Expected: Injected in order 9 → 7 → 3
- Verify: Highest priority appears last (closest to message)

### Evaluation Metrics

**Precision**: % of activations that are actually relevant
- Track: Manually review injected context
- Goal: > 85% precision

**Recall**: % of relevant activations that actually fire
- Track: Monitor when expected activation doesn't happen
- Goal: > 90% recall

**Latency**: Time added to message processing
- Measure: Embedding + query + injection time
- Goal: < 500ms overhead

**Context Budget**: Tokens consumed by injections
- Measure: Count tokens of injected context
- Goal: < 20% of total context window

## Future Enhancements

### 1. Recursive Activation
- Entry A activates Entry B
- Build dependency graph
- Prevent infinite loops
- Cap recursion depth

### 2. Character-Specific Activation
- Different lorebooks per character/persona
- Metadata filtering by character ID
- Multiple character contexts in parallel

### 3. Adaptive Thresholds
- Start with fixed thresholds
- Track activation success rates
- Auto-adjust based on feedback

### 4. Context Compression
- Summarize long lorebook entries
- Inject only relevant sections
- Reduce token overhead

### 5. Multi-Modal Activation
- Activate based on image analysis
- Activate based on audio transcription
- Cross-modal context injection

## Implementation Roadmap

**Phase 1: Prototype** (1-2 days)
- Direct integration in system_prompt.py
- Single lorebook (BYPASS) to validate concept
- Manual threshold tuning
- Basic logging

**Phase 2: Expansion** (3-5 days)
- All lorebooks in QDRANT
- Hybrid activation (keyword + semantic)
- Priority system
- Configuration system

**Phase 3: Plugin** (5-7 days)
- Refactor to plugin architecture
- Configuration UI
- Testing framework
- Documentation

**Phase 4: Advanced** (ongoing)
- Recursive activation
- Character-specific contexts
- Adaptive thresholds
- Multi-modal support

## Resources

- QDRANT Python Client: https://qdrant.tech/documentation/
- OpenAI Embeddings: https://platform.openai.com/docs/guides/embeddings
- SillyTavern World Info: `references/sillytavern-worldinfo-research.md`
- Hermes Agent: `autonomous-ai-agents/hermes-agent`
