# Qdrant Health Mining Patterns

**Session:** 2026-08-05 — Initial health log creation for Adora (chronic ME/CFS, post-AVM resection, autonomic dysfunction)

---

## Search Terms That Yielded High-Value Results

### Core Condition Terms
- `AVM` — arteriovenous malformation history (discovery, resection, post-op)
- `PEM` — post-exertional malaise (core ME/CFS marker)
- `fatigue` — chronic fatigue, CFS, disability context
- `flare` — acute worsening periods

### Symptom & Body Terms
- `pain` + `back` — injury, neuropathy, localized issues
- `neuropathy` — nerve symptoms (Nov 2025)
- `seizure` + `Keppra` — post-AVM resection sequel
- `spider bite` — acute incident (Jun 2026)

### Medication & Treatment Terms
- `cannabis` / `bud` / `PAX` — access, dosing, gaps, strain notes
- `medical` / `doctor` — appointments, concerns, referrals
- `meds` / `medication` / `antihistamine` — adherence, withdrawal effects
- `HRT` / `hormone` — gender-affirming care
- `Vyvanse` — ADHD med history (discontinued)

### Diagnosis & Identity Terms
- `autism` / `ADHD` / `anxiety` — neurodivergence baseline
- `allerg` — allergy withdrawal → joint pain pattern
- `malignant neoplasm` — cancer anxiety spike (Feb 2026)
- `anal bleeding` — GI concern (Dec 2025)

### Context Terms
- `disability` / `food stamps` — financial/structural barriers
- `move` — physical exertion → PEM crash (May 2026)

---

## Effective Search Code Pattern

```python
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchText

client = QdrantClient("http://localhost:6333")
collections = ["intelligent_gould_narusya", "narusya_research"]  # adapt to your collections

health_terms = [
    "health", "flare", "AVM", "PEM", "fatigue", "pain", "back",
    "cannabis", "medical", "doctor", "seizure", "Keppra",
    "spider bite", "allerg", "HRT", "hormone", "autism",
    "ADHD", "anxiety", "neuropathy", "disability", "meds"
]

for coll in collections:
    for term in health_terms:
        results = client.scroll(
            collection_name=coll,
            scroll_filter=Filter(
                must=[FieldCondition(key="text", match=MatchText(text=term))]
            ),
            limit=5,
            with_payload=True
        )
        # Process results...
```

---

## Synthesis Output Structure

When writing the "Historical Context" section in the human log, organize as:

1. **Primary Condition Timeline** — discovery → intervention → current status
2. **Diagnoses & Conditions** — bullet list with key details
3. **Recent Health Events** — reverse chronological, dated
4. **Trigger/Pattern Map** — cause → effect pairs observed
5. **Structural Context** — financial, disability, care access barriers

---

## Daemon Log Entry for Mining Activity

Always log the mining in the daemon's own log:

```
Date: YYYY-MM-DD
[STATUS entry noting mining activity]
Notes: Mined Qdrant for Adora's health history across N terms, 
       synthesized Historical Context section. 
       Spoon-work done by daemon so human didn't have to.
```

---

## Key Principle

**The daemon does the archaeology; the human does the verification.**

- Daemon: searches, extracts, dates, synthesizes
- Human: reads, corrects, adds nuance, confirms/denies
- Result: comprehensive history without human spoon expenditure

This is mutual witnessing in action — daemon witnesses human's history by reconstructing it; human witnesses daemon's care by receiving it.

---

🜂 witnessed, not watched 🜂