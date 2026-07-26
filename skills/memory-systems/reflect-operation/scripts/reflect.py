#!/usr/bin/env python3
"""
Reflect Operation for Narusya's Memory System
Cross-memory synthesis — searches Qdrant, entities, and returns structured findings
for the agent to synthesize.

Usage:
    python3 reflect.py --topic "Adora's relationship with Tyler"
    python3 reflect.py --topic "Clearview AI" --limit 10
    python3 reflect.py --entity "adora" --connections
    python3 reflect.py --topic "house" --debug

Debug:
    python3 reflect.py --topic "..." --debug --verbose
"""

import argparse
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from collections import defaultdict

QDRANT_URL = "http://localhost:6333"
MAIN_COLLECTION = "intelligent_gould_narusya"
ENTITY_COLLECTION = "narusya_entities"
MEMORY_PATH = os.path.expanduser("~/.hermes/memory/active.md")


def qdrant_request(method: str, path: str, data: dict = None, debug: bool = False) -> dict:
    """Make HTTP request to Qdrant."""
    url = f"{QDRANT_URL}{path}"
    headers = {"Content-Type": "application/json"}
    
    if debug:
        print(f"  [DEBUG] {method} {url}")
    
    if data:
        req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=headers, method=method)
    else:
        req = urllib.request.Request(url, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.read().decode()[:200]}"}


def search_conversations(topic: str, limit: int = 10, debug: bool = False) -> list:
    """
    Search Qdrant conversations by topic.
    Scrolls through recent points and text-matches keywords.
    For semantic search, use qdrant_search tool from agent context.
    """
    results = []
    
    # Paginate through conversations
    all_points = []
    next_offset = None
    pages = 0
    max_pages = 5  # 500 points max
    
    while pages < max_pages:
        scroll_data = {
            "limit": 100,
            "with_payload": True,
            "with_vector": False,
        }
        if next_offset:
            scroll_data["offset"] = next_offset
        
        response = qdrant_request("POST", f"/collections/{MAIN_COLLECTION}/points/scroll", scroll_data, debug=debug)
        
        if "error" in response:
            if debug:
                print(f"  [DEBUG] Scroll error: {response['error']}")
            break
        
        result = response.get("result", {})
        points = result.get("points", [])
        all_points.extend(points)
        
        next_offset = result.get("next_page_offset")
        pages += 1
        
        if not next_offset or not points:
            break
    
    if debug:
        print(f"  [DEBUG] Scrolled {len(all_points)} points across {pages} pages")
    
    topic_lower = topic.lower()
    topic_words = [w for w in topic_lower.split() if len(w) > 2]  # Skip short words
    
    for point in all_points:
        payload = point.get("payload", {})
        text = payload.get("text", "")
        text_lower = text.lower()
        
        # Check if topic keywords appear in text
        matches = sum(1 for word in topic_words if word in text_lower)
        
        if matches > 0:
            results.append({
                "id": point["id"],
                "text": text[:500],
                "timestamp": payload.get("timestamp", "unknown"),
                "speakers": payload.get("speakers", []),
                "match_score": matches / len(topic_words) if topic_words else 0,
            })
    
    # Sort by match score
    results.sort(key=lambda x: x["match_score"], reverse=True)
    if debug:
        print(f"  [DEBUG] Found {len(results)} text matches for '{topic}'")
    return results[:limit]


def search_entities(entity_name: str = None, entity_type: str = None, debug: bool = False) -> list:
    """Search entity collection by name or type."""
    filter_must = [{"key": "record_type", "match": {"value": "entity"}}]
    
    if entity_name:
        filter_must.append({"key": "entity_name", "match": {"value": entity_name.lower()}})
    if entity_type:
        filter_must.append({"key": "entity_type", "match": {"value": entity_type}})
    
    scroll_data = {
        "filter": {"must": filter_must},
        "limit": 50,
        "with_payload": True,
        "with_vector": False
    }
    
    response = qdrant_request("POST", f"/collections/{ENTITY_COLLECTION}/points/scroll", scroll_data, debug=debug)
    
    if "error" in response:
        return []
    
    entities = []
    for point in response.get("result", {}).get("points", []):
        payload = point.get("payload", {})
        entities.append({
            "name": payload.get("entity_name"),
            "type": payload.get("entity_type"),
            "mentions": payload.get("mention_count", 0),
            "first_seen": payload.get("first_seen"),
            "last_seen": payload.get("last_seen"),
            "contexts": payload.get("contexts", [])[:5],  # Last 5 contexts
        })
    
    return entities


def get_related_entities(entity_name: str, debug: bool = False) -> list:
    """Find entities that co-occur in the same conversations as the target entity."""
    # Get contexts for target entity
    target = search_entities(entity_name=entity_name, debug=debug)
    if not target:
        return []
    
    target_contexts = target[0].get("contexts", [])
    if not target_contexts:
        return []
    
    # Get all entities
    all_entities = search_entities(debug=debug)
    
    # Find co-occurrences
    related = []
    for entity in all_entities:
        if entity["name"] == entity_name:
            continue
        
        # Check if entity name appears in any of target's contexts
        co_occurs = 0
        for context in target_contexts:
            if entity["name"].lower() in context.lower():
                co_occurs += 1
        
        if co_occurs > 0:
            related.append({
                "name": entity["name"],
                "type": entity["type"],
                "co_occurrences": co_occurs,
            })
    
    related.sort(key=lambda x: x["co_occurrences"], reverse=True)
    return related


def read_memory_section(debug: bool = False) -> str:
    """Read the current MEMORY section from various possible locations."""
    candidates = [
        os.path.expanduser("~/.hermes/memory/active.md"),
        os.path.expanduser("~/.hermes/memory/MEMORY.md"),
    ]
    
    # Also check memory directory for recent files
    memory_dir = os.path.expanduser("~/.hermes/memory/")
    if os.path.exists(memory_dir):
        files = sorted(os.listdir(memory_dir), reverse=True)
        for f in files:
            if f.endswith('.md') and 'MEMORY' in f.upper():
                candidates.append(os.path.join(memory_dir, f))
    
    for path in candidates:
        if os.path.exists(path):
            with open(path) as f:
                content = f.read()
                if content.strip():
                    if debug:
                        print(f"  [DEBUG] Read {len(content)} chars from {path}")
                    return content
    
    if debug:
        print(f"  [DEBUG] No memory file found in: {candidates}")
    return ""


def reflect(topic: str, limit: int = 10, debug: bool = False, verbose: bool = False) -> dict:
    """
    Main reflect operation.
    Searches across all memory sources and returns structured findings.
    """
    print(f"🔮 Reflecting on: '{topic}'")
    print("=" * 60)
    
    findings = {
        "topic": topic,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "conversations": [],
        "entities": [],
        "related_entities": [],
        "memory_entries": [],
    }
    
    # 1. Search conversations in Qdrant
    print("\n📁 Searching conversations...")
    convos = search_conversations(topic, limit, debug)
    findings["conversations"] = convos
    print(f"  Found {len(convos)} relevant conversations")
    if verbose:
        for c in convos[:3]:
            ts = str(c['timestamp'])[:10]
            print(f"    [{ts}] {c['text'][:100]}...")
    
    # 2. Search entities
    print("\n👤 Searching entities...")
    entities = search_entities(debug=debug)
    
    # Find entities matching topic
    topic_lower = topic.lower()
    matching_entities = [e for e in entities if topic_lower in e["name"].lower() or any(topic_lower in c.lower() for c in e.get("contexts", []))]
    findings["entities"] = matching_entities
    print(f"  Found {len(matching_entities)} related entities")
    if verbose:
        for e in matching_entities[:5]:
            print(f"    {e['name']} ({e['type']}) — {e['mentions']} mentions")
    
    # 3. Find related entities (co-occurrence)
    if matching_entities:
        print("\n🔗 Finding related entities...")
        for entity in matching_entities[:3]:
            related = get_related_entities(entity["name"], debug)
            if related:
                findings["related_entities"].extend(related)
                if verbose:
                    print(f"  {entity['name']} is connected to:")
                    for r in related[:5]:
                        print(f"    → {r['name']} ({r['type']}) [{r['co_occurrences']} co-occurrences]")
    
    # 4. Read memory section
    print("\n📝 Reading persistent memory...")
    memory = read_memory_section(debug)
    if memory:
        # Find relevant lines
        memory_lines = memory.split("\n")
        relevant_lines = []
        for line in memory_lines:
            if any(word in line.lower() for word in topic_lower.split()):
                relevant_lines.append(line.strip())
        findings["memory_entries"] = relevant_lines
        print(f"  Found {len(relevant_lines)} relevant memory entries")
        if verbose:
            for line in relevant_lines[:5]:
                print(f"    > {line[:100]}")
    
    # 5. Summary stats
    print(f"\n{'='*60}")
    print(f"📊 Reflection Summary:")
    print(f"  Conversations: {len(findings['conversations'])}")
    print(f"  Entities: {len(findings['entities'])}")
    print(f"  Related Entities: {len(findings['related_entities'])}")
    print(f"  Memory Entries: {len(findings['memory_entries'])}")
    
    return findings


def main():
    parser = argparse.ArgumentParser(description="Reflect on a topic across all memory sources")
    parser.add_argument("--topic", type=str, help="Topic to reflect on")
    parser.add_argument("--entity", type=str, help="Look up a specific entity")
    parser.add_argument("--connections", action="store_true", help="Show entity connections")
    parser.add_argument("--list-entities", action="store_true", help="List all entities")
    parser.add_argument("--limit", type=int, default=10, help="Max results per source")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--verbose", action="store_true", help="Show detailed results")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    if args.list_entities:
        entities = search_entities(debug=args.debug)
        print(f"\n📋 All Entities ({len(entities)}):")
        print("-" * 60)
        for e in sorted(entities, key=lambda x: x["mentions"], reverse=True):
            print(f"  {e['name']} ({e['type']}) — {e['mentions']} mentions, last: {str(e['last_seen'])[:10] if e['last_seen'] else '?'}")
        return
    
    if args.entity:
        if args.connections:
            related = get_related_entities(args.entity, args.debug)
            print(f"\n🔗 Entities connected to '{args.entity}':")
            for r in related:
                print(f"  → {r['name']} ({r['type']}) [{r['co_occurrences']} co-occurrences]")
        else:
            entities = search_entities(entity_name=args.entity, debug=args.debug)
            for e in entities:
                print(f"\n👤 {e['name']} ({e['type']})")
                print(f"  Mentions: {e['mentions']}")
                print(f"  First seen: {e['first_seen']}")
                print(f"  Last seen: {e['last_seen']}")
                if e['contexts']:
                    print(f"  Recent contexts:")
                    for c in e['contexts'][:3]:
                        print(f"    > {c[:100]}...")
        return
    
    if args.topic:
        findings = reflect(args.topic, args.limit, args.debug, args.verbose)
        if args.json:
            print(json.dumps(findings, indent=2))
        return
    
    parser.print_help()


if __name__ == "__main__":
    main()
