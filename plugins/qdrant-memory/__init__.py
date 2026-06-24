"""Qdrant memory provider for Hermes Agent.

Connects to a local Qdrant instance for semantic conversation recall.
Uses OpenRouter for embeddings (text-embedding-3-large, 3072-dim).
Auto-syncs conversation turns to Qdrant in a background thread.
"""

from __future__ import annotations

import json
import logging
import math
import os
import queue
import re
import requests
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent.memory_provider import MemoryProvider
from tools.registry import tool_error

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Timestamp helpers
# ---------------------------------------------------------------------------

def _ts_to_date_str(ts_ms: int) -> str:
    try:
        return datetime.fromtimestamp(ts_ms / 1000).strftime("%Y-%m-%d")
    except (OSError, ValueError):
        return "unknown"

def _ts_age_days(ts_ms: int) -> float:
    try:
        return (datetime.now() - datetime.fromtimestamp(ts_ms / 1000)).total_seconds() / 86400
    except (OSError, ValueError):
        return float("inf")

def _recency_score(ts_ms: int) -> float:
    age_days = max(_ts_age_days(ts_ms), 0)
    return math.exp(-age_days / 30.0)

def _extract_timestamp(payload: dict, text: str) -> int:
    ts = payload.get("timestamp")
    if ts and isinstance(ts, (int, float)) and ts > 0:
        return int(ts)
    match = re.search(r'\[(\d{4}-\d{2}-\d{2})\]', text)
    if match:
        try:
            return int(datetime.strptime(match.group(1), "%Y-%m-%d").timestamp() * 1000)
        except ValueError:
            pass
    return 0

# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------

def _load_plugin_config() -> dict:
    try:
        from hermes_constants import get_hermes_home
        config_path = get_hermes_home() / "config.yaml"
        if not config_path.exists():
            return {}
        import yaml
        with open(config_path) as f:
            all_config = yaml.safe_load(f) or {}
        return all_config.get("plugins", {}).get("qdrant-memory", {}) or {}
    except Exception:
        return {}

def _load_env_key(key: str) -> Optional[str]:
    val = os.environ.get(key)
    if val:
        return val
    try:
        from hermes_constants import get_hermes_home
        env_path = get_hermes_home() / ".env"
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    if line.strip().startswith(f"{key}="):
                        return line.strip().split("=", 1)[1].strip().strip('"').strip("'")
    except Exception:
        pass
    return None

# ---------------------------------------------------------------------------
# Qdrant REST client (requests-only, no qdrant-client dependency)
# ---------------------------------------------------------------------------

class _QdrantRestClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def health(self) -> bool:
        try:
            r = requests.get(f"{self.base_url}/healthz", timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    def collection_exists(self, name: str) -> bool:
        try:
            r = requests.get(f"{self.base_url}/collections/{name}", timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    def get_collection_info(self, name: str) -> dict:
        r = requests.get(f"{self.base_url}/collections/{name}", timeout=5)
        r.raise_for_status()
        return r.json().get("result", {})

    def upsert(self, collection: str, points: list) -> bool:
        try:
            r = requests.put(
                f"{self.base_url}/collections/{collection}/points?wait=true",
                json={"points": points},
                headers={"Content-Type": "application/json"},
                timeout=30,
            )
            return r.status_code in (200, 202)
        except Exception as e:
            logger.debug("Qdrant upsert failed: %s", e)
            return False

    def search(self, collection: str, vector: list, limit: int = 5, score_threshold: float = 0.0) -> list:
        payload = {
            "vector": vector,
            "limit": limit,
            "with_payload": True,
            "params": {"hnsw_ef": 128, "exact": False},
        }
        if score_threshold > 0:
            payload["score_threshold"] = score_threshold
        try:
            r = requests.post(
                f"{self.base_url}/collections/{collection}/points/search",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )
            r.raise_for_status()
            return r.json().get("result", [])
        except Exception as e:
            logger.debug("Qdrant search failed: %s", e)
            return []

    def scroll(self, collection: str, limit: int = 10, offset: Optional[str] = None) -> tuple:
        payload = {"limit": limit, "with_payload": True}
        if offset:
            payload["offset"] = offset
        try:
            r = requests.post(
                f"{self.base_url}/collections/{collection}/points/scroll",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )
            r.raise_for_status()
            data = r.json().get("result", {})
            return data.get("points", []), data.get("next_page_offset")
        except Exception as e:
            logger.debug("Qdrant scroll failed: %s", e)
            return [], None

# ---------------------------------------------------------------------------
# Embedding client
# ---------------------------------------------------------------------------

class _EmbeddingClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or _load_env_key("OPENROUTER_API_KEY")
        self.model = "openai/text-embedding-3-large"
        self.dimensions = 3072
        self.url = "https://openrouter.ai/api/v1/embeddings"

    def embed(self, text: str) -> Optional[list]:
        if not self.api_key:
            logger.debug("No OPENROUTER_API_KEY available for embedding")
            return None
        if not text or not text.strip():
            return None
        try:
            r = requests.post(
                self.url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://hermes-agent.local",
                    "X-Title": "Hermes Qdrant Memory",
                },
                json={"model": self.model, "input": text[:8000], "dimensions": self.dimensions},
                timeout=30,
            )
            r.raise_for_status()
            data = r.json()
            return data["data"][0]["embedding"]
        except Exception as e:
            logger.debug("Embedding failed: %s", e)
            return None

# ---------------------------------------------------------------------------
# MemoryProvider implementation
# ---------------------------------------------------------------------------

class QdrantMemoryProvider(MemoryProvider):
    """Qdrant-backed semantic memory with OpenRouter embeddings."""

    def __init__(self, config: dict | None = None):
        self._config = config or _load_plugin_config()
        self._qdrant_url = self._config.get("qdrant_url", "http://localhost:6333")
        self._collection = self._config.get("collection", "intelligent_gould_narusya")
        self._prefetch_limit = int(self._config.get("prefetch_limit", 5))
        self._max_age_days = int(self._config.get("max_age_days", 90))
        self._recency_weight = float(self._config.get("recency_weight", 0.3))

        self._client: Optional[_QdrantRestClient] = None
        self._embedder: Optional[_EmbeddingClient] = None
        self._session_id: str = ""
        self._available = False

        # Background sync worker
        self._sync_queue: queue.Queue = queue.Queue()
        self._shutdown_event = threading.Event()
        self._sync_thread: Optional[threading.Thread] = None

    @property
    def name(self) -> str:
        return "qdrant"

    def is_available(self) -> bool:
        return self._available

    def initialize(self, session_id: str, **kwargs) -> None:
        self._session_id = session_id
        self._client = _QdrantRestClient(self._qdrant_url)
        self._embedder = _EmbeddingClient()

        if not self._client.health():
            logger.warning("Qdrant not reachable at %s", self._qdrant_url)
            self._available = False
            return

        if not self._client.collection_exists(self._collection):
            logger.warning("Qdrant collection '%s' does not exist", self._collection)
            self._available = False
            return

        # Verify embedding pipeline
        test_vec = self._embedder.embed("test")
        if not test_vec or len(test_vec) != self._embedder.dimensions:
            logger.warning("Embedding pipeline not functional")
            self._available = False
            return

        self._available = True
        self._start_sync_worker()
        logger.info(
            "Qdrant initialized: url=%s, collection=%s, prefetch_limit=%d, max_age_days=%d, recency_weight=%.2f",
            self._qdrant_url, self._collection, self._prefetch_limit, self._max_age_days, self._recency_weight,
        )

    def _start_sync_worker(self) -> None:
        if self._sync_thread and self._sync_thread.is_alive():
            return
        self._shutdown_event.clear()
        self._sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self._sync_thread.start()

    def _sync_loop(self) -> None:
        while not self._shutdown_event.is_set():
            try:
                item = self._sync_queue.get(timeout=1.0)
                self._process_sync_item(item)
            except queue.Empty:
                continue
            except Exception as e:
                logger.debug("Sync loop error: %s", e)

    def _process_sync_item(self, item: dict) -> None:
        if not self._client or not self._embedder:
            return
        text = item.get("text", "")
        ts = item.get("timestamp", int(datetime.now().timestamp() * 1000))
        role = item.get("role", "unknown")
        session = item.get("session_id", "")

        if not text or len(text) < 10:
            return

        vector = self._embedder.embed(text)
        if not vector:
            return

        point_id = str(uuid.uuid4()) if "uuid" in globals() else str(hash(text + str(ts)))
        payload = {
            "text": text,
            "timestamp": ts,
            "role": role,
            "session_id": session,
            "date_str": _ts_to_date_str(ts),
        }

        point = {
            "id": point_id,
            "vector": vector,
            "payload": payload,
        }

        self._client.upsert(self._collection, [point])

    def sync_turn(self, user_content: str, assistant_content: str, *, session_id: str = "", agent_context: str = "primary") -> None:
        # Only sync primary context, not cron/subagent
        if agent_context != "primary":
            return
        if not self._available:
            return

        ts = int(datetime.now().timestamp() * 1000)

        if user_content and len(user_content) >= 10:
            self._sync_queue.put({
                "text": f"User: {user_content}",
                "timestamp": ts,
                "role": "user",
                "session_id": session_id or self._session_id,
            })

        if assistant_content and len(assistant_content) >= 10:
            self._sync_queue.put({
                "text": f"Assistant: {assistant_content}",
                "timestamp": ts,
                "role": "assistant",
                "session_id": session_id or self._session_id,
            })

    def prefetch(self, query: str, *, session_id: str = "") -> str:
        if not self._available or not query or not self._client or not self._embedder:
            return ""

        vector = self._embedder.embed(query)
        if not vector:
            return ""

        raw_results = self._client.search(self._collection, vector, limit=min(self._prefetch_limit * 3, 20))
        if not raw_results:
            return ""

        # Filter by age and score
        filtered = []
        for r in raw_results:
            payload = r.get("payload", {})
            ts = _extract_timestamp(payload, payload.get("text", ""))
            age_days = _ts_age_days(ts)
            if self._max_age_days > 0 and age_days > self._max_age_days:
                continue
            sim = r.get("score", 0)
            recency = _recency_score(ts)
            blended = (1 - self._recency_weight) * sim + self._recency_weight * recency
            filtered.append((blended, ts, payload.get("text", "")))

        if not filtered:
            return ""

        filtered.sort(key=lambda x: x[0], reverse=True)
        top = filtered[:self._prefetch_limit]

        # Build context block
        dates = [_ts_to_date_str(t[1]) for t in top if t[1] > 0]
        date_range = f"{min(dates)} → {max(dates)}" if dates else "unknown"

        lines = []
        for _, ts, text in top:
            date_str = _ts_to_date_str(ts) if ts > 0 else "date unknown"
            preview = text[:300].replace("\n", " ")
            if preview.startswith(f"[{date_str}]"):
                preview_no_date = preview[len(f"[{date_str}]"):].lstrip()
                lines.append(f"- [{date_str}] {preview_no_date}")
            else:
                lines.append(f"- [{date_str}] {preview}")

        # Memory recall context
        mem_block = (
            f"<memory-context>\n"
            f"[System note: recalled from long-term memory — check dates, recent = more relevant]\n"
            f"## Qdrant Memory Recall (spans: {date_range})\n"
            + "\n".join(lines)
            + "\n</memory-context>"
        )

        # Lorebook auto-inject context
        lb_block = self._query_lorebooks(query, vector)

        if lb_block:
            return mem_block + "\n\n" + lb_block
        return mem_block


    def _query_lorebooks(self, query: str, vector: list) -> str:
        """Hybrid lorebook matching: keyword triggers + semantic similarity.

        Keyword matches (query contains a lorebook's trigger word) always win.
        Semantic matches use tiered thresholds as fallback.
        """
        lb_collection = self._config.get("lorebook_collection", "narusya_lorebooks")
        if not self._client.collection_exists(lb_collection):
            return ""

        max_lorebooks = int(self._config.get("lorebook_max_per_turn", 3))

        # Load metadata cache lazily
        if not hasattr(self, '_lb_meta_cache') or self._lb_meta_cache is None:
            self._lb_meta_cache = self._load_lorebook_metadata(lb_collection)

        query_lower = query.lower()

        # Phase 1: Keyword matching
        keyword_hits = []  # (score=1.0, tier, payload)
        already_hit_stems = set()
        for stem, kw_data in self._lb_meta_cache.items():
            keywords = kw_data.get("keywords", [])
            tier = kw_data.get("priority_tier", 3)
            filename = kw_data.get("filename", "")
            if tier >= 99:
                continue  # skip files never auto-inject
            for kw in keywords:
                kw_lower = kw.lower()
                if len(kw_lower) >= 3 and kw_lower in query_lower:
                    keyword_hits.append((1.0, tier, {
                        "stem": stem,
                        "filename": filename,
                        "priority_tier": tier,
                    }))
                    already_hit_stems.add(stem)
                    break  # one hit per lorebook

        # Phase 2: Semantic matching (fill remaining slots)
        semantic_hits = []
        tier_thresholds = {
            1: 0.20,  # Critical lorebooks: low bar to fire
            2: 0.28,  # Important
            3: 0.35,  # General
            99: 0.45,  # Skip - high bar
        }
        try:
            raw = self._client.search(lb_collection, vector, limit=max_lorebooks * 3, score_threshold=0.15)
        except Exception:
            raw = []

        for r in raw:
            payload = r.get("payload", {})
            stem = payload.get("stem", "?")
            tier = payload.get("priority_tier", 3)
            score = r.get("score", 0)
            if stem in already_hit_stems:
                continue  # already matched by keyword
            if tier >= 99:
                continue  # skip files
            threshold = tier_thresholds.get(tier, 0.45)
            if score >= threshold:
                semantic_hits.append((score, tier, payload))

        # Merge: keyword first, then semantic by score
        all_hits = sorted(keyword_hits, key=lambda x: (x[1], -x[0]))  # by tier asc, score desc
        all_hits += sorted(semantic_hits, key=lambda x: -x[0])  # by score desc
        matched = all_hits[:max_lorebooks]

        if not matched:
            return ""

        names = [p.get("stem", "?") for _, _, p in matched]
        kw_count = sum(1 for _, _, p in matched if p.get("stem") in already_hit_stems)
        logger.info("Lorebook auto-inject: %s (keyword=%d, semantic=%d)", names, kw_count, len(matched) - kw_count)

        # Build context block
        lb_parts = ["<lorebook-context>"]
        lb_parts.append("[The following lorebook entries were contextually matched. Integrate their protocols naturally.]")
        for score, tier, payload in matched:
            stem = payload.get("stem", "?")
            lorebook_path = Path.home() / ".hermes" / "lorebooks" / payload.get("filename", "")
            content = ""
            try:
                if lorebook_path.exists():
                    content = lorebook_path.read_text(encoding="utf-8")
            except Exception:
                content = payload.get("content_preview", "")

            match_type = "keyword" if stem in already_hit_stems else f"semantic:{score:.2f}"
            # Cap tier 2/3 lorebooks to avoid bloat; tier 1 gets more room
            max_chars = 4000 if tier == 1 else 2500
            if len(content) > max_chars:
                content = content[:max_chars] + "\n... [truncated]"
            lb_parts.append(f"\n### [{stem}] (match: {match_type})")
            lb_parts.append(content)

        lb_parts.append("\n</lorebook-context>")
        return "\n".join(lb_parts)

    def _load_lorebook_metadata(self, lb_collection: str) -> dict:
        """Load all lorebook metadata from Qdrant for keyword matching.
        
        Returns dict: stem -> {filename, priority_tier, keywords}
        """
        metadata = {}
        try:
            offset = None
            while True:
                points, offset = self._client.scroll(lb_collection, limit=50, offset=offset)
                if not points:
                    break
                for p in points:
                    payload = p.get("payload", {})
                    stem = payload.get("stem", "")
                    if stem:
                        metadata[stem] = {
                            "filename": payload.get("filename", ""),
                            "priority_tier": payload.get("priority_tier", 3),
                            "keywords": payload.get("keywords", []),
                        }
                if not offset:
                    break
        except Exception as e:
            logger.warning("Failed to load lorebook metadata: %s", e)
        return metadata

    def queue_prefetch(self, query: str, *, session_id: str = "") -> None:
        # Prefetch is synchronous in this implementation
        pass


    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "qdrant_recall",
                "description": "Semantic search over Qdrant conversation memory. Returns relevant past messages with timestamps.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "limit": {"type": "integer", "description": "Max results", "default": 5},
                        "collection": {"type": "string", "description": "Collection name (default: main collection)"},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "qdrant_browse",
                "description": "Chronologically browse Qdrant memory entries.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "description": "Max entries", "default": 10},
                        "offset": {"type": "string", "description": "Pagination offset"},
                    },
                },
            },
            {
                "name": "qdrant_collections",
                "description": "List all available Qdrant collections.",
                "parameters": {"type": "object", "properties": {}},
            },
        ]

    def handle_tool_call(self, tool_name: str, args: Dict[str, Any], **kwargs) -> str:
        if not self._available or not self._client or not self._embedder:
            return tool_error("Qdrant memory provider not available")

        try:
            if tool_name == "qdrant_recall":
                return self._handle_qdrant_recall(args)
            elif tool_name == "qdrant_browse":
                return self._handle_qdrant_browse(args)
            elif tool_name == "qdrant_collections":
                return self._handle_qdrant_collections(args)
            return tool_error(f"Unknown tool: {tool_name}")
        except Exception as e:
            return tool_error(str(e))

    def _handle_qdrant_recall(self, args: dict) -> str:
        query = args.get("query", "")
        limit = int(args.get("limit", 5))
        collection = args.get("collection") or self._collection

        vector = self._embedder.embed(query)
        if not vector:
            return json.dumps({"error": "Embedding failed", "results": []})

        raw_results = self._client.search(collection, vector, limit=limit * 3)
        filtered = []
        for r in raw_results:
            payload = r.get("payload", {})
            ts = _extract_timestamp(payload, payload.get("text", ""))
            age_days = _ts_age_days(ts)
            if self._max_age_days > 0 and age_days > self._max_age_days:
                continue
            sim = r.get("score", 0)
            recency = _recency_score(ts)
            blended = (1 - self._recency_weight) * sim + self._recency_weight * recency
            filtered.append((blended, ts, payload.get("text", ""), r.get("score", 0)))

        filtered.sort(key=lambda x: x[0], reverse=True)
        top = filtered[:limit]

        results = []
        for blended, ts, text, raw_score in top:
            date_str = _ts_to_date_str(ts) if ts > 0 else "date unknown"
            preview = text[:400].replace("\n", " ")
            if preview.startswith(f"[{date_str}]"):
                preview = preview[len(f"[{date_str}]"):].lstrip()
            results.append({
                "date": date_str,
                "text": preview,
                "similarity": round(raw_score, 4),
                "blended_score": round(blended, 4),
            })

        return json.dumps({"results": results, "count": len(results)})

    def _handle_qdrant_browse(self, args: dict) -> str:
        limit = int(args.get("limit", 10))
        offset = args.get("offset")
        points, next_offset = self._client.scroll(self._collection, limit=limit, offset=offset)
        results = []
        for p in points:
            payload = p.get("payload", {})
            ts = payload.get("timestamp", 0)
            results.append({
                "id": p.get("id"),
                "date": _ts_to_date_str(ts) if ts > 0 else "unknown",
                "text": payload.get("text", "")[:300],
                "role": payload.get("role", "unknown"),
            })
        return json.dumps({"results": results, "count": len(results), "next_offset": next_offset})

    def _handle_qdrant_collections(self, args: dict) -> str:
        try:
            r = requests.get(f"{self._qdrant_url.rstrip('/')}/collections", timeout=10)
            r.raise_for_status()
            data = r.json().get("result", {})
            collections = data.get("collections", [])
            return json.dumps({"collections": [c.get("name") for c in collections]})
        except Exception as e:
            return json.dumps({"error": str(e), "collections": []})

    def on_session_end(self, messages: List[Dict[str, Any]]) -> None:
        # Flush remaining sync queue
        if not self._available:
            return
        remaining = []
        while True:
            try:
                remaining.append(self._sync_queue.get_nowait())
            except queue.Empty:
                break
        for item in remaining:
            self._process_sync_item(item)

    def shutdown(self) -> None:
        """Clean shutdown — flush queues, close connections."""
        try:
            if self._sync_thread and self._sync_thread.is_alive():
                self._shutdown_event.set()
                self._sync_thread.join(timeout=5.0)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Plugin entry point
# ---------------------------------------------------------------------------

def register(ctx) -> None:
    config = _load_plugin_config()
    provider = QdrantMemoryProvider(config=config)
    ctx.register_memory_provider(provider)
