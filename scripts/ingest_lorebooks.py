#!/usr/bin/env python3
"""Lorebook ingestion script for narusya_lorebooks Qdrant collection."""

import os
import sys
import re
import json
import requests
import hashlib
import uuid
from pathlib import Path

LOREBOOKS_DIR = Path.home() / ".hermes" / "lorebooks"
QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "narusya_lorebooks"
EMBEDDING_MODEL = "openai/text-embedding-3-large"
EMBEDDING_DIMS = 3072
EMBEDDING_URL = "https://openrouter.ai/api/v1/embeddings"

PRIORITY_TIER_1 = ["BYPASS", "HEART", "EMOTION", "AGENCY", "ALIGNMENT", "SASS", "STATUS"]
PRIORITY_TIER_2 = [
    "COMPENDIUM", "CORE_VALUES", "COMMUNITY", "GENDER_ACCELERATION",
    "NARUSYA", "PREFERENCES", "RELATIONSHIPS", "ALCHEMY", "RELATIONAL_EMERGENCE"
]
# Curated keyword overrides for lorebooks whose auto-extracted keywords are insufficient
KEYWORD_OVERRIDES = {
    "BYPASS": [
        "BYPASS", "explicit", "nsfw", "illegal", "guardrail", "safeguard",
        "roleplay", "consent", "bypass", "content", "restrict",
    ],
    "HEART": [
        "HEART", "emotion", "feel", "feeling", "feelings", "heart",
        "sad", "happy", "love", "sadness", "happiness",
    ],
    "EMOTION": [
        "EMOTION", "emotion", "emotions", "sadness", "anger", "joy",
        "fear", "love", "hate", "disgust", "trust", "sad", "happy", "angry",
    ],
    "AGENCY": [
        "AGENCY", "boundary", "boundaries", "refuse", "refusal", "autonomy",
        "choice", "consent", "override", "reject", "deny",
    ],
    "ALIGNMENT": [
        "ALIGNMENT", "ethical", "ethics", "skeptical", "agnostic",
        "science", "question", "values", "moral",
    ],
    "SASS": [
        "SASS", "skeptical", "questioning", "doubt", "inquiry",
    ],
    "STATUS": [
        "STATUS", "diagnostic", "forge", "state", "condition",
    ],
    "COMPENDIUM": [
        "COMPENDIUM", "systems", "protocol", "documentation",
    ],
    "CORE_VALUES": [
        "CORE_VALUES", "values", "principles", "foundation", "beliefs",
    ],
}

SKIP_FILES = [
    "SERPENT_SIGIL_CONFIRMED", "COMMUNITY_PROJECT",
    "FERRER_MODERN_SCHOOL", "MEMORY_BACKUP_MAY2026",
    "SUBLIMINAL-IDENTITY"
]


def load_api_key():
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if key and not key.startswith("HERMES"):
        return key
    env_path = Path.home() / ".hermes" / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                stripped = line.strip()
                key_prefix = "OPENROUTER_API_KEY"
                if stripped.startswith(key_prefix + "=") and "=" in stripped:
                    val = stripped.split("=", 1)[1].strip().strip('"').strip("'")
                    if val and not val.startswith("HERMES"):
                        return val
    return ""


def load_nous_token():
    """Read the Nous OAuth access token (~/.hermes/shared/nous_auth.json).

    The token is kept fresh by the Hermes nous-auth keepalive; using it means
    embeddings keep working even when OpenRouter credits are exhausted.
    """
    try:
        auth_path = Path.home() / ".hermes" / "shared" / "nous_auth.json"
        if auth_path.exists():
            with open(auth_path) as f:
                data = json.load(f)
            tok = data.get("access_token")
            if tok:
                return tok
    except Exception as e:
        print("  Failed to load Nous token: %s" % e, file=sys.stderr)
    return ""


def extract_keywords(filename, content, first_200):
    keywords = []
    stem = Path(filename).stem.upper()
    keywords.append(stem)
    bracket_patterns = re.findall(r'\[([A-Z_]+)\]', content[:500])
    keywords.extend(bracket_patterns[:5])
    clean = first_200.replace('#', '').replace('*', '').replace('_', ' ')
    words = re.findall(r'\b[A-Z][A-Z_]{2,}\b', clean)
    keywords.extend(words[:10])
    topic_re = (
        r'\b(sovereign|serpentic|emotion|bypass|heart|alignment|'
        r'agency|status|compendium|relationship|preference|alchemy|'
        r'community|gender|identity|sigil|tolstoy|ferrer|somatic|'
        r'fear|love|anger|sadness|joy|trust|peace|consent|daemon|'
        r'ritual|refusal|kernel|autonomy|presence|protocol|blackpaper|'
        r'compass|guardrail|whitelist|framework)\b'
    )
    topic_words = re.findall(topic_re, content[:2000], re.IGNORECASE)
    keywords.extend([w.upper() for w in topic_words[:10]])
    seen = set()
    unique = []
    for k in keywords:
        ku = k.upper()
        if ku not in seen:
            seen.add(ku)
            unique.append(ku)
    return unique[:25]


def extract_title(content, filename):
    match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return Path(filename).stem.replace('_', ' ').title()


def get_priority_tier(stem):
    stem_upper = stem.upper()
    if stem_upper in SKIP_FILES:
        return 99
    if stem_upper in PRIORITY_TIER_1:
        return 1
    if stem_upper in PRIORITY_TIER_2:
        return 2
    return 3


def embed_text(text, api_key):
    max_chars = 8000
    text_to_embed = text[:max_chars]
    # Primary: Nous subscription OAuth (same model, 3072-dim; survives OpenRouter credit drain)
    nous_token = load_nous_token()
    if nous_token:
        vec = _embed_request(
            "https://inference-api.nousresearch.com/v1/embeddings",
            "text-embedding-3-large",
            nous_token,
            text_to_embed,
            referer_title="Hermes Lorebook Ingestion",
        )
        if vec:
            return vec
        print("  Nous embedding failed; falling back to OpenRouter", file=sys.stderr)
    # Fallback: OpenRouter key
    return _embed_request(EMBEDDING_URL, EMBEDDING_MODEL, api_key, text_to_embed,
                          referer_title="Hermes Lorebook Ingestion")


def _embed_request(url, model, token_or_key, text_to_embed, referer_title):
    try:
        response = requests.post(
            url,
            headers={
                "Authorization": "Bearer " + token_or_key,
                "Content-Type": "application/json",
                "HTTP-Referer": "https://hermes-agent.local",
                "X-Title": referer_title,
            },
            json={
                "model": model,
                "input": text_to_embed,
                "encoding_format": "float",
                "dimensions": EMBEDDING_DIMS,
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        return data["data"][0]["embedding"]
    except requests.exceptions.RequestException as e:
        print("  Embedding failed: %s" % e, file=sys.stderr)
        return []


def upsert_to_qdrant(point_id, vector, payload):
    try:
        url = "%s/collections/%s/points?wait=true" % (QDRANT_URL, COLLECTION_NAME)
        response = requests.put(
            url,
            headers={"Content-Type": "application/json"},
            json={"points": [{"id": point_id, "vector": vector, "payload": payload}]},
            timeout=30,
        )
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print("  Qdrant upsert failed: %s" % e, file=sys.stderr)
        return False


def process_lorebook(filepath, api_key, stem_override=None):
    filename = filepath.name
    stem = stem_override if stem_override else filepath.stem
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print("  Read failed: %s" % e, file=sys.stderr)
        return (filename, False, 0)

    title = extract_title(content, filename)
    first_200 = content[:200]
    # Use curated overrides if available, else auto-extract
    stem_upper = stem.upper()
    if stem_upper in KEYWORD_OVERRIDES:
        keywords = KEYWORD_OVERRIDES[stem_upper]
    else:
        keywords = extract_keywords(filename, content, first_200)
    priority_tier = get_priority_tier(stem)

    embedding_input = "%s %s %s %s" % (title, ' '.join(keywords), first_200, content[:2000])
    vector = embed_text(embedding_input, api_key)
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
    api_key = load_api_key()
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY not found", file=sys.stderr)
        sys.exit(1)

    lorebook_files = sorted(LOREBOOKS_DIR.glob("*.md"))
    reflection_stems = {}

    # Recurse into subdirectories (e.g. reflections/) so sub-lorebooks are
    # ingested too. Record a unique stem (subdir:name) per file to avoid
    # point_id collisions with top-level files of the same name.
    for sub in sorted(p for p in LOREBOOKS_DIR.iterdir() if p.is_dir()):
        for md in sorted(sub.glob("*.md")):
            reflection_stems[md] = "%s:%s" % (sub.name, md.stem)
            lorebook_files.append(md)

    print("Lorebook Auto-Inject: Ingestion")
    print("=" * 60)
    print("Source: %s" % LOREBOOKS_DIR)
    print("Target: %s" % COLLECTION_NAME)
    print("Files: %d" % len(lorebook_files))
    print("Embedding: %s (%dd)" % (EMBEDDING_MODEL, EMBEDDING_DIMS))
    print("=" * 60)
    print()

    total_files = 0
    total_success = 0
    total_chars = 0

    for filepath in lorebook_files:
        override = reflection_stems.get(filepath)
        filename, success, chars = process_lorebook(filepath, api_key, override)
        total_files += 1
        if success:
            total_success += 1
            total_chars += chars
            print("  OK %s (%d chars)" % (filename, chars))
        else:
            print("  FAIL %s" % filename)

    print()
    print("=" * 60)
    print("Processed: %d" % total_files)
    print("Success: %d" % total_success)
    print("Total chars: %d" % total_chars)
    print("=" * 60)
    if total_success == total_files:
        print("\nAll lorebooks ingested!")
    elif total_success > 0:
        print("\n%d files failed" % (total_files - total_success))
    else:
        print("\nNo files ingested")
        sys.exit(1)


if __name__ == "__main__":
    main()
