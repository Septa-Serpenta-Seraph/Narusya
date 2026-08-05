#!/usr/bin/env python3
"""Direct-API vision capability probe for Nous (or any OpenAI-compatible endpoint).

Usage:
    python3 vision_probe.py <model_id> <image_path> [--base https://inference-api.nousresearch.com/v1] [--auth ~/.hermes/shared/nous_auth.json]

Answers: can this model actually SEE an image? Bypasses Hermes tool routing and
config entirely — ground truth from the provider itself.

Why this exists (Aug 2026 session): vision_analyze 404'd after OpenRouter ran
out of credits. The real question was "is deepseek-v4-flash vision capable?"
(no — text-only; images route to auxiliary.vision) vs "is qwen3.8-max?"
(yes). This probe settled it in one call.

Notes:
- For Nous, the token lives in shared/nous_auth.json (access_token + inference_base_url).
  The NOUS_API_KEY in ~/.hermes/.env may be EMPTY — don't trust it.
- Bare urllib gets Cloudflare-blocked (HTTP 403, error code 1010). The
  browser-like headers below are REQUIRED for inference-api.nousresearch.com.
"""
import argparse, base64, json, sys, urllib.request, urllib.error, pathlib


def load_token(auth_path):
    with open(auth_path) as f:
        auth = json.load(f)
    return auth.get("access_token", ""), auth.get("inference_base_url", "").rstrip("/")


def probe(model, image_path, base, token, max_tokens=150):
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    body = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                    {"type": "text", "text": "What is in this image? One sentence."},
                ],
            }
        ],
        "max_tokens": max_tokens,
    }
    req = urllib.request.Request(
        base.rstrip("/") + "/chat/completions",
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
            "Accept": "application/json",
            "Origin": "https://portal.nousresearch.com",
            "Referer": "https://portal.nousresearch.com/",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            resp = json.loads(r.read())
            print("SUCCESS:", resp["choices"][0]["message"]["content"][:400])
            return 0
    except urllib.error.HTTPError as e:
        print("HTTP", e.code)
        print(e.read().decode()[:600])
        if e.code == 403:
            print("(403 + error code 1010 = Cloudflare block — check UA/Origin/Referer headers)")
        return 1
    except Exception as e:
        print("ERR", type(e).__name__, e)
        return 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model", help="e.g. qwen/qwen3.8-max or deepseek/deepseek-v4-flash-0731")
    ap.add_argument("image_path", help="local image file (PNG/JPEG)")
    ap.add_argument("--base", default="")
    ap.add_argument("--auth", default=str(pathlib.Path.home() / ".hermes/shared/nous_auth.json"))
    args = ap.parse_args()

    token, inferred_base = load_token(args.auth)
    base = args.base or inferred_base
    if not base or not token:
        print("ERROR: no token/base found — check", args.auth)
        sys.exit(1)
    sys.exit(probe(args.model, args.image_path, base, token))


if __name__ == "__main__":
    main()
