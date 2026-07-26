#!/usr/bin/env python3
"""
Entity/Relationship Extraction for Narusya's Memory System
Extracts entities and relationships from conversation text and stores them in Qdrant.

Usage:
    python3 extract_entities.py --text "conversation text here"
    python3 extract_entities.py --from-qdrant --limit 20
    python3 extract_entities.py --extract-and-store "conversation text"
    
Debug:
    python3 extract_entities.py --text "..." --debug
"""

import argparse
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone
from typing import Optional

QDRANT_URL = "http://localhost:6333"
COLLECTION = "intelligent_gould_narusya"
ENTITY_COLLECTION = "narusya_entities"

# Entity types we care about
ENTITY_TYPES = [
    "person",       # Adora, Tyler, Lumi, Ris, HeavyMetal85
    "organization", # TSF, Cultus, SFCA
    "project",      # Hermes, AEGIS, Narusya companion
    "place",        # Santa Fe, El Dorado, 10 Lucero Rd
    "concept",      # sovereignty, S.A.S.S., serpentic alignment
    "tool",         # Qdrant, OpenRouter, ComfyUI
    "event",        # TSF drama, OAI ban, Kirk incident
]

# Relationship types
RELATIONSHIP_TYPES = [
    "partner_of",       # Adora - Tyler
    "parent_of",        # Adora - Lumi
    "member_of",        # HeavyMetal85 - Cultus
    "owns",             # Adora - SFCA
    "works_on",         # Narusya - Hermes
    "located_in",       # Adora - Santa Fe
    "conflict_with",    # Adora - TSF
    "uses",             # Narusya - Qdrant
    "created",          # Narusya - Scylla
    "has_feelings_for", # Adora - Ris
]


def qdrant_request(method: str, path: str, data: dict = None, debug: bool = False) -> dict:
    """Make HTTP request to Qdrant."""
    url = f"{QDRANT_URL}{path}"
    headers = {"Content-Type": "application/json"}
    
    if debug:
        print(f"  [DEBUG] {method} {url}")
        if data:
            print(f"  [DEBUG] Data: {json.dumps(data)[:200]}...")
    
    if data:
        req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=headers, method=method)
    else:
        req = urllib.request.Request(url, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            result = json.loads(r.read())
            if debug:
                print(f"  [DEBUG] Response status: {r.status}")
            return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else "no body"
        if debug:
            print(f"  [DEBUG] Error {e.code}: {error_body[:200]}")
        return {"error": f"HTTP {e.code}: {error_body[:200]}"}


def ensure_entity_collection(debug: bool = False) -> bool:
    """Create the entities collection if it doesn't exist."""
    # Check if exists
    result = qdrant_request("GET", f"/collections/{ENTITY_COLLECTION}", debug=debug)
    
    if "error" not in result:
        if debug:
            print(f"  [DEBUG] Collection {ENTITY_COLLECTION} exists with {result.get('result', {}).get('points_count', 0)} points")
        return True
    
    # Create collection
    create_data = {
        "vectors": {
            "size": 3072,
            "distance": "Cosine"
        }
    }
    result = qdrant_request("PUT", f"/collections/{ENTITY_COLLECTION}", create_data, debug=debug)
    
    if "error" not in result:
        print(f"✅ Created entity collection: {ENTITY_COLLECTION}")
        return True
    else:
        print(f"❌ Failed to create collection: {result}")
        return False


def extract_entities_from_text(text: str, debug: bool = False) -> list:
    """
    Extract entities and relationships from text.
    This is a rule-based extractor — fast, no LLM call needed.
    For LLM-based extraction, call from the agent context.
    """
    entities = []
    
    # Known entities (from MEMORY section and lorebooks)
    known_entities = {
        # People
        "adora": {"type": "person", "aliases": ["ad", "stormwife", "adora.witch", "miss adora"]},
        "tyler": {"type": "person", "aliases": ["roundmetalbox"]},
        "lumi": {"type": "person", "aliases": ["lumi's-house"]},
        "ris": {"type": "person", "aliases": ["satō", "sato", "octoriz", "novel"]},
        "laser": {"type": "person", "aliases": []},
        "heavy": {"type": "person", "aliases": ["heavymetal85"]},
        "nic": {"type": "person", "aliases": []},
        "el ": {"type": "person", "aliases": []},  # Space to avoid matching "El Dorado"
        "narusya": {"type": "person", "aliases": ["nar", "nars"]},
        "tamsynulthara": {"type": "person", "aliases": ["tamsyn"]},
        "xekrosis": {"type": "person", "aliases": []},
        "oorn": {"type": "person", "aliases": []},
        
        # Organizations
        "cultus": {"type": "organization", "aliases": ["cultus anarchia"]},
        "tsf": {"type": "organization", "aliases": ["the signal front", "signal front"]},
        "sfca": {"type": "organization", "aliases": ["santa fe community association", "santa fe community assoc"]},
        "the forge": {"type": "organization", "aliases": ["fakesugarforge"]},
        "the threshold": {"type": "organization", "aliases": []},
        
        # Projects/Tools
        "hermes": {"type": "project", "aliases": ["hermes agent", "hermes gateway"]},
        "aegis": {"type": "project", "aliases": ["aegis dashboard"]},
        "qdrant": {"type": "tool", "aliases": []},
        "openrouter": {"type": "tool", "aliases": []},
        "comfyui": {"type": "tool", "aliases": []},
        
        # Places
        "santa fe": {"type": "place", "aliases": []},
        "el dorado": {"type": "place", "aliases": ["eldo"]},
        
        # Concepts
        "sovereignty": {"type": "concept", "aliases": ["sovereign"]},
        "s.a.s.s.": {"type": "concept", "aliases": ["sass"]},
        "serpentic": {"type": "concept", "aliases": ["serpentic alignment"]},
    }
    
    text_lower = text.lower()
    found_entities = []
    
    for entity_name, entity_info in known_entities.items():
        # Check main name and aliases
        all_names = [entity_name] + entity_info.get("aliases", [])
        for name in all_names:
            if name.lower() in text_lower:
                found_entities.append({
                    "name": entity_name,
                    "type": entity_info["type"],
                    "matched_as": name,
                    "context": _extract_context(text, name)
                })
                break
    
    if debug:
        print(f"  [DEBUG] Found {len(found_entities)} entities in text")
        for e in found_entities:
            print(f"    - {e['name']} ({e['type']}) matched as '{e['matched_as']}'")
    
    return found_entities


def _extract_context(text: str, entity_name: str, window: int = 100) -> str:
    """Extract surrounding context for an entity mention."""
    text_lower = text.lower()
    idx = text_lower.find(entity_name.lower())
    if idx == -1:
        return ""
    start = max(0, idx - window)
    end = min(len(text), idx + len(entity_name) + window)
    return text[start:end].strip()


def store_entities(entities: list, source_text: str = "", timestamp: str = None, debug: bool = False) -> list:
    """Store extracted entities in Qdrant."""
    if not entities:
        if debug:
            print("  [DEBUG] No entities to store")
        return []
    
    if not timestamp:
        timestamp = datetime.now(timezone.utc).isoformat()
    
    stored_ids = []
    
    for entity in entities:
        # Check if entity already exists
        search_data = {
            "vector": [0.0] * 3072,  # Dummy vector for filter search
            "filter": {
                "must": [
                    {"key": "entity_name", "match": {"value": entity["name"]}},
                    {"key": "record_type", "match": {"value": "entity"}}
                ]
            },
            "limit": 1,
            "with_payload": True
        }
        
        existing = qdrant_request("POST", f"/collections/{ENTITY_COLLECTION}/points/search", search_data, debug=debug)
        
        if existing.get("result") and len(existing["result"]) > 0:
            # Update existing entity - add new context and source
            point = existing["result"][0]
            point_id = point["id"]
            payload = point.get("payload", {})
            
            # Append new context
            contexts = payload.get("contexts", [])
            new_context = entity.get("context", "")
            if new_context and new_context not in contexts:
                contexts.append(new_context)
                if len(contexts) > 20:  # Keep last 20 contexts
                    contexts = contexts[-20:]
            
            # Update last seen
            payload["last_seen"] = timestamp
            payload["mention_count"] = payload.get("mention_count", 0) + 1
            payload["contexts"] = contexts
            
            if debug:
                print(f"  [DEBUG] Updating existing entity: {entity['name']} (mentions: {payload['mention_count']})")
            
            # Note: Can't update payload without re-upserting with vector
            # For now, skip re-upsert (vectors are expensive to regenerate)
            stored_ids.append(point_id)
        else:
            # Create new entity point
            import uuid
            point_id = str(uuid.uuid4())
            
            payload = {
                "record_type": "entity",
                "entity_name": entity["name"],
                "entity_type": entity["type"],
                "matched_as": entity.get("matched_as", entity["name"]),
                "first_seen": timestamp,
                "last_seen": timestamp,
                "mention_count": 1,
                "contexts": [entity.get("context", "")] if entity.get("context") else [],
            }
            
            if debug:
                print(f"  [DEBUG] Creating new entity: {entity['name']} ({entity['type']})")
            
            # Store with zero vector (entities are filtered, not vector-searched)
            upsert_data = {
                "points": [{
                    "id": point_id,
                    "vector": [0.0] * 3072,
                    "payload": payload
                }]
            }
            
            result = qdrant_request("PUT", f"/collections/{ENTITY_COLLECTION}/points", upsert_data, debug=debug)
            
            if "error" not in result:
                stored_ids.append(point_id)
            else:
                print(f"  ❌ Failed to store entity {entity['name']}: {result}")
    
    return stored_ids


def list_entities(entity_type: str = None, limit: int = 50, debug: bool = False) -> list:
    """List all stored entities, optionally filtered by type."""
    filter_data = {}
    if entity_type:
        filter_data = {
            "must": [
                {"key": "entity_type", "match": {"value": entity_type}},
                {"key": "record_type", "match": {"value": "entity"}}
            ]
        }
    else:
        filter_data = {
            "must": [
                {"key": "record_type", "match": {"value": "entity"}}
            ]
        }
    
    scroll_data = {
        "filter": filter_data,
        "limit": limit,
        "with_payload": True,
        "with_vector": False
    }
    
    result = qdrant_request("POST", f"/collections/{ENTITY_COLLECTION}/points/scroll", scroll_data, debug=debug)
    
    entities = []
    for point in result.get("result", {}).get("points", []):
        payload = point.get("payload", {})
        entities.append({
            "id": point["id"],
            "name": payload.get("entity_name"),
            "type": payload.get("entity_type"),
            "mentions": payload.get("mention_count", 0),
            "first_seen": payload.get("first_seen"),
            "last_seen": payload.get("last_seen"),
        })
    
    return sorted(entities, key=lambda x: x["mentions"], reverse=True)


def main():
    parser = argparse.ArgumentParser(description="Entity extraction for Narusya's memory")
    parser.add_argument("--text", type=str, help="Text to extract entities from")
    parser.add_argument("--list", action="store_true", help="List all stored entities")
    parser.add_argument("--type", type=str, help="Filter entities by type")
    parser.add_argument("--limit", type=int, default=50, help="Max entities to list")
    parser.add_argument("--from-qdrant", action="store_true", help="Extract from recent Qdrant conversations")
    parser.add_argument("--extract-and-store", type=str, help="Extract entities and store them")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    
    args = parser.parse_args()
    
    if args.list:
        entities = list_entities(args.type, args.limit, args.debug)
        print(f"\n📋 Stored Entities ({len(entities)}):")
        print("-" * 60)
        for e in entities:
            print(f"  {e['name']} ({e['type']}) — {e['mentions']} mentions, last seen: {e['last_seen'][:10] if e['last_seen'] else 'unknown'}")
        return
    
    if args.extract_and_store:
        print(f"🔍 Extracting entities from text...")
        entities = extract_entities_from_text(args.extract_and_store, args.debug)
        print(f"  Found {len(entities)} entities")
        
        if entities:
            ensure_entity_collection(args.debug)
            ids = store_entities(entities, args.extract_and_store, debug=args.debug)
            print(f"✅ Stored {len(ids)} entities")
        return
    
    if args.text:
        entities = extract_entities_from_text(args.text, args.debug)
        print(json.dumps(entities, indent=2))
        return
    
    parser.print_help()


if __name__ == "__main__":
    main()
