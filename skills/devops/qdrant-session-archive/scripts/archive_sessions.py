#!/usr/bin/env python3
"""Archive all Hermes session messages from state.db into Qdrant with embeddings and timestamps."""

import sqlite3
import datetime
import json
import sys
import os

os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

DB_PATH = "/home/adora/.hermes/state.db"
COLLECTION_NAME = "session_messages_archive"
BATCH_SIZE = 500

def log(msg):
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def main():
    log("Starting session archive pipeline...")
    
    # Load local embedding model (384d, free, no API cost)
    log("Loading embedding model...")
    model = SentenceTransformer('all-MiniLM-L6-v2', config_kwargs={"local_files_only": True})
    dim = model.get_sentence_embedding_dimension()
    log(f"Model loaded, dim={dim}")
    
    # Connect to Qdrant
    client = QdrantClient(host='localhost', port=6333)
    
    # Create or recreate collection
    if client.collection_exists(COLLECTION_NAME):
        log(f"Replacing existing {COLLECTION_NAME} collection...")
        client.delete_collection(COLLECTION_NAME)
    
    log(f"Creating {COLLECTION_NAME} collection (dim={dim})...")
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=dim, distance=Distance.COSINE)
    )
    
    # Connect to SQLite
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Get all sessions for metadata
    cur.execute("SELECT id, source, model, started_at, title FROM sessions")
    sessions = {}
    for row in cur.fetchall():
        sessions[row[0]] = {
            "source": row[1], "model": row[2],
            "started_at": row[3], "title": row[4]
        }
    
    log(f"Loaded {len(sessions)} sessions")
    
    # Get all messages with content, joined with session metadata
    cur.execute(
        "SELECT m.id, m.session_id, m.role, m.content, m.timestamp, "
        "s.source, s.started_at, s.title, s.model "
        "FROM messages m JOIN sessions s ON m.session_id = s.id "
        "WHERE m.content IS NOT NULL AND m.content != '' "
        "ORDER BY m.timestamp ASC"
    )
    all_messages = cur.fetchall()
    total = len(all_messages)
    log(f"Found {total} messages to archive")
    
    point_id = 0
    total_points = 0
    errors = 0
    
    for i in range(0, total, BATCH_SIZE):
        batch = all_messages[i:i+BATCH_SIZE]
        points = []
        
        for msg in batch:
            msg_id, session_id, role, content, timestamp, source, session_start, session_title, session_model = msg
            
            try:
                dt = datetime.datetime.fromtimestamp(timestamp)
                dt_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                session_dt = datetime.datetime.fromtimestamp(session_start).strftime('%Y-%m-%d')
                
                content_for_text = content[:4096] if len(content) > 4096 else content
                embedding = model.encode(f"{role}: {content_for_text}")
                
                points.append(PointStruct(
                    id=point_id,
                    vector=embedding.tolist(),
                    payload={
                        "db_message_id": msg_id,
                        "session_id": session_id,
                        "session_title": session_title or "",
                        "role": role,
                        "content": content,
                        "timestamp": timestamp,
                        "timestamp_iso": dt_str,
                        "session_date": session_dt,
                        "source": source,
                        "session_model": session_model or "",
                    }
                ))
                point_id += 1
            except Exception as e:
                errors += 1
                if errors < 5:
                    log(f"Error on msg {msg_id}: {e}")
        
        if points:
            try:
                client.upsert(collection_name=COLLECTION_NAME, points=points)
                total_points += len(points)
                progress = (i + len(batch)) / total * 100
                log(f"Batch {i//BATCH_SIZE + 1}: {len(points)} points ({progress:.1f}%) - total: {total_points}")
            except Exception as e:
                log(f"Upsert error: {e}")
    
    conn.close()
    log(f"Archive complete: {total_points} points, {errors} errors")

if __name__ == "__main__":
    main()
