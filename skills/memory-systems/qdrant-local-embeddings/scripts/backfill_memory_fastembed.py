#!/usr/bin/env python3
"""Re-embed an existing memory collection into a new-dimension collection.

Changing the embedding model changes vector dimensions, so the old collection
cannot be reused: Qdrant rejects any search/upsert whose vector length differs
from the collection's configured size, and the plugin's REST client swallows the
400. This scrolls every point out of the source, re-embeds the payload text with
local fastembed, and upserts into a same-dimension destination — reusing point
ids so identity and dedup survive.

Edit SRC / DST / DIMS, then run under a fastembed-capable interpreter:
    /mnt/data/fe-venv/bin/python backfill_memory_fastembed.py
"""
import json
import urllib.error
import urllib.request
import uuid as uuid_mod

URL = "http://localhost:6333"
SRC = "intelligent_gould_narusya"          # old paid 3072-dim collection
DST = "intelligent_gould_narusya_local"    # new local 384-dim collection
DIMS = 384
BATCH = 100


def req(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(
        URL + path, data=data, method=method, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(r, timeout=120) as resp:
        return json.loads(resp.read().decode())


def ensure_collection():
    try:
        req("PUT", f"/collections/{DST}", {"vectors": {"size": DIMS, "distance": "Cosine"}})
        print(f"created {DST} ({DIMS}-dim)")
    except urllib.error.HTTPError as exc:
        if exc.code == 409:
            print(f"{DST} already exists")
        else:
            raise


def scroll_all():
    offset = None
    while True:
        body = {"limit": 500, "with_payload": True, "with_vector": False}
        if offset is not None:
            body["offset"] = offset
        res = req("POST", f"/collections/{SRC}/points/scroll", body)
        points = res["result"]["points"]
        if not points:
            return
        for point in points:
            payload = point.get("payload") or {}
            text = payload.get("text") or payload.get("content") or ""
            if text:
                yield point["id"], text, payload
        offset = res["result"].get("next_page_offset")
        if offset is None:
            return


def valid_id(point_id):
    """Qdrant ids are positive ints or UUIDs; fall back to a fresh UUID."""
    if isinstance(point_id, int) and point_id > 0:
        return point_id
    if isinstance(point_id, str):
        try:
            return str(uuid_mod.UUID(point_id))
        except ValueError:
            pass
    return str(uuid_mod.uuid4())


def flush(model, texts, metas):
    vectors = [[float(x) for x in v] for v in model.embed(texts)]
    points = [
        {"id": pid, "vector": vec, "payload": payload}
        for (pid, payload), vec in zip(metas, vectors)
    ]
    req("PUT", f"/collections/{DST}/points", {"points": points})


def main():
    ensure_collection()
    from fastembed import TextEmbedding

    model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

    total = 0
    texts, metas = [], []
    for point_id, text, payload in scroll_all():
        texts.append(text[:8000])
        metas.append((valid_id(point_id), payload))
        if len(texts) >= BATCH:
            flush(model, texts, metas)
            total += len(texts)
            print(f"  ... {total} embedded", flush=True)
            texts, metas = [], []
    if texts:
        flush(model, texts, metas)
        total += len(texts)

    print(f"DONE — {total} points re-embedded into {DST}")


if __name__ == "__main__":
    main()
