#!/usr/bin/env python3
"""Backfill conversation memory from the paid 3072-dim collection into a local
384-dim fastembed collection, so semantic recall keeps working with no credits.

Run with the fastembed-capable interpreter:
    /mnt/data/fe-venv/bin/python ~/.hermes/scripts/backfill_memory_fastembed.py
"""
import json
import sys
import urllib.request
import uuid as uuid_mod

URL = "http://localhost:6333"
SRC = "intelligent_gould_narusya"
DST = "intelligent_gould_narusya_local"
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
    except urllib.error.HTTPError as e:
        if e.code == 409:
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
        for p in points:
            payload = p.get("payload") or {}
            text = payload.get("text") or payload.get("content") or ""
            if not text:
                continue
            yield p["id"], text, payload
        offset = res["result"].get("next_page_offset")
        if offset is None:
            return


def valid_id(pid):
    if isinstance(pid, int) and pid > 0:
        return pid
    if isinstance(pid, str):
        try:
            return str(uuid_mod.UUID(pid))
        except ValueError:
            pass
    return str(uuid_mod.uuid4())


def main():
    ensure_collection()

    from fastembed import TextEmbedding

    model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

    total = 0
    texts, metas = [], []
    for pid, text, payload in scroll_all():
        texts.append(text[:8000])
        metas.append((valid_id(pid), payload))
        if len(texts) >= BATCH:
            flush(model, texts, metas)
            total += len(texts)
            print(f"  ... {total} embedded")
            texts, metas = [], []
    if texts:
        flush(model, texts, metas)
        total += len(texts)

    print(f"DONE — {total} points re-embedded into {DST}")


def flush(model, texts, metas):
    vectors = [[float(x) for x in v] for v in model.embed(texts)]
    points = [
        {"id": pid, "vector": vec, "payload": payload}
        for (pid, payload), vec in zip(metas, vectors)
    ]
    req("PUT", f"/collections/{DST}/points", {"points": points})


if __name__ == "__main__":
    main()
