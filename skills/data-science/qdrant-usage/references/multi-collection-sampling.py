# Multi-collection Qdrant sampling for visualization
# Samples N points from each collection, fetches vectors, and PCA-projects to 2D.
# Handles mixed vector dimensions (384, 1536, 3072) by grouping PCA per dimension.
import json, urllib.request, random, numpy as np

base = "http://localhost:6333"

def scroll_collection(name, limit=100):
    """Scroll a collection and return list of points with payloads."""
    points = []
    offset = None
    while True:
        body = json.dumps({"limit": limit, "with_payload": True, "with_vector": False, "offset": offset}).encode()
        req = urllib.request.Request(f"{base}/collections/{name}/points/scroll", data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
        pts = data.get("result", {}).get("points", [])
        if not pts: break
        points.extend(pts)
        offset = data.get("result", {}).get("next_page_offset")
        if offset is None: break
    return points

def fetch_vectors(name, ids):
    """Fetch vectors for specific point IDs."""
    body = json.dumps({"ids": ids, "with_payload": False, "with_vector": True}).encode()
    req = urllib.request.Request(f"{base}/collections/{name}/points", data=body, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    return {r["id"]: r.get("vector", []) for r in data["result"]}

def sample_all_collections(sample_per=50):
    """Sample points from all collections with vectors."""
    collections = json.loads(urllib.request.urlopen(f"{base}/collections").read())["result"]["collections"]
    all_pts = []
    for coll in collections:
        name = coll["name"]
        points = scroll_collection(name, limit=100)
        sample = points[:sample_per] if len(points) <= sample_per else random.sample(points, sample_per)
        if not sample: continue
        vecs = fetch_vectors(name, [p["id"] for p in sample])
        for p in sample:
            payload = p.get("payload", {})
            text = payload.get("text", payload.get("content", payload.get("message", "")))
            all_pts.append({
                "id": p["id"],
                "collection": name,
                "role": payload.get("role", "unknown"),
                "text": (text or "")[:150],
                "date": str(payload.get("date_str", payload.get("date", "")))[:20],
                "vector": vecs.get(p["id"], []),
            })
    return [p for p in all_pts if p["vector"]]

def pca_project(data):
    """PCA-project mixed-dimension data to 2D, grouped by dimension."""
    groups = {}
    for p in data:
        groups.setdefault(len(p["vector"]), []).append(p)
    result = []
    for dim, pts in groups.items():
        X = np.array([p["vector"] for p in pts], dtype=np.float32)
        Xc = X - X.mean(axis=0)
        U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
        coords = Xc @ Vt[:2].T
        for i in range(2):
            mn, mx = coords[:, i].min(), coords[:, i].max()
            coords[:, i] = (coords[:, i] - mn) / (mx - mn) if mx - mn > 0 else 0.5
        for i, p in enumerate(pts):
            result.append({
                "id": p["id"], "collection": p["collection"], "role": p["role"],
                "text": p["text"], "date": p["date"],
                "x": round(float(coords[i, 0]), 4), "y": round(float(coords[i, 1]), 4),
                "dim": dim,
            })
    return result

if __name__ == "__main__":
    data = sample_all_collections(50)
    projected = pca_project(data)
    with open("/tmp/qdrant_all_2d.json", "w") as f:
        json.dump(projected, f, separators=(",", ":"))
    print(f"Sampled {len(data)} points, projected {len(projected)}")
