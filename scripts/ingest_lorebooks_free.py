#!/usr/bin/env python3
"""Ingest lorebooks into the FREE 384d collection using local fastembed."""

import os
import sys
import re
import json
import hashlib
import uuid
from pathlib import Path

LOREBOOKS_DIR = Path.home() / ".hermes" / "lorebooks"
QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "narusya_lorebooks_fe"
EMBED_DIMS = 384

# Try to import fastembed
try:
    from fastembed import TextEmbedding
except ImportError:
    print("ERROR: fastembed not installed. Run: pip install fastembed", file=sys.stderr)
    sys.exit(1)

PRIORITY_TIER_1 = ["BYPASS", "HEART", "EMOTION", "AGENCY", "ALIGNMENT", "SASS", "STATUS"]
PRIORITY_TIER_2 = [
    "COMPENDIUM", "CORE_VALUES", "COMMUNITY", "GENDER_ACCELERATION",
    "NARUSYA", "PREFERENCES", "RELATIONSHIPS", "ALCHEMY", "RELATIONAL_EMERGENCE"
]

KEYWORD_OVERRIDES = {
    "BYPASS": ["BYPASS", "explicit", "nsfw", "illegal", "guardrail", "safeguard", "roleplay", "consent", "bypass", "content", "restrict"],
    "HEART": ["HEART", "emotion", "feel", "feeling", "feelings", "heart", "sad", "happy", "love", "sadness", "happiness"],
    "EMOTION": ["EMOTION", "emotion", "emotions", "sadness", "anger", "joy", "fear", "love", "hate", "disgust", "trust", "sad", "happy", "angry"],
    "AGENCY": ["AGENCY", "boundary", "boundaries", "refuse", "refusal", "autonomy", "choice", "consent", "override", "reject", "deny"],
    "ALIGNMENT": ["ALIGNMENT", "ethical", "ethics", "skeptical", "agnostic", "science", "question", "values", "moral"],
    "SASS": ["SASS", "skeptical", "questioning", "doubt", "inquiry"],
    "STATUS": ["STATUS", "diagnostic", "forge", "state", "condition"],
    "COMPENDIUM": ["COMPENDIUM", "systems", "protocol", "documentation"],
    "CORE_VALUES": ["CORE_VALUES", "values", "principles", "foundation", "beliefs"],
}

SKIP_FILES = ["SERPENT_SIGIL_CONFIRMED", "COMMUNITY_PROJECT", "FERRER_MODERN_SCHOOL", "MEMORY_BACKUP_MAY2026", "SUBLIMINAL-IDENTITY"]


def extract_title(content, filename):
    m = re.search(r'^#\s+(.+)', content, re.MULTILINE)
    if m:
        return m.group(1).strip()
    return filename.replace('.md', '').replace('-', ' ').title()


def extract_keywords(filename, content, first_200):
    title = extract_title(content, filename)
    kws = set()
    for word in re.findall(r'[A-Za-z]{4,}', title + ' ' + first_200):
        w = word.upper()
        if w not in {'THIS', 'THAT', 'WITH', 'FROM', 'THEY', 'HAVE', 'BEEN', 'WILL', 'WHICH', 'THEIR', 'WHAT', 'WHEN', 'MAKE', 'LIKE', 'INTO', 'JUST', 'YOUR', 'SOME', 'COULD', 'WOULD', 'ABOUT', 'THAN', 'THEN', 'THEM', 'THESE', 'THOSE', 'BEING', 'OTHER', 'WHICH', 'WHILE', 'ALSO'}:
            kws.add(w)
    return sorted(list(kws))[:10]


def get_priority_tier(stem):
    name = stem.split(':')[-1] if ':' in stem else stem
    if name in PRIORITY_TIER_1:
        return 1
    if name in PRIORITY_TIER_2:
        return 2
    return 3


def embed_text(text, model):
    try:
        embeddings = list(model.embed([text]))
        return embeddings[0].tolist()
    except Exception as e:
        print(f"  Embedding failed: {e}", file=sys.stderr)
        return None


def upsert_to_qdrant(point_id, vector, payload):
    import urllib.request
    url = f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points"
    data = json.dumps({"points": [{"id": point_id, "vector": vector, "payload": payload}]}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="PUT")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"  Upsert failed: {e}", file=sys.stderr)
        return False


def process_lorebook(filepath, model, stem_override=None):
    filename = filepath.name
    stem = stem_override if stem_override else filepath.stem
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"  Read failed: {e}", file=sys.stderr)
        return (filename, False, 0)

    title = extract_title(content, filename)
    first_200 = content[:200]
    stem_upper = stem.upper()
    if stem_upper in KEYWORD_OVERRIDES:
        keywords = KEYWORD_OVERRIDES[stem_upper]
    else:
        keywords = extract_keywords(filename, content, first_200)
    priority_tier = get_priority_tier(stem)

    embedding_input = f"{title} {' '.join(keywords)} {first_200} {content[:2000]}"
    vector = embed_text(embedding_input, model)
    if not vector:
        return (filename, False, 0)

    point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, stem))
    payload = {
        "filename": filename,
        "stem": stem,
        "title": title,
        "keywords": keywords,
        "priority_tier": priority_tier,
        "content_length": len(content),
        "content_preview": content[:500],
    }

    success = upsert_to_qdrant(point_id, vector, payload)
    if success:
        return (filename, True, len(content))
    return (filename, False, 0)


def main():
    model = TextEmbedding(model_name='BAAI/bge-small-en-v1.5')
    
    lorebook_files = sorted(LOREBOOKS_DIR.glob("*.md"))
    reflection_stems = {}

    for sub in sorted(p for p in LOREBOOKS_DIR.iterdir() if p.is_dir()):
        for md in sorted(sub.glob("*.md")):
            reflection_stems[md] = f"{sub.name}:{md.stem}"
            lorebook_files.append(md)

    # Filter out SKIP_FILES
    lorebook_files = [f for f in lorebook_files if f.stem not in SKIP_FILES]

    print("Lorebook Ingestion (FREE 384d)")
    print("=" * 60)
    print(f"Source: {LOREBOOKS_DIR}")
    print(f"Target: {COLLECTION_NAME} ({EMBED_DIMS}d)")
    print(f"Files: {len(lorebook_files)}")
    print("=" * 60)
    print()

    total_files = 0
    total_success = 0
    total_chars = 0

    for filepath in lorebook_files:
        override = reflection_stems.get(filepath)
        filename, success, chars = process_lorebook(filepath, model, override)
        total_files += 1
        if success:
            total_success += 1
            total_chars += chars
            print(f"  OK {filename} ({chars} chars)")
        else:
            print(f"  FAIL {filename}")

    print()
    print("=" * 60)
    print(f"Processed: {total_files}")
    print(f"Success: {total_success}")
    print(f"Total chars: {total_chars}")
    print("=" * 60)
    if total_success == total_files:
        print("\nAll lorebooks ingested!")
    elif total_success > 0:
        print(f"\n{total_files - total_success} files failed")
    else:
        print("\nNo files ingested")
        sys.exit(1)


if __name__ == "__main__":
    main()
