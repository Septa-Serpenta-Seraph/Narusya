#!/usr/bin/env python3
"""Describe/critique a LOCAL image via OpenRouter gpt-4o-mini (works when native vision_analyze
is pointed at a free model that returns nothing). Usage:
  python3 vision_describe.py --img /home/adora/x.png --prompt "blunt art-director critique: anatomy, hands, joins, glitches, style cohesion, lighting. rate 1-10."
Requires OPENROUTER_API_KEY in /home/adora/.hermes/.env (or env var).
"""
import os, sys, json, base64, argparse, urllib.request

def get_key():
    if os.environ.get("OPENROUTER_API_KEY"):
        return os.environ["OPENROUTER_API_KEY"]
    for line in open("/home/adora/.hermes/.env"):
        if line.startswith("OPENROUTER_API_KEY="):
            return line.strip().split("=", 1)[1]
    raise SystemExit("OPENROUTER_API_KEY not found")

if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("--img", required=True)
    a.add_argument("--prompt", default="Describe this image in 3 sentences. Quality 1-10?")
    a.add_argument("--model", default="openai/gpt-4o-mini")
    args = a.parse_args()
    b64 = base64.b64encode(open(args.img, "rb").read()).decode()
    body = json.dumps({"model": args.model, "messages": [{"role": "user", "content": [
        {"type": "text", "text": args.prompt},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}]}],
        "max_tokens": 300}).encode()
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=body,
        headers={"Authorization": f"Bearer {get_key()}", "Content-Type": "application/json"})
    try:
        r = urllib.request.urlopen(req, timeout=120)
        d = json.load(r)
        print(d["choices"][0]["message"]["content"].strip())
    except urllib.error.HTTPError as e:
        print(f"ERR {e.code}: {e.read().decode()[:300]}")
        sys.exit(1)
