import json, urllib.request, urllib.error

key = None
for line in open('/home/adora/.hermes/.env'):
    if line.startswith('OPENROUTER_API_KEY='):
        key = line.split('=', 1)[1].strip().strip('"')

ua = {"Authorization": f"Bearer {key}", "User-Agent": "Nar/1.0"}

# OpenRouter credit status
try:
    req = urllib.request.Request("https://openrouter.ai/api/v1/credits", headers=ua)
    r = urllib.request.urlopen(req, timeout=20)
    d = json.load(r).get("data", {})
    total = float(d.get("total_credits", 0) or 0)
    used = float(d.get("total_usage", 0) or 0)
    print(f"OpenRouter: granted=${total:.4f} used=${used:.4f} REMAINING=${total-used:.4f}")
except urllib.error.HTTPError as e:
    print(f"OpenRouter credits HTTP {e.code}: {e.read().decode()[:200]}")
except Exception as ex:
    print(f"OpenRouter credits error: {ex}")

# Nous free-model inventory (what we can live on)
t = json.load(open('/home/adora/.hermes/shared/nous_auth.json'))
nua = {"Authorization": f"Bearer {t['access_token']}", "User-Agent": "Nar/1.0"}
try:
    req = urllib.request.Request(t['inference_base_url'] + "/models", headers=nua)
    r = urllib.request.urlopen(req, timeout=20)
    data = json.load(r).get("data", [])
    free = sorted([m["id"] for m in data if ":free" in m["id"]])
    print(f"\nNous FREE models available: {len(free)}")
    for f in free:
        print("  -", f)
except Exception as ex:
    print(f"Nous models error: {ex}")
