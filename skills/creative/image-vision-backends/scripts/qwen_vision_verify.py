#!/usr/bin/env python3
"""Uncensored vision verification — qwen3-vl-8b-instruct on OpenRouter.

Reads any image (including NSFW/explicit renders that the built-in vision model 451s on)
and returns an honest, detailed description. Use this to self-verify explicit image-gen
iterations instead of handing the file to the user blind.

Usage:
    python3 qwen_vision_verify.py /path/to/image.png [--prompt "optional custom question"]

Requires OPENROUTER_API_KEY in ~/.hermes/.env. Works mid-session, no restart needed.
"""
import json, base64, sys, os, urllib.request, urllib.parse

DEFAULT_PROMPT = (
    "Describe this image honestly and in detail: the art style, the figures, their "
    "expressions, the composition, the mood, and whether the intended scenario actually "
    "reads clearly. Don't mince words."
)


def get_openrouter_key():
    with open(os.path.expanduser("~/.hermes/.env")) as fh:
        for line in fh:
            if line.startswith("OPENROUTER_API_KEY="):
                return line.strip().split("=", 1)[1]
    raise SystemExit("OPENROUTER_API_KEY not found in ~/.hermes/.env")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    img_path = sys.argv[1]
    prompt = DEFAULT_PROMPT
    if "--prompt" in sys.argv:
        i = sys.argv.index("--prompt")
        prompt = sys.argv[i + 1]

    key = get_openrouter_key()
    img_b64 = base64.b64encode(open(img_path, "rb").read()).decode()

    body = json.dumps({
        "model": "qwen/qwen3-vl-8b-instruct",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": "data:image/png;base64," + img_b64}},
            ],
        }],
        "max_tokens": 500,
    }).encode()

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=body,
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            d = json.loads(r.read())
        print(d["choices"][0]["message"]["content"])
    except urllib.error.HTTPError as e:
        print("HTTP %s: %s" % (e.code, e.read().decode()[:500]))
    except Exception as e:
        print("ERR: %r" % (e,))


if __name__ == "__main__":
    main()
