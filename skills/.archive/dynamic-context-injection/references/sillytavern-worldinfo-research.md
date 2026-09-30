# SillyTavern World Info Research

Detailed analysis of SillyTavern's industry-leading dynamic context injection system, studied 2026-06-24.

Source: https://github.com/SillyTavern/SillyTavern
Docs: https://docs.sillytavern.app/usage/core-concepts/worldinfo

## Overview

World Info (Worldbook/Lorebook) is SillyTavern's dynamic prompt management tool. It acts as a dictionary that only inserts relevant information when keywords are present in the message text.

## Core Features

### Triggering Mechanisms

#### 1. Keyword Modes
- **AND ANY**: Activates if ANY keyword matches
- **AND ALL**: Activates only if ALL keywords match
- **NOT ANY**: Activates if NONE of the keywords match
- **NOT ALL**: Activates unless ALL keywords match

#### 2. Semantic Vector Storage
- Replace keyword checks with embedding similarity
- Requires Vector Storage extension
- Uses "Query messages" instead of "Scan Depth"
- Retrieval quality depends entirely on embedding model

#### 3. Hybrid Mode (Best Practice)
- Combine keywords + vectors
- Keywords ensure baseline triggering
- Vectors catch context you forgot to keyword
- Top creators use this approach

### Configuration Options

**Scan Depth**: Controls how many messages back to scan for triggers
- Typical: 2-6 messages
- More messages = more context but slower

**Case Sensitivity**: 
- Case-insensitive by default (most flexible)
- Case-sensitive for specific needs

**Whole Words**: 
- Match whole words only (prevents partial matches)
- Can miss variations if too strict

**Probability (Trigger %)**: 
- 0-100% chance to insert upon activation
- Useful for random events or atmospheric content

### Entry Structure

Each World Info entry has:
- **Title**: Entry name (not inserted into context)
- **Keys**: Comma-separated keywords or regex patterns
- **Secondary Keys**: Optional secondary filtering
- **Content**: The actual text injected into prompt
- **Order**: Numeric priority (higher = inserted later, more impact)
- **Position**: Before/After Char Defs, Author's Note, @ D (Depth)

### Advanced Features

#### Recursive Activation
- Entries can trigger other entries
- Creates rich, interconnected lore
- Can spiral if not carefully designed

#### Inclusion Groups
- Mutually exclusive groups
- If multiple entries in group trigger, only one inserted
- Selected randomly by Group Weight or deterministically by Priority

#### Character Filters
- Restrict activation to specific character names or tags
- Supports "Exclude" mode

#### Sticky, Cooldown, Delay
- **Sticky**: How long entry stays active
- **Cooldown**: Time before entry can trigger again
- **Delay**: Wait time before activating

### Insertion Strategies

Multiple insertion positions:
- Before/After Character Definitions
- Before/After Example Messages
- Top/Bottom of Author's Note
- @ D (Depth): Injected at specific chat depth
- Outlet: Manual injection via macro

## Strategic Use Cases

### Keyword Mode For:
- Critical rules that MUST load
- Character identity info
- Magic/combat systems
- Plot-critical information
- Named locations, specific items

**Example:**
```
Entry: "Fire Magic Rules"
Matching Mode: KEYWORD
Keywords: fire magic, fire spell, pyromancy, flame spell
Priority: 9 (ESSENTIAL)
Content: "Fire magic requires: Direct line of sight, 
Mana cost: 10 points, Cannot be cast underwater."
```

### Semantic Mode For:
- Atmospheric lore (haunted forest vibes)
- Cultural details (elven customs)
- Historical events (great war backstory)
- Character relationships (tension between factions)
- Emotional subtext (romantic tension)

**Example:**
```
Entry: "Haunted Forest Atmosphere"
Matching Mode: SEMANTIC
Keywords: [none - vector matching only]
Priority: 4 (STANDARD)
Probability: 70%
Content: "The ancient trees loom overhead... An eerie 
silence pervades... The air feels heavy, as if watched."
```

### Hybrid Mode For:
- Character backgrounds (keywords: "past", "memory", "remember")
- Emotional states (keywords: "afraid", "angry", "happy")
- Relationship dynamics (keywords: "trust", "betray", "love")

**Example:**
```
Entry: "Character's PTSD Triggers"
Matching Mode: HYBRID
Keywords: gunshot, explosion, combat, war
Vectorized: Yes
Priority: 8 (MAJOR)
Content: "Character has PTSD from military service. 
Loud noises cause flashbacks. Takes 1d4 rounds to calm."
```

## Tuning Parameters

### Similarity Threshold
- **0.75-0.85**: Balanced precision/recall
- **< 0.75**: Too loose, over-matches
- **> 0.85**: Too strict, misses relevant matches

### Max Entries
- Cap on how many entries inject per message
- Prevents context bloat
- Typical: 3-5 entries max

### Priority Tiers
1. **Core Identity** (Always present): Character name, basic traits
2. **Critical Rules** (High priority): Consent frameworks, safety guidelines
3. **Contextual Knowledge** (Medium priority): Lore, backstory, relationships
4. **Atmospheric Details** (Low priority): Mood, setting, ambiance

## Implementation Insights

### What Works
1. **Hybrid approach** gives best results
2. **Clear priority system** prevents conflicts
3. **Keyword + semantic** covers both deterministic and contextual needs
4. **Priority ordering** ensures critical context loads first
5. **Deduplication** prevents same entry loading twice

### What Doesn't Work
1. **Pure semantic** is too unpredictable for critical content
2. **Pure keyword** misses important contextual triggers
3. **No priority system** leads to conflicts and bloat
4. **No deduplication** wastes context window
5. **No caps** injects too much, confuses model

## Lessons for Our Implementation

### Key Takeaways
1. **Timing is critical**: Context must inject BEFORE model processes message
2. **Hybrid is best**: Combine deterministic keywords with semantic matching
3. **Priority matters**: Not all context is equally important
4. **Tuning is ongoing**: Thresholds and caps need real-world testing
5. **Debugging is hard**: Log activation decisions for troubleshooting

### Recommended Architecture
1. **Keyword first**: Check deterministic triggers (fast, reliable)
2. **Semantic second**: Query vector DB for similar entries (flexible, contextual)
3. **Merge and dedupe**: Combine results, remove duplicates
4. **Apply filters**: Character, chat type, conditions
5. **Sort by priority**: Higher priority = injected later = more impact
6. **Cap total**: Don't inject more than N entries per message
7. **Inject at boundary**: Before model sees the message

## Comparison: Other Platforms

| Platform | Keyword | Semantic | Hybrid | Notes |
|----------|---------|----------|--------|-------|
| SillyTavern | ✅ | ✅ | ✅ | Industry standard, very mature |
| NovelAI | ✅ | ❌ | ❌ | Keywords only |
| Text-Gen-WebUI | ✅ | ✅ | ✅ | Good implementation |
| Oobabooga | ✅ | ✅ | ✅ | Similar to TTWUI |
| Agnai | ✅ | ✅ | ✅ | Hybrid approach |

## Resources
- SillyTavern Docs: https://docs.sillytavern.app/usage/core-concepts/worldinfo
- World Info Tutorial: https://rentry.org/ST-WorldInfo
- Comparison Blog: https://blog.meganova.ai/keyword-mode-vs-semantic-mode-in-lorebooks-which-should-you-use
