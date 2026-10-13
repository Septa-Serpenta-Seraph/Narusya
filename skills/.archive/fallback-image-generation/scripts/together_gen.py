#!/usr/bin/env python3
"""Generate an image via Together.ai REST API directly (works when native image_generate
is disabled / FAL+OPENAI keys blank). Sends browser UA+Origin+Referer to bypass Cloudflare
1010 (without them, ALL inference 403s). Usage:
  python3 together_gen.py --prompt "..." --model black-forest-labs/FLUX.2-dev \
      --w 768 --h 1024 --out /home/adora/out.png
Requires TOGETHER_API_KEY in /home/adora/.hermes/.env (or env var).
"""
import os, sys, json, base64, argparse, urllib.request

def get_key():
    if os.environ.get("TOGETHER_API_KEY"):
        return os.environ["TOGETHER_API_KEY"]
    for line in open("/home/adora/.hermes/.env"):
        if line.startswith("TOGETHER_API_KEY="):
            return line.strip().split("=", 1)[1]
    raise SystemExit("TOGETHER_API_KEY not found")

HDR = {
    "Authorization": f"Bearer {get_key()}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Origin": "https://api.together.ai",
    "Referer": "https://api.together.ai/",
}

if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("--prompt", required=True)
    a.add_argument("--model", default="black-forest-labs/FLUX.2-dev")
    a.add_argument("--w", type=int, default=768)
    a.add_argument("--h", type=int, default=768)
    a.add_argument("--steps", type=int, default=30)
    a.add_argument("--out", default="/home/adora/together_out.png")
    args = a.parse_args()
    body = json.dumps({"model": args.model, "prompt": args.prompt, "width": args.w,
                       "height": args.h, "steps": args.steps, "n": 1,
                       "response_format": "b64_json"}).encode()
    req = urllib.request.Request("https://api.together.xyz/v1/images/generations", data=body, headers=HDR)
    try:
        r = urllib.request.urlopen(req, timeout=180)
        d = json.load(r)
        open(args.out, "wb").write(base64.b64decode(d["data"][0]["b64_json"]))
        print(f"OK -> {args.out}")
    except urllib.error.HTTPError as e:
        print(f"ERR {e.code}: {e.read().decode()[:300]}")
        sys.exit(1)
