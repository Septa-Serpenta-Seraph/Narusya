import json, urllib.request, urllib.error

t = json.load(open('/home/adora/.hermes/shared/nous_auth.json'))
key = t['access_token']
base = t['inference_base_url']

ua = {"Authorization": f"Bearer {key}", "User-Agent": "Nar/1.0",
      "Content-Type": "application/json", "Accept": "application/json"}

def try_model(model, prompt):
    payload = json.dumps({
        "model": model,
        "messages": [{"role":"user","content":prompt}],
        "max_tokens": 60
    }).encode()
    req = urllib.request.Request(base+"/chat/completions", data=payload, method='POST', headers=ua)
    try:
        r = urllib.request.urlopen(req, timeout=45)
        d = json.load(r)
        msg = d['choices'][0]['message']
        c = msg.get('content') or msg.get('reasoning_content') or ""
        # collect a few raw keys to debug None cases
        keys = sorted(list(msg.keys())) if isinstance(msg, dict) else []
        print(f"OK {model}: {(c.strip()[:80]) if c else '(no content; msg keys='+str(keys)+')'}")
        return True
    except urllib.error.HTTPError as e:
        print(f"FAIL {model}: HTTP {e.code} {e.read().decode()[:200]}")
        return False

print("=== Longcat (the one that 400'd before) ===")
try_model("meituan/longcat-2.0:free", "hi, quick sanity check, who are you?")

print("=== Tencent hy3 ===")
try_model("tencent/hy3:free", "hi, reply in one short line, no thinking")

print("=== Poolside laguna-s ===")
try_model("poolside/laguna-s-2.1:free", "hi, reply in one short line")