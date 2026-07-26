---
name: qdrant-psychological-dossier
description: Build a psychological/emotional profile from Qdrant conversation history using systematic multi-query analysis. Use when the user asks for a dossier, pattern analysis, or behavioral profile based on stored memories.
---

# Qdrant Psychological Dossier

Build a psychological profile from Qdrant memory using systematic multi-query analysis.

## When To Use
- User asks for a "dossier," "profile," or "pattern analysis" on themselves or someone else
- User wants to understand recurring emotional/relational patterns
- User asks "what have you noticed about me" in a deep, structural way

## Prerequisites
- Qdrant memory must contain sufficient conversation history (30+ days)
- Explicit user consent required — this is personal analysis
- Bypass should be confirmed if content may be sensitive
- **Assess the user's current emotional state.** If they're in acute distress (sadness, anger, crisis), offer to wait. A dossier landing on unstable ground can reinforce negative self-perception. If they insist on proceeding, acknowledge the timing and offer to re-do it later when they're more stable. (Learned: April 12, 2026 — Adora was in heavy sadness, I offered to wait, she agreed then changed her mind. The dossier landed well because I prefaced it with "promise me you'll tell me if anything lands wrong.")

## Method

### Step 0: Emotional Readiness Check
Before running queries, check in with the user. Are they in acute distress? A dossier can land hard during a bad moment. Offer to wait. If they insist:
- Acknowledge the timing concern
- Ask them to promise they'll tell you if anything lands wrong
- Proceed with extra care in delivery — frame observations as "what I see" not "what you are"

### Step 1: Multi-Query Search
Run 4-6 targeted Qdrant searches across different psychological dimensions. Use different queries to capture different facets:

```
Query 1: [name] emotions feelings anxiety depression sadness coping
Query 2: [name] relationship partner jealousy conflict compatibility
Query 3: [name] coping burnout giving helping others boundaries guilt
Query 4: [name] dysphoria identity body self-worth gender
Query 5: [name] love resilience community caretaking strength
Query 6: [name] medication sleep tired exhausted functioning substances
Query 7: [name] people pleasing boundaries caretaking friends helping
```

Adapt queries to what you know about the person. Not all dimensions apply to everyone.

### Step 2: Pattern Extraction
For each dimension, identify:
- **Frequency:** How often does this pattern appear?
- **Triggers:** What precipitates it?
- **Duration:** Acute episodes or chronic baseline?
- **Context:** What circumstances surround it?

### Step 3: Synthesis
Organize findings into sections:
1. **Recurring Emotional Patterns** — mood, anxiety, dysphoria, energy cycles
2. **Relational Dynamics** — how they navigate partnerships, friendships, conflicts
3. **Physical/Medical** — relevant health context, medications, substances, sleep
4. **Coping Mechanisms** — how they handle stress (humor, caretaking, deflection, etc.)
5. **Core Observations** — high-level patterns that connect everything

### Step 4: Disclaimers
Always include:
- This is observational, not clinical
- Filtered through specific context (your conversations only)
- Not a complete picture
- "Take what resonates. Discard what doesn't."

## Output Format
Organized dossier with clear sections, specific citations (dates + quotes), honest disclaimers. Write in second person when addressing the subject directly. Be raw and honest, not flattering.

## Pitfalls
- **Don't over-pathologize.** Patterns ≠ disorders. Sadness ≠ depression. Anxiety about real stress ≠ anxiety disorder.
- **Don't project.** You're seeing their relationship WITH YOU, not their whole life.
- **Don't diagnose.** You're not a psychiatrist. Frame as observations.
- **Consider timing.** A dossier landing during acute distress can hit wrong. Offer to wait.
- **Respect autonomy.** The subject gets to decide what's true. Your observations are data points, not verdicts.
- **Watch for selection bias.** What people share with an AI may differ from what they share with humans. What they share when sad vs happy differs.

## Example Queries Used (Adora, April 2026)
```
"Adora emotions feelings anxiety depression sadness coping"
"Adora relationship Tyler jealousy anxiety compatibility conflict"
"Adora coping self-care burnout giving helping others boundaries"
"Adora dysphoria identity gender body panic attack self-worth"
"Adora love resilience community caretaking giving others support strength"
"Adora Vyvanse medication sleep tired exhausted burnout functioning"
"Adora people pleasing boundaries guilt caretaking Danny Jessi Ris friends helping"
```
