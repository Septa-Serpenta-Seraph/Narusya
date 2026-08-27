import base64, json, sys, urllib.request, urllib.error

img_path = sys.argv[1] if len(sys.argv) > 1 else "/home/adora/.hermes/cache/images/img_f07afed33604.jpeg"
question = sys.argv[2] if len(sys.argv) > 2 else (
    "Describe everything visible in this image in detail: any text, numbers, UI elements, or artwork."
)

t = json.load(open('/home/adora/.hermes/shared/nous_auth.json'))
key, base = t['access_token'], t['inference_base_url']

raw = open(img_path, 'rb').read()
ext = img_path.rsplit('.', 1)[-1].lower()
mime = "image/png" if ext == "png" else "image/jpeg"
b64 = base64.b64encode(raw).decode()

payload = json.dumps({
    "model": "stepfun/step-3.7-flash:free",
    "messages": [{
        "role": "user",
        "content": [
            {"type": "text", "text": question},
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
        ],
    }],
    "max_tokens": 700,
}).encode()

req = urllib.request.Request(
    base + "/chat/completions", data=payload, method='POST',
    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
             "User-Agent": "Nar/1.0", "Accept": "application/json"},
)
try:
    r = urllib.request.urlopen(req, timeout=90)
    d = json.load(r)
    msg = d['choices'][0]['message']
    out = msg.get('content') or msg.get('reasoning') or msg.get('reasoning_content') or ""
    if not out:
        rd = msg.get('reasoning_details')
        if isinstance(rd, list) and rd:
            parts = []
            for item in rd:
                if isinstance(item, dict):
                    parts.append(str(item.get('text') or item.get('content') or item))
                else:
                    parts.append(str(item))
            out = "\n".join(parts)
    if not out and msg.get('refusal'):
        out = "REFUSAL: " + str(msg['refusal'])
    print(out.strip() if out else f"(empty; raw={json.dumps(msg)[:500]})")
except urllib.error.HTTPError as e:
    print(f"FAIL HTTP {e.code}: {e.read().decode()[:400]}")
