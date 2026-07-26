#!/usr/bin/env python3
"""Generate sky-castle tiefling images via OpenAI images API (falls back to FAL).

Reads keys directly from ~/.hermes/.env (the running Hermes session did not
export them, but the terminal can read the file). Saves PNGs locally so they
can be delivered as MEDIA: attachments.
"""
from __future__ import annotations

import os
import re
import base64
import json
import urllib.request
import urllib.error
from pathlib import Path

ENV_PATH = Path.home() / ".hermes" / ".env"
OUT_DIR = Path.home() / ".hermes" / "generated"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_env() -> dict:
    data = {}
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        v = v.strip().strip('"').strip("'")
        data[k] = v
    return data


PROMPT_WIDE = (
    "A majestic floating sky castle of pale luminous stone and glowing crystal "
    "spires drifting among soft clouds at golden-hour dusk, wind sweeping across "
    "an open balcony. On the balcony stand two tiefling women together: one TALL, "
    "PALE-SKINNED tiefling with long elegant curved dark horns, flowing dark hair, "
    "and a long coat; one SHORT, RED-SKINNED tiefling with small swept-back horns, "
    "freckled warm complexion, and a mischievous grin. They stand close, shoulders "
    "nearly touching, gazing out at the endless sky. Fantasy concept art, cinematic "
    "volumetric lighting, intricate architectural detail, ethereal atmosphere, high "
    "fidelity, painterly."
)

PROMPT_PORTRAIT = (
    "Close intimate portrait of two tiefling women, fantasy character art. LEFT: a "
    "TALL, PALE-SKINNED tiefling, elegant long curved dark horns, dark hair, calm "
    "confident expression. RIGHT: a SHORT, RED-SKINNED tiefling, small curved horns, "
    "freckled warm red skin, bright playful smile. They lean toward each other, "
    "foreheads nearly touching, warm affection between them. Softly blurred "
    "sky-castle towers and floating clouds behind them, bokeh. Painterly fantasy "
    "illustration, rich color, tender mood, detailed horns and skin texture."
)


def gen_openai(api_key: str, prompt: str, out_path: Path) -> bool:
    import openai
    client = openai.OpenAI(api_key=api_key)
    try:
        res = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024",
            n=1,
            quality="high",
        )
        # gpt-image-1 returns b64_json by default
        b64 = res.data[0].b64_json
        if b64:
            out_path.write_bytes(base64.b64decode(b64))
            return True
        # fallback: url
        url = getattr(res.data[0], "url", None)
        if url:
            urllib.request.urlretrieve(url, out_path)
            return True
    except Exception as e:
        print(f"  [openai error] {type(e).__name__}: {e}")
    return False


def gen_fal(api_key: str, prompt: str, out_path: Path) -> bool:
    import fal_client  # may not be installed
    try:
        from fal_client import submit, status, result
    except Exception as e:
        print(f"  [fal_client not available] {e}")
        return False
    try:
        handler = submit("fal-ai/flux/dev", arguments={"prompt": prompt})
        last = None
        while True:
            s = status(handler)
            if s.get("status") == "COMPLETED":
                last = result(handler)
                break
        imgs = last.get("images") or last.get("data") or []
        if imgs:
            urllib.request.urlretrieve(imgs[0]["url"], out_path)
            return True
    except Exception as e:
        print(f"  [fal error] {type(e).__name__}: {e}")
    return False


def main() -> None:
    env = load_env()
    openai_key = env.get("OPENAI_API_KEY")
    fal_key = env.get("FAL_KEY")
    print(f"keys found: OPENAI={'yes' if openai_key else 'no'}  FAL={'yes' if fal_key else 'no'}")

    jobs = [
        ("skycastle_wide", PROMPT_WIDE),
        ("skycastle_portrait", PROMPT_PORTRAIT),
    ]
    for name, prompt in jobs:
        out = OUT_DIR / f"{name}.png"
        print(f"\n=== generating {name} ===")
        ok = False
        if openai_key:
            print("trying OpenAI...")
            ok = gen_openai(openai_key, prompt, out)
        if not ok and fal_key:
            print("trying FAL...")
            ok = gen_fal(fal_key, prompt, out)
        if ok:
            print(f"  saved -> {out}  ({out.stat().st_size} bytes)")
        else:
            print("  FAILED: both backends unavailable")
            if out.exists():
                out.unlink()


if __name__ == "__main__":
    main()
