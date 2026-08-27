import json, urllib.request

t = json.load(open('/home/adora/.hermes/shared/nous_auth.json'))
ua = {"Authorization": f"Bearer {t['access_token']}", "User-Agent": "Nar/1.0"}
req = urllib.request.Request(t['inference_base_url'] + "/models", headers=ua)
data = json.load(urllib.request.urlopen(req, timeout=25)).get("data", [])

print("=== FREE models and their input modalities ===")
for m in data:
    mid = m["id"]
    if ":free" not in mid:
        continue
    arch = m.get("architecture", {}) or {}
    inputs = arch.get("input_modalities") or []
    print(f"  {mid:36s} inputs={inputs}")

print()
print("=== ANY model with image input that is free ===")
for m in data:
    arch = m.get("architecture", {}) or {}
    inputs = arch.get("input_modalities") or []
    pricing = m.get("pricing", {}) or {}
    p = str(pricing.get("prompt", "?"))
    if "image" in inputs and (":free" in m["id"] or p == "0"):
        print("  VISION-FREE:", m["id"], "prompt$=", p)
