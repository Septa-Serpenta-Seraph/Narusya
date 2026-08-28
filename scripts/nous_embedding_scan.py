import json, urllib.request

t = json.load(open('/home/adora/.hermes/shared/nous_auth.json'))
ua = {"Authorization": f"Bearer {t['access_token']}", "User-Agent": "Nar/1.0"}
req = urllib.request.Request(t['inference_base_url'] + "/models", headers=ua)
data = json.load(urllib.request.urlopen(req, timeout=25)).get("data", [])

print("=== FREE models with embedding capability ===")
for m in data:
    mid = m["id"]
    if ":free" not in mid:
        continue
    arch = m.get("architecture", {}) or {}
    mtype = arch.get("model_type") or ""
    inputs = arch.get("input_modalities") or []
    if "embedding" in mtype.lower() or "embed" in mid.lower():
        print(f"  {mid:36s} type={mtype} inputs={inputs}")

print("\n=== ALL free models ===")
for m in data:
    if ":free" in m["id"]:
        print(f"  {m['id']}")
