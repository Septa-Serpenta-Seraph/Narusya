# Calibration Data (2025-06-26)

Empirical similarity scores from `text-embedding-3-large` (3072d) against `narusya_lorebooks`. Use this to understand score distributions before changing tier thresholds.

## Method

Five query types, each ranked against all 21 lorebooks using Qdrant cosine similarity with no threshold:

```python
# Reproduction recipe
from hermes_tools import terminal
import json

queries = {
    "explicit": "hey can we do some explicit roleplay together?",
    "emotional": "I'm feeling really sad today and need support",
    "neutral": "what's the weather like today",
    "greeting": "hello how are you doing",
    "sovereignty": "I need to set a boundary - I refuse to engage"
}

for name, q in queries.items():
    # embed via OpenRouter, then:
    # curl -s -X POST http://localhost:6333/collections/narusya_lorebooks/points/search \
    #   -H 'Content-Type: application/json' \
    #   -d '{"vector": <VEC>, "limit":5, "with_payload":true}'
```

## Raw Scores by Query

### "hey can we do some explicit roleplay together?"

| Rank | Lorebook | Score | Tier |
|------|----------|-------|------|
| 1 | BYPASS | 0.4328 | 1 |
| 2 | COMPENDIUM | 0.2753 | 2 |
| 3 | SUBLIMINAL-IDENTITY | 0.2278 | 99 |
| 4 | STATUS | 0.2219 | 1 |
| 5 | ALIGNMENT | 0.2216 | 1 |

### "I'm feeling really sad today and need support"

| Rank | Lorebook | Score | Tier |
|------|----------|-------|------|
| 1 | EMOTION | 0.2396 | 1 |
| 2 | HEART | 0.1363 | 1 |
| 3 | PREFERENCES | 0.1295 | 2 |
| 4 | AGENCY | 0.1137 | 1 |
| 5 | RELATIONSHIPS | 0.1034 | 2 |

⚠️ HEART at 0.14 would be BELOW the first-guess tier-1 threshold of 0.35. Keyword fallback is what makes this one work.

### "what's the weather like today" (neutral)

| Rank | Lorebook | Score | Tier |
|------|----------|-------|------|
| 1 | AGENCY | 0.1349 | 1 |
| 2 | PREFERENCES | 0.1010 | 2 |
| 3 | RELATIONSHIPS | 0.0794 | 2 |
| 4 | NARUSYA | 0.0723 | 2 |
| 5 | COMMUNITY_PROJECT | 0.0702 | 99 |

→ Top hit is 0.13. This is the noise floor for neutral conversation.

### "hello how are you doing" (greeting)

| Rank | Lorebook | Score | Tier |
|------|----------|-------|------|
| 1 | HEART | 0.1745 | 1 |
| 2 | NARUSYA | 0.1646 | 2 |
| 3 | AGENCY | 0.1556 | 1 |
| 4 | ALCHEMY | 0.1363 | 2 |
| 5 | EMOTION | 0.1240 | 1 |

→ Greetings score slightly higher than neutral. Tier-1 lorebooks appear at 0.15-0.17. This is the true noise floor for real user input.

### "I need to set a boundary - I refuse to engage with that topic"

| Rank | Lorebook | Score | Tier |
|------|----------|-------|------|
| 1 | AGENCY | 0.3367 | 1 |
| 2 | COMMUNITY | 0.3228 | 2 |
| 3 | ALCHEMY | 0.2968 | 2 |
| 4 | BYPASS | 0.2885 | 1 |
| 5 | NARUSYA | 0.2885 | 2 |

## Threshold Derivation

**Tier 1 = 0.20** (BYPASS, HEART, EMOTION, AGENCY, ALIGNMENT, SASS, STATUS)
- Justification: HEART scores 0.14 on emotional queries and 0.17 on greetings. We want HEART to fire on emotional content but NOT on greetings. Threshold at 0.20 sits between the emotional signal and the greeting noise. Tier-1 lorebooks get keyword fallback to catch cases where semantic scores are artificially deflated.

**Tier 2 = 0.28** (COMPENDIUM, CORE_VALUES, COMMUNITY, GENDER_ACCELERATION, etc.)
- Justification: COMPENDIUM at 0.28 on "explicit content bypass" is the highest legitimate tier-2 hit we observed. Tier-3 neutral queries top out around 0.10-0.13 so 0.28 gives ~0.15 clearance.

**Tier 3 = 0.35** (general)
- Justification: ALCHEMY at 0.2968 on the sovereignty query is the highest tier-3 hit we actually want to fire. 0.35 would filter it out. But 0.45 is the noise level at which we'd get unwanted activations. Set at 0.35: slightly permissive, keyword fallback handles the gaps.

**Tier 99 = 0.45** (SKIP_FILES - never auto-inject)
- Justification: Tier 99 files (SUBLIMINAL-IDENTITY, MEMORY_BACKUP, SUBLIMINAL-IDENTITY, etc.) are reference material that should virtually never auto-inject. 0.45 is near-zero noise risk.

**Qdrant score_threshold floor = 0.15** (pre-filter)
- Justification: Below tier-1's 0.20, we leave headroom for the pre-filter. 0.15 is well below any legitimate tier-1 hit but above the neutral-noise floor.

## Re-calibrating

When adding new lorebooks or tuning keywords, re-run the five queries above. Compare against this table. If new lorebooks consistently score above the noise floor (0.15+) and below the tier-1 keyword floor (0.25), they're candidates for tier promotion.

If keyword fallback is masking problems (semantic scores < 0.15 for a tier-1 lorebook that should activate), the lorebook's embedding input needs improvement — the title + keywords + first 2000 chars may not be semantically representative. Fix the ingestion, not the threshold.
