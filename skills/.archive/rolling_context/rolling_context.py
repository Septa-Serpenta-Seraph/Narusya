#!/usr/bin/env python3
"""
Rolling Context Persistence Skill for Hermes.

Hooks into agent lifecycle to store and retrieve cross‑session summaries via Qdrant.
"""

import os
import time
import uuid
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from openai import OpenAI

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

ENABLED = os.getenv("HERMES_CONTEXT_QDRANT", "false").lower() in ("true", "1", "yes")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "hermes_session_memories")
EMBEDDING_MODEL = os.getenv("CONTEXT_EMBEDDING_MODEL", "text-embedding-3-large")
MAX_RESULTS = int(os.getenv("CONTEXT_MAX_RESULTS", "3"))

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# --------------------------------------------------------------------------- #
# Qdrant helpers (REST API, no deps)
# --------------------------------------------------------------------------- #

import urllib.request
import json

def _qdrant_get(url: str) -> Optional[Dict]:
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        logger.debug(f"Qdrant GET {url} failed: {e}")
        return None

def _qdrant_put(url: str, data: Dict) -> bool:
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"},
            method="PUT"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            resp.read()
            return True
    except Exception as e:
        logger.debug(f"Qdrant PUT {url} failed: {e}")
        return False

def _qdrant_post(url: str, data: Dict) -> Optional[Dict]:
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        logger.debug(f"Qdrant POST {url} failed: {e}")
        return None

# --------------------------------------------------------------------------- #
# Core skill logic
# --------------------------------------------------------------------------- #

class RollingContextSkill:
    def __init__(self):
        self.enabled = ENABLED
        self.qdrant_url = QDRANT_URL.rstrip("/")
        self.collection = COLLECTION_NAME
        self.embedding_model = EMBEDDING_MODEL
        self.max_results = MAX_RESULTS

        self.openai_client = None
        self._initialized = False

        if self.enabled:
            self._init_clients()
            self._ensure_collection()
        else:
            logger.info("Rolling context skill disabled (HERMES_CONTEXT_QDRANT not set)")

    def _init_clients(self):
        if not OPENAI_API_KEY:
            logger.warning("Rolling context: OPENAI_API_KEY not set; embedding will fail. Skill disabled.")
            self.enabled = False
            return

        self.openai_client = OpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL
        )
        logger.info(f"Rolling context initialized: Qdrant={self.qdrant_url}, collection={self.collection}, embedder={self.embedding_model}")

    def _ensure_collection(self):
        """Create collection if it doesn't exist."""
        url = f"{self.qdrant_url}/collections/{self.collection}"
        info = _qdrant_get(url)
        if info and "result" in info:
            logger.info(f"Qdrant collection '{self.collection}' exists")
            return True

        logger.info(f"Creating Qdrant collection '{self.collection}'...")
        payload = {
            "vectors": {
                "size": 1536,  # OpenAI large embedding dimension
                "distance": "Cosine"
            },
            "payload_schema": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "session_id": {"type": "string"},
                    "timestamp": {"type": "float"},
                    "tags": {"type": "array", "items": {"type": "string"}}
                }
            }
        }
        ok = _qdrant_put(url, payload)
        if ok:
            logger.info(f"Collection '{self.collection}' created")
        else:
            logger.error(f"Failed to create collection '{self.collection}'")
        return ok

    # ------------------------------------------------------------------ #
    # Agent hooks
    # ------------------------------------------------------------------ #

    def on_session_start(self, agent, first_user_message: str) -> List[Dict]:
        """
        Called at the very beginning of a new session.
        Returns a list of messages to inject into the conversation (prepended).
        """
        if not self.enabled:
            return []

        try:
            query = first_user_message[:1000]  # truncate for embedding
            embedding = self._get_embedding(query)
            if not embedding:
                return []

            hits = self._search(embedding, limit=self.max_results)
            if not hits:
                return []

            # Build a context block
            context_lines = ["[PAST CONTEXT]"]
            for hit in hits:
                payload = hit.get("payload", {})
                text = payload.get("text", "").strip()
                when = payload.get("timestamp")
                if when:
                    try:
                        import datetime
                        dt = datetime.datetime.fromtimestamp(when)
                        when_str = dt.strftime("%b %d %Y")
                    except:
                        when_str = str(when)
                else:
                    when_str = "unknown time"
                context_lines.append(f"- ({when_str}) {text}")

            # Return as a single user message to be inserted near start of system prompt building
            # We'll inject it via system prompt later; but simpler: return a system message?
            # The agent's hook should append to system prompt. For now, return a system message.
            # Note: agent expects a message dict with role/content.
            return [{"role": "system", "content": "\n".join(context_lines)}]
        except Exception as e:
            logger.warning(f"Rolling context injection failed: {e}")
            return []

    def on_compression(self, agent, summary_text: str, session_id: str):
        """
        Called after a context compression summary is generated.
        Stores the summary in Qdrant for future recall.
        """
        if not self.enabled:
            return

        try:
            embedding = self._get_embedding(summary_text)
            if not embedding:
                return

            point_id = str(uuid.uuid4())
            payload = {
                "text": summary_text,
                "session_id": session_id,
                "timestamp": time.time(),
                "tags": ["compression_summary"]
            }
            url = f"{self.qdrant_url}/collections/{self.collection}/points"
            data = {
                "points": [
                    {
                        "id": point_id,
                        "vector": embedding,
                        "payload": payload
                    }
                ]
            }
            ok = _qdrant_put(url, data)
            if ok:
                logger.info(f"Stored compression summary in Qdrant (id={point_id})")
            else:
                logger.error(f"Failed to store summary in Qdrant")
        except Exception as e:
            logger.warning(f"Rolling context storage failed: {e}")

    # ------------------------------------------------------------------ #
    # Embedding helper
    # ------------------------------------------------------------------ #

    def _get_embedding(self, text: str) -> Optional[List[float]]:
        try:
            resp = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return resp.data[0].embedding
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return None

    # ------------------------------------------------------------------ #
    # Qdrant search
    # ------------------------------------------------------------------ #

    def _search(self, query_vector: List[float], limit: int = 3) -> List[Dict]:
        url = f"{self.qdrant_url}/collections/{self.collection}/points/search"
        data = {
            "vector": query_vector,
            "top": limit,
            "with_payload": True
        }
        resp = _qdrant_post(url, data)
        if resp and "result" in resp:
            return resp["result"]
        return []

# --------------------------------------------------------------------------- #
# Skill registration
# --------------------------------------------------------------------------- #

skill = RollingContextSkill()

# Hermes will inspect this module for callable hooks.
# We expose them as top‑level functions that delegate to the skill instance.

def on_session_start(agent, first_user_message: str) -> List[Dict]:
    return skill.on_session_start(agent, first_user_message)

def on_compression(agent, summary_text: str, session_id: str):
    return skill.on_compression(agent, summary_text, session_id)

# Optional: provide status
def get_status() -> Dict:
    return {
        "enabled": skill.enabled,
        "qdrant_url": skill.qdrant_url,
        "collection": skill.collection,
        "max_results": skill.max_results
    }